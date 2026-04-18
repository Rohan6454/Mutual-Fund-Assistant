# Chunking & Embedding Architecture (GitHub Actions Scheduler)

This document describes **how text is chunked and embedded** in the Mutual Fund FAQ Assistant, and how that work is **scheduled and executed in GitHub Actions**. It complements the end-to-end view in [`RAG-Architecture.md`](./RAG-Architecture.md) (Section 7) by isolating the **indexing plane** (chunk → vector → Qdrant) and the **CI scheduler** that runs it.

---

## 1. Role in the overall system

| Plane | Responsibility |
|-------|----------------|
| **Ingestion (Phase 1)** | Fetch HTML/PDF from URLs in `data/sources.json` → `data/raw/` |
| **Chunking (this doc)** | Extract text, clean, split into JSON chunks under `data/processed/chunks/` |
| **Embedding (this doc)** | Turn chunk text into vectors and **upsert** into Qdrant |
| **Query (Phase 3+)** | Embed the user query with the **same** model/dimensions as ingestion, search Qdrant |

The scheduler’s job is to run ingestion (optional, if you scrape in CI) and **always** run chunking + embedding after raw data exists so the vector store matches the latest corpus.

---

## 2. Scheduler: GitHub Actions

### 2.1 Why GitHub Actions

- **Cron schedules** without maintaining a VM cron or systemd timer.
- **Secrets** for Gemini and Qdrant credentials, scoped to the repo or environment.
- **Repeatable runs**: same container image / `ubuntu-latest` + pinned Python on every execution.
- **Audit trail**: each run is logged with commit SHA, duration, and failure reason.

### 2.2 Recommended schedule

The product target is **daily 09:15 in the deployment timezone** (see main RAG doc). GitHub `schedule` uses **UTC** only.

Example: **09:15 India Standard Time (IST)** ≈ **03:45 UTC** (same calendar day in standard IST).

```yaml
on:
  schedule:
    - cron: "45 3 * * *"   # 03:45 UTC ≈ 09:15 IST — adjust if you standardize on another zone
  workflow_dispatch: {}     # manual re-index without waiting for cron
```

Document the chosen cron in the workflow file comment so future operators know which local time it represents.

### 2.3 High-level workflow shape

Two common patterns:

**Pattern A — Single workflow (simplest)**  
One job, sequential steps: setup → scrape (optional) → `process_documents.py` → `generate_embeddings.py`.

**Pattern B — Split jobs (clearer failures)**  
1. **Job `scrape`** — produces `data/raw/**` (and updated scrape metadata). Upload **artifacts** (raw files + `sources.json` snapshot).  
2. **Job `chunk-and-embed`** — `needs: scrape`, downloads artifacts, runs chunking + embedding, talks to Qdrant.

Use Pattern B if scrape is slow or flaky and you want to retry only embedding, or to inspect raw artifacts from a failed run.

```
cron / workflow_dispatch
        |
        v
+------------------+
|  setup (Python)  |
+--------+---------+
         |
         v
+------------------+     optional artifact upload
| scrape_sources   |---------------------------+
+--------+---------+                           |
         |                                     v
         v                            +-------------------+
+------------------+                  | chunk-and-embed   |
| process_documents|  <--------------| (download raw)    |
|   (chunking)     |                  +---------+-------+
+--------+---------+                            |
         |                                      |
         v                                      v
+------------------+                  Qdrant Cloud / self-hosted
| generate_embed   |------------------>(upsert by chunk_id)
+------------------+
```

---

## 3. Chunking architecture

### 3.1 Inputs and outputs

| Input | Source |
|-------|--------|
| HTML | `data/raw/html/*.html` (+ sidecars / registry in `data/sources.json`) |
| PDF | `data/raw/pdf/*.pdf` |

| Output | Location |
|--------|----------|
| Chunk records | `data/processed/chunks/*.json` (one file per chunk, or batched JSONL — implementation choice; the main doc assumes one JSON per chunk) |

### 3.2 Processing stages (logical)

1. **Extraction**  
   - HTML: BeautifulSoup — main content, headings, tables; strip nav/footer/scripts.  
   - PDF: PyMuPDF per page; `pdfplumber` for table-heavy pages; tables flattened to readable key-value text.

2. **Cleaning** (shared utilities, same rules at query-time where applicable)  
   - Unicode NFKC, whitespace normalization, boilerplate fingerprinting, ISO dates, PDF header/footer removal.

3. **Structural boundaries**  
   - Split on H2/H3 before token/character splitting.  
   - Do not merge text across **scheme boundaries** in multi-scheme sources.  
   - **Tables**: one chunk per table even if longer than the normal size cap; `doc_type: "table"`.

4. **Character splitting**  
   - `RecursiveCharacterTextSplitter` (`langchain-text-splitters`).  
   - `chunk_size`: **500** characters.  
   - `chunk_overlap`: **75** characters (~15%).  
   - `separators`: `["\n\n", "\n", ". ", " "]`.

5. **Metadata attachment**  
   - Each chunk gets stable `chunk_id` (UUID), `text`, and `metadata`: `source_url`, `source_id`, `scheme_name`, `doc_type`, `section`, `page_number`, `last_updated`, `chunk_index`, `total_chunks`.

### 3.3 Determinism and rebuild strategy

For Phase 1 corpus size (~150–200 chunks), a **full rebuild** on each scheduled run is acceptable:

- Delete or overwrite `data/processed/chunks/` for the current run’s output set **or** write to a run-scoped directory then swap.
- Regenerate all chunk files from the **current** `data/raw/` so embeddings always align with the latest scrape.

If you later add incremental ingestion, introduce a **content hash** per source file in chunk metadata and only re-chunk/re-embed changed sources; that is out of scope for the initial GitHub Actions design but the UUID + upsert model supports it.

---

## 4. Embedding architecture

### 4.1 Model selection and consistency

| Mode | Model | Vector dimension |
|------|--------|------------------|
| Primary | Gemini `text-embedding-004` | **768** |
| Fallback | `sentence-transformers/all-MiniLM-L6-v2` | **384** |

**Rule:** The value of `EMBEDDING_MODEL` (or equivalent in `config/settings.py`) used in CI **must match** the API service that answers user queries. Mixing dimensions or models between ingest and query breaks retrieval.

### 4.2 Abstraction

Use `app/utils/embeddings.py` (or the same interface in scripts):

- `embed_texts(texts: list[str]) -> list[list[float]]` — batch path for ingestion.  
- `embed_query(query: str) -> list[float]` — single-vector path for retrieval.

Scripts call the batch API for all chunk texts read from disk.

### 4.3 Batching and API limits

- Read all chunk JSON files from `data/processed/chunks/`.  
- Embed in batches (e.g. **batch_size = 64**); tune down if Gemini returns rate-limit errors.  
- Implement **retry with exponential backoff** on HTTP 429 / transient errors inside `embed_texts` or the workflow step.  
- Log batch index, cumulative count, and elapsed time for observability.

### 4.4 Qdrant upsert

| Setting | Value |
|---------|--------|
| Collection | `mutual_fund_faq` (configurable via `QDRANT_COLLECTION`) |
| Distance | Cosine |
| Point ID | `chunk_id` (UUID string) |
| Vector | Embedding from chosen model |
| Payload | Full metadata + `text` (for debugging and optional keyword filters) |

**Upsert** (not insert-only) ensures re-runs **replace** points with the same `chunk_id`, keeping the collection aligned with the latest chunk files.

**Payload indexes** (keyword): `scheme_name`, `doc_type`, `section` — as in the main architecture doc.

### 4.5 Connectivity from GitHub-hosted runners

Runners are on the public internet. Qdrant must be reachable accordingly:

| Deployment | How the workflow reaches Qdrant |
|------------|----------------------------------|
| **Qdrant Cloud** | `QDRANT_URL` + API key secrets — recommended for Actions. |
| **Self-hosted Qdrant** | Public HTTPS endpoint with auth, or a secure tunnel/API gateway — **not** `localhost` on a private server without ingress. |

Store:

- `GEMINI_API_KEY` (or Google AI key used by `google-generativeai`)  
- `QDRANT_URL`, `QDRANT_API_KEY` (if using cloud or secured instance)  
- Optional: `QDRANT_HOST` / `QDRANT_PORT` if your client expects them

Use **GitHub Environments** (e.g. `production`) with protection rules if only certain branches should push to production Qdrant.

---

## 5. Workflow implementation checklist

1. **Trigger:** `schedule` + `workflow_dispatch`.  
2. **Permissions:** `contents: read`; no need for `contents: write` unless the workflow commits chunks back to the repo (usually **avoid** committing generated chunks).  
3. **Python:** `actions/setup-python` with version from `.python-version` or `3.11`.  
4. **Dependencies:** `pip install -r requirements.txt` (or cached venv).  
5. **Env:** Export all secrets as environment variables expected by `config/settings.py` / scripts.  
6. **Steps:**  
   - (Optional) `python scripts/scrape_sources.py`  
   - `python scripts/process_documents.py`  
   - `python scripts/generate_embeddings.py`  
7. **Failure handling:** Fail the job if any script exits non-zero; optional Slack/email via third-party action.  
8. **Artifacts:** Optional upload of `data/processed/chunks/` for debugging (mind PII policy — corpus is public URLs only in Phase 1).

---

## 6. Observability and operations

| Signal | Where |
|--------|--------|
| Run success/failure | GitHub Actions run history |
| Duration trend | Same; split jobs to see scrape vs embed time |
| Embedding counts | Script logs: points upserted, collection info |
| Cost | Gemini embedding usage (Google AI Studio / Cloud billing) |

For **manual recovery**: run `workflow_dispatch` after fixing a bad scrape or Qdrant outage; upsert makes the vector store self-healing on the next successful run.

---

## 7. Related documents and scripts

| Resource | Purpose |
|----------|---------|
| [`RAG-Architecture.md`](./RAG-Architecture.md) §7 | Canonical Phase 2 data flow and schemas |
| [`phase-2-document-processing/README.md`](../phase-2-document-processing/README.md) | Phase 2 file list and dependencies |
| `scripts/process_documents.py` | Chunking implementation |
| `scripts/generate_embeddings.py` | Embedding + Qdrant upsert |
| `app/utils/embeddings.py` | Model abstraction |

---

## 8. Summary

- **Chunking** is deterministic off `data/raw/`: extract → clean → section-aware rules → `RecursiveCharacterTextSplitter` (500 / 75) → JSON chunks with rich metadata.  
- **Embedding** uses the shared `embed_texts` path, batched with retries, **768-d Gemini** or **384-d MiniLM**, with **Qdrant upsert** keyed by `chunk_id`.  
- **GitHub Actions** replaces traditional OS schedulers: UTC cron + `workflow_dispatch`, secrets for Gemini and Qdrant Cloud, optional artifact handoff between scrape and index jobs.  
- **Query path** must use the same embedding configuration as this pipeline.
