# RAG Architecture Document — Mutual Fund FAQ Assistant

## 1. Executive Summary

This document describes the complete Retrieval-Augmented Generation (RAG) architecture for the Mutual Fund FAQ Assistant. The system answers **facts-only**, verifiable queries by retrieving information exclusively from official public sources registered in `data/sources.json`: Groww Help (user flows), ICICI Prudential / HDFC / Nippon India scheme and factsheet pages, and AMFI/SEBI investor material. Responses are generated with Google Gemini under strict guardrails.

The assistant does not give investment advice, opinions, or recommendations. Each answer uses **at most three sentences**, includes **exactly one source link**, and (where the pipeline attaches it) a last-updated line derived from ingestion metadata. Advisory questions receive a polite refusal with **one** AMFI or SEBI educational link.

---

## 2. High-Level System Architecture

```
                          MUTUAL FUND FAQ ASSISTANT
 ___________________________________________________________________________
|                                                                           |
|  +------------+    +--------------+    +---------------+    +----------+  |
|  | Streamlit  |--->|   FastAPI    |--->|  RAG Engine   |--->|  Gemini  |  |
|  | Frontend   |<---|   Backend    |<---|  + Retriever  |<---|  LLM     |  |
|  +------------+    +--------------+    +---------------+    +----------+  |
|    Port 8501         Port 8000               |                            |
|                                        +-----+-----+                     |
|                                        |  Qdrant   |                     |
|                                        | VectorDB  |                     |
|                                        |  Port 6333|                     |
|                                        +-----------+                     |
|                                              ^                           |
|                                  +-----------+-----------+               |
|                                  | Data Ingestion        |               |
|                                  | Pipeline              |               |
|                                  | (Chunker -> Embedder  |               |
|                                  |  -> Qdrant)           |               |
|                                  +-----------+-----------+               |
|                                              ^                           |
|                                  +-----------+-----------+               |
|                                  | Scraping Service      |               |
|                                  | (HTTP fetch URLs from |               |
|                                  |  data/sources.json)   |               |
|                                  +-----------+-----------+               |
|                                              ^                           |
|                                  +-----------+-----------+               |
|                                  | Daily Scheduler       |               |
|                                  | 09:15 (local time)    |               |
|                                  +-----------+-----------+               |
|                                              ^                           |
|                                  +-----------+-----------+               |
|                                  | Official Sources      |               |
|                                  | (Groww Help, 3 AMCs,  |               |
|                                  |  AMFI, SEBI — see      |               |
|                                  |  Phase 1 batches)     |               |
|                                  +-----------------------+               |
|__________________________________________________________________________|
```

### Component Summary

| Component | Technology | Role |
|-----------|-----------|------|
| Frontend | Streamlit | Chat UI with multi-thread support |
| Backend API | FastAPI + Uvicorn | REST API, thread management, request orchestration |
| RAG Engine | Custom Python | Orchestrates retrieval, generation, guardrails |
| Vector Database | Qdrant (local/Docker) | Stores document embeddings + metadata |
| LLM | Google Gemini (gemini-2.0-flash) | Response generation from retrieved context |
| Embeddings | Gemini text-embedding-004 / all-MiniLM-L6-v2 | Text-to-vector conversion |
| Data Pipeline | BeautifulSoup, PyMuPDF, pdfplumber | Scheduled scrape, parsing, chunking |
| Scheduler | OS cron, systemd timer, APScheduler, or **GitHub Actions** (`schedule` cron) | Daily 09:15 local (or UTC cron equivalent) — triggers scrape + index |
| Scraping service | `scripts/scrape_sources.py` (planned) | Fetches every URL in `data/sources.json` |

### Scheduled data refresh (daily 09:15)

Phase 1 content is kept current by a **daily scheduler** that runs at **09:15 in the deployment host’s local timezone** (adjust if you standardize on IST/UTC in production).

| Piece | Responsibility |
|-------|------------------|
| **Scheduler** | Fires once per day at 09:15 — implemented as **Windows Task Scheduler**, **Linux cron**, **systemd timer**, an in-process **APScheduler** job, or **GitHub Actions** (workflow with `schedule` + optional `workflow_dispatch`). |
| **Scraping service** | `scripts/scrape_sources.py` loads **`data/sources.json`**, iterates every `sources[]` entry, and downloads HTML (and PDFs discovered from factsheet index pages per scraper logic). Writes under `data/raw/` and updates `last_scraped` / `scrape_status`. |
| **Downstream refresh** | After a successful scrape, the same job or a follow-up step runs `process_documents.py` and `generate_embeddings.py` so Qdrant reflects the latest corpus (see Section 7). For **chunking, embedding, and Qdrant upsert** details in a GitHub Actions context, see [`docs/Chunking-Embedding-GitHub-Actions-Architecture.md`](./Chunking-Embedding-GitHub-Actions-Architecture.md). |

**End-to-end flow (scheduled):**

```
09:15 Scheduler trigger
       |
       v
scrape_sources.py  ---- reads ---->  data/sources.json (all Phase 1 URLs)
       |
       v
data/raw/html/ , data/raw/pdf/  +  updated sources.json
       |
       v
process_documents.py  ->  data/processed/chunks/
       |
       v
generate_embeddings.py  ->  Qdrant upsert
```

**Phase 1 URL batches** (canonical list in `data/sources.json`):

| Batch | Role | Examples |
|-------|------|----------|
| 1 — Groww Help | User flows (statements, capital gains) | `groww.in/help`, mutual-funds help articles |
| 2 — Scheme pages | Core scheme facts (ICICI, HDFC, Nippon) | AMC scheme detail URLs |
| 3 — Factsheets | Listing pages linking to PDF factsheets | AMC `/factsheets` download sections |
| 4 — Regulatory | Refusal copy + education | AMFI investor corner, knowledge center, SEBI MF FAQ HTML |

---

## 3. Tech Stack

| Layer | Technology | Version | License | Cost |
|-------|-----------|---------|---------|------|
| Language | Python | 3.11+ | PSF | Free |
| Backend Framework | FastAPI | >=0.110 | MIT | Free |
| ASGI Server | Uvicorn | >=0.29 | BSD | Free |
| Vector Database | Qdrant | >=1.8 | Apache 2.0 | Free (local) |
| LLM Provider | Google Gemini | gemini-2.0-flash | Proprietary | Free tier |
| Embedding (Primary) | Gemini text-embedding-004 | - | Proprietary | Free tier |
| Embedding (Fallback) | sentence-transformers/all-MiniLM-L6-v2 | >=2.6 | Apache 2.0 | Free (local) |
| Frontend | Streamlit | >=1.32 | Apache 2.0 | Free |
| HTML Parsing | BeautifulSoup4 | >=4.12 | MIT | Free |
| PDF Parsing | PyMuPDF (fitz) | >=1.24 | AGPL | Free |
| PDF Tables | pdfplumber | >=0.10 | MIT | Free |
| Text Splitting | langchain-text-splitters | >=0.0.1 | MIT | Free |
| Rate Limiting | slowapi | >=0.1.9 | MIT | Free |
| Validation | Pydantic v2 | >=2.6 | MIT | Free |

---

## 4. Corpus scope (Phase 1)

### 4.1 Platforms and AMCs

- **Groww** — Help center HTML only (how-to flows for mutual funds on the platform); not the corpus for Groww AMC scheme pages in Phase 1.
- **ICICI Prudential**, **HDFC Mutual Fund**, **Nippon India Mutual Fund** — Scheme detail pages plus factsheet index pages.
- **AMFI** and **SEBI** — Regulatory / educational HTML for compliant refusals and generic mutual fund facts.

### 4.2 Scheme pages in scope (Batch 2)

| AMC | Schemes (scheme page URLs in `sources.json`) |
|-----|-----------------------------------------------|
| ICICI Prudential | Bluechip, Flexicap, Value Discovery |
| HDFC Mutual Fund | Flexi Cap, Large Cap, Mid-Cap Opportunities, Small Cap |
| Nippon India MF | Large Cap, Small Cap, Growth, Tax Saver (ELSS) |

### 4.3 Source registry

All Phase 1 URLs, types, and metadata live in **`data/sources.json`** (`batch`: `groww_help`, `scheme_pages`, `factsheets`, `regulatory`). The scraping service does not hard-code URLs; it follows this file.

---

## 5. Project Directory Structure

```
MutualFund-FAQ-Assistant/
|
|-- Problem-Statement.md
|-- README.md
|-- requirements.txt
|-- .env.example
|
|-- docs/
|   +-- RAG-Architecture.md              # This document
|
|-- config/
|   |-- settings.py                       # Central configuration
|   +-- prompts.py                        # Prompt templates, refusal messages
|
|-- data/
|   |-- sources.json                      # Master URL registry
|   |-- raw/
|   |   |-- html/                         # Scraped HTML files
|   |   +-- pdf/                          # Downloaded PDF files
|   +-- processed/
|       |-- chunks/                       # Processed text chunks (JSON)
|       +-- metadata/                     # Chunk metadata files
|
|-- scripts/
|   |-- scrape_sources.py                 # Scraping service: URLs from data/sources.json
|   |-- daily_ingest.py                   # Optional: scrape + process + embed (for scheduler)
|   |-- process_documents.py              # Text extraction + cleaning
|   +-- generate_embeddings.py            # Embedding generation + Qdrant ingestion
|
|-- app/
|   |-- __init__.py
|   |-- main.py                           # FastAPI application entry point
|   |-- models/
|   |   |-- __init__.py
|   |   |-- schemas.py                    # Pydantic request/response models
|   |   +-- enums.py                      # Intent types, document types
|   |-- routers/
|   |   |-- __init__.py
|   |   |-- chat.py                       # POST /api/chat
|   |   |-- threads.py                    # /api/threads CRUD
|   |   +-- health.py                     # GET /api/health
|   |-- services/
|   |   |-- __init__.py
|   |   |-- rag_engine.py                 # Core RAG orchestration
|   |   |-- retriever.py                  # Qdrant vector search + re-ranking
|   |   |-- generator.py                  # Gemini LLM call + response formatting
|   |   |-- guardrails.py                 # PII detection, advisory detection
|   |   +-- thread_manager.py             # In-memory chat thread state
|   +-- utils/
|       |-- __init__.py
|       |-- embeddings.py                 # Embedding model wrapper
|       +-- text_processing.py            # Query preprocessing utilities
|
|-- frontend/
|   +-- streamlit_app.py                  # Streamlit chat UI
|
|-- tests/
|   |-- test_guardrails.py
|   |-- test_retriever.py
|   +-- test_rag_engine.py
|
|-- phase-1-data-collection/
|   +-- README.md
|-- phase-2-document-processing/
|   +-- README.md
|-- phase-3-retrieval-engine/
|   +-- README.md
|-- phase-4-response-generation/
|   +-- README.md
|-- phase-5-backend-api/
|   +-- README.md
+-- phase-6-frontend-ui/
    +-- README.md
```

---

## 6. Phase 1 — Data Collection & Corpus Preparation

### 6.1 Objective

Collect official public HTML and PDFs for Phase 1 using the URL batches in **`data/sources.json`**: Groww Help (user flows), ICICI/HDFC/Nippon scheme and factsheet pages, and AMFI/SEBI pages for education and refusals.

### 6.2 Data Flow

```
Daily @ 09:15 (scheduler) --> scrape_sources.py
                                    |
sources.json (URL registry) <-------+
       |
       v
scrape_sources.py
       |
       |-- [HTML pages] --> requests + BeautifulSoup validation
       |                        |
       |                        v
       |                   data/raw/html/{source_type}_{scheme_slug}_{date}.html
       |                   data/raw/html/{source_type}_{scheme_slug}_{date}.meta.json
       |
       +-- [PDF documents] --> requests (binary download)
                                |
                                v
                           data/raw/pdf/{source_type}_{scheme_slug}_{date}.pdf
                           data/raw/pdf/{source_type}_{scheme_slug}_{date}.meta.json
```

### 6.3 URL Registry Schema (`data/sources.json`)

```json
{
  "metadata": {
    "description": "Multi-AMC Mutual Fund FAQ Assistant corpus",
    "amcs": ["ICICI Prudential", "HDFC Mutual Fund", "Nippon India Mutual Fund"],
    "platforms": ["Groww"],
    "created_at": "2026-04-14",
    "total_sources": 21
  },
  "sources": [
    {
      "id": "src_001",
      "url": "https://groww.in/help",
      "source_type": "help_guide",
      "document_format": "html",
      "batch": "groww_help",
      "scheme_name": "general",
      "category": "platform_help",
      "last_scraped": null,
      "scrape_status": "pending",
      "notes": "Groww main help center landing page"
    }
  ]
}
```

**Valid `source_type` values:** `scheme_page`, `factsheet`, `sid`, `kim`, `faq`, `help_guide`, `regulatory`, `tax_guide`

**Valid `scrape_status` values:** `pending`, `success`, `failed`, `stale`

### 6.4 Scraping Pipeline (`scripts/scrape_sources.py`)

**Design principles:**
- Polite scraping: 2-second delay between requests, respectful User-Agent header
- Idempotent: checks `last_scraped` timestamp; skips if within freshness window (configurable, default 7 days)
- Robust: retries failed downloads up to 3 times with exponential backoff
- Metadata tracking: each downloaded file has a `.meta.json` sidecar file

**Sidecar metadata schema (`.meta.json`):**

```json
{
  "source_id": "src_001",
  "url": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund",
  "scraped_at": "2026-04-14T10:30:00Z",
  "http_status": 200,
  "content_type": "text/html",
  "file_size_bytes": 45230,
  "file_path": "data/raw/html/scheme_page_hdfc-flexi-cap_20260414.html"
}
```

**File naming convention:** `{source_type}_{scheme_slug}_{YYYYMMDD}.{ext}`

### 6.5 Key Files

| File | Purpose |
|------|---------|
| `data/sources.json` | Master URL registry with metadata |
| `scripts/scrape_sources.py` | Web scraping orchestrator |
| `data/raw/html/` | Stored HTML files + sidecars |
| `data/raw/pdf/` | Stored PDF files + sidecars |

### 6.6 Dependencies

- `requests` — HTTP fetching
- `beautifulsoup4` — HTML validation (content loaded check)
- `pathlib` — File path management (stdlib)
- `json`, `time`, `datetime` — Stdlib utilities

---

## 7. Phase 2 — Document Processing & Embedding Pipeline

### 7.1 Objective

Extract text from raw HTML/PDF files, clean and normalize it, split into semantically meaningful chunks, generate vector embeddings, and ingest into Qdrant.

### 7.2 Data Flow

```
data/raw/html/*.html ----+
                          |
                          v
data/raw/pdf/*.pdf -------> process_documents.py
                                |
                                |-- HTML: BeautifulSoup
                                |   - Extract main content, tables, headings
                                |   - Strip nav, footer, scripts, styles
                                |
                                |-- PDF: PyMuPDF (fitz)
                                |   - Extract text per page
                                |   - pdfplumber fallback for tables
                                |
                                v
                          Text Cleaning
                                |
                                |-- Unicode normalization (NFKC)
                                |-- Financial term standardization
                                |-- Boilerplate removal
                                |-- Date format normalization
                                |
                                v
                          Chunking (RecursiveCharacterTextSplitter)
                                |
                                |-- chunk_size: 500 chars
                                |-- chunk_overlap: 75 chars
                                |-- Section-aware splitting
                                |
                                v
                   data/processed/chunks/*.json
                                |
                                v
                   generate_embeddings.py
                                |
                                |-- Embed texts (batch_size=64)
                                |   Primary: Gemini text-embedding-004 (768d)
                                |   Fallback: all-MiniLM-L6-v2 (384d)
                                |
                                v
                          Qdrant Upsert
                          Collection: mutual_fund_faq
                          Distance: Cosine
```

### 7.3 Text Extraction Strategies

**HTML extraction (`process_documents.py`):**
- Parse with BeautifulSoup, target main content containers
- Preserve heading hierarchy (h1/h2/h3) as section markers for chunk metadata
- Convert tables to flattened key-value text: `"Expense Ratio: 1.62% (Regular), 0.55% (Direct)"`
- Strip: `<script>`, `<style>`, `<nav>`, `<footer>`, ad containers

**PDF extraction (`process_documents.py`):**
- Primary: PyMuPDF (`fitz`) for text-per-page extraction
- Fallback: `pdfplumber` for table-heavy pages (factsheets with tabular data)
- Detect text-primary vs. table-primary pages and route accordingly
- Tables converted to flattened key-value text representation
- Strip page numbers, headers/footers, watermarks

### 7.4 Text Cleaning & Normalization

Implemented as reusable functions (shared between ingestion and query-time):

| Operation | Details |
|-----------|---------|
| Unicode normalization | NFKC (handles rupee symbol, Hindi characters) |
| Whitespace cleanup | Collapse multiple spaces/newlines |
| Financial terms | Keep uppercase: NAV, AUM, SIP, SWP, STP, ELSS, KIM, SID |
| Boilerplate removal | Detect and remove repeated disclaimer text via fingerprinting |
| Date normalization | Convert to ISO-8601 (YYYY-MM-DD) |
| PDF artifacts | Remove page numbers, repeated headers/footers |

### 7.5 Chunking Strategy

**Algorithm:** `RecursiveCharacterTextSplitter` from `langchain-text-splitters`

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `chunk_size` | 500 characters | Short factual content; keeps chunks focused on single facts |
| `chunk_overlap` | 75 characters | ~15% overlap; preserves context at boundaries |
| `separators` | `["\n\n", "\n", ". ", " "]` | Prefer paragraph > sentence > word boundaries |

**Section-aware enhancements:**
- Split documents at H2/H3 heading boundaries before chunking
- Each chunk inherits the nearest heading as its `section` metadata
- Never chunk across scheme boundaries in multi-scheme documents
- Tables become single chunks (even if >500 chars), tagged with `doc_type: "table"`

### 7.6 Chunk Metadata Schema

Each chunk is stored as a JSON file in `data/processed/chunks/`:

```json
{
  "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
  "text": "Illustrative chunk text for a scheme detail page (expense ratio, plans, benchmark — values must match the scraped source).",
  "metadata": {
    "source_url": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund",
    "source_id": "src_008",
    "scheme_name": "HDFC Flexi Cap Fund",
    "doc_type": "scheme_page",
    "section": "Fund Details",
    "page_number": null,
    "last_updated": "2026-04-01",
    "chunk_index": 3,
    "total_chunks": 12
  }
}
```

### 7.7 Qdrant Collection Configuration

| Setting | Value |
|---------|-------|
| Collection name | `mutual_fund_faq` |
| Vector size | 768 (Gemini) or 384 (MiniLM) — driven by config |
| Distance metric | Cosine |
| Payload indexes | `scheme_name` (keyword), `doc_type` (keyword), `section` (keyword) |

**Ingestion process (`scripts/generate_embeddings.py`):**
1. Read all chunk JSON files from `data/processed/chunks/`
2. Batch embed texts (batch_size=64 to respect API rate limits)
3. Upsert to Qdrant: `point_id = chunk UUID`, `vector = embedding`, `payload = all metadata + text`
4. Log: total points ingested, collection stats

### 7.8 Embedding Model Abstraction (`app/utils/embeddings.py`)

```
Interface:
  embed_texts(texts: list[str]) -> list[list[float]]   # Batch embedding
  embed_query(query: str) -> list[float]                # Single query embedding

Config switch (config/settings.py):
  EMBEDDING_MODEL = "gemini"   # or "local"

Models:
  "gemini"  -> google-generativeai text-embedding-004 (768 dimensions)
  "local"   -> sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
```

### 7.9 Key Files

| File | Purpose |
|------|---------|
| `scripts/process_documents.py` | Text extraction, cleaning, chunking |
| `scripts/generate_embeddings.py` | Embedding generation + Qdrant ingestion |
| `app/utils/embeddings.py` | Embedding model wrapper (Gemini + MiniLM) |
| `app/utils/text_processing.py` | Shared text cleaning utilities |
| `data/processed/chunks/` | Processed chunk JSON files |

### 7.10 Dependencies

- `beautifulsoup4` — HTML extraction
- `PyMuPDF` (`fitz`) — PDF extraction
- `pdfplumber` — PDF table extraction fallback
- `langchain-text-splitters` — RecursiveCharacterTextSplitter
- `google-generativeai` — Gemini embeddings
- `sentence-transformers` — Local fallback embeddings
- `qdrant-client` — Qdrant Python SDK

---

## 8. Phase 3 — RAG Retrieval Engine

### 8.1 Objective

Process user queries, classify intent, perform vector similarity search against Qdrant, re-rank results for relevance and diversity, and assemble context for LLM generation.

### 8.2 End-to-End Retrieval Flow

```
User Query: "What is the expense ratio of HDFC Flexi Cap Fund?"
       |
       v
  Query Preprocessing (app/services/retriever.py)
       |
       |-- Normalize text (lowercase, strip whitespace)
       |-- Expand abbreviations: "ER" -> "expense ratio"
       |-- Extract scheme name: "HDFC Flexi Cap Fund" (fuzzy match)
       |
       v
  Intent Classification (app/services/guardrails.py)
       |
       |-- PII scan (regex): PASS
       |-- Advisory keyword check: PASS
       |-- Comparison check: PASS
       |-- Result: FACTUAL
       |
       v
  Embed Query (app/utils/embeddings.py)
       |
       |-- embed_query("expense ratio hdfc flexi cap fund")
       |-- Returns: [0.012, -0.034, 0.078, ...] (768d vector)
       |
       v
  Qdrant Search (app/services/retriever.py)
       |
       |-- Collection: mutual_fund_faq
       |-- top_k: 5
       |-- Score threshold: 0.65
       |-- Filter: scheme_name = "HDFC Flexi Cap Fund"
       |
       |-- Returns 5 candidate chunks with scores
       |
       v
  Re-Ranking: MMR (app/services/retriever.py)
       |
       |-- lambda_param: 0.7 (70% relevance, 30% diversity)
       |-- Select top 3 diverse, relevant chunks
       |
       v
  Context Assembly
       |
       |-- RetrievalResult:
       |     chunks: [chunk_1, chunk_2, chunk_3]
       |     primary_source_url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund"
       |     primary_source_date: "2026-04-01"
       |     confidence: 0.82
       |
       v
  Pass to Phase 4 (Generator)
```

### 8.3 Intent Classification Taxonomy

| Intent | Example Query | Action |
|--------|--------------|--------|
| `FACTUAL` | "What is the expense ratio of HDFC Flexi Cap Fund?" | Proceed to retrieval |
| `PROCEDURAL` | "How do I download my capital gains statement?" | Proceed to retrieval |
| `ADVISORY` | "Should I invest in Nippon India Tax Saver ELSS?" | Refuse with educational link |
| `COMPARISON` | "Which is better, Large Cap or Multicap?" | Refuse with educational link |
| `PII_DETECTED` | "My PAN is ABCDE1234F, check my folio" | Refuse, warn about PII |
| `OUT_OF_SCOPE` | "What's the weather today?" | Refuse, redirect to MF topics |

**Classification implementation (rule-based, no LLM call):**

Layer 1 — PII scan (highest priority):
- PAN: `[A-Z]{5}[0-9]{4}[A-Z]`
- Aadhaar: `\d{4}\s?\d{4}\s?\d{4}`
- Email: standard email regex
- Phone: `(\+91[\-\s]?)?[6-9]\d{9}`

Layer 2 — Advisory keyword patterns:
- `should i (invest|buy|sell|redeem|switch)`
- `(recommend|suggest).*fund`
- `(best|top|worst).*fund`
- `(good|bad) (investment|fund|scheme)`
- `will (it|this|the fund) (give|generate|earn).*return`

Layer 3 — Comparison detection:
- `(compare|vs|versus|better than|which fund)`

Layer 4 — Default: `FACTUAL` (proceed to retrieval)

### 8.4 Query Enhancement

Before vector search, the query is enhanced:

| Enhancement | Example |
|-------------|---------|
| Abbreviation expansion | "ER" -> "expense ratio", "NAV" -> "net asset value" |
| Scheme name extraction | "HDFC Flexi Cap" -> filter: `scheme_name = "HDFC Flexi Cap Fund"` |
| Fuzzy matching | "hdfc flexicap" -> matched to "HDFC Flexi Cap Fund" |

Known scheme names are stored as a list in config for fuzzy matching.

### 8.5 Vector Search Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `top_k` | 5 | Retrieve 5 candidates for re-ranking down to 3 |
| `score_threshold` | 0.65 | Below this, "no relevant information found" |
| Filter: `scheme_name` | Applied if detected in query | Narrows search to relevant scheme only |
| Filter: `doc_type` | Optional, not applied by default | Could be used for specific doc type queries |

**Threshold behavior:**
- All 5 results below 0.65 -> skip LLM, return "I don't have information about that in my sources"
- Some results above 0.65 -> proceed with those above threshold only

### 8.6 Re-Ranking: Maximal Marginal Relevance (MMR)

**Why MMR instead of a cross-encoder?**
- Corpus is small (~150-200 chunks). Initial Qdrant retrieval is already precise.
- MMR adds diversity cheaply (no extra model, no extra latency).
- Cross-encoder would add 200-400ms latency for marginal improvement at this scale.

**MMR parameters:**
- `lambda_param = 0.7` — 70% relevance to query, 30% diversity from already-selected chunks
- Select top 3 from the 5 candidates
- Prevents returning 3 chunks from the same paragraph/section

### 8.7 Retrieval Result Schema

```
RetrievalResult:
    chunks: list[RetrievedChunk]        # Top 3 after MMR
        - text: str                     # Chunk text content
        - score: float                  # Similarity score
        - metadata: ChunkMetadata       # Full metadata dict
    primary_source_url: str             # URL from highest-scored chunk
    primary_source_date: str            # last_updated from highest-scored chunk
    confidence: float                   # Average score of top 3 chunks
```

The `primary_source_url` and `primary_source_date` flow into the response formatter (Phase 4) to satisfy the "1 citation + footer date" requirement.

### 8.8 Key Files

| File | Purpose |
|------|---------|
| `app/services/retriever.py` | Vector search, query enhancement, MMR re-ranking |
| `app/services/guardrails.py` | Intent classification (PII, advisory, comparison, scope) |
| `app/utils/embeddings.py` | Query embedding (shared with ingestion) |
| `app/utils/text_processing.py` | Query normalization, abbreviation expansion |
| `app/models/enums.py` | Intent enum definitions |

### 8.9 Dependencies

- `qdrant-client` — Qdrant search API
- `numpy` — MMR similarity calculations (stdlib for cosine similarity)

---

## 9. Phase 4 — LLM Response Generation & Guardrails

### 9.1 Objective

Generate concise, factual, source-backed responses using Google Gemini, with comprehensive input/output guardrails to ensure compliance with facts-only constraints.

### 9.2 Full Generation Pipeline

```
                +------------------------+
                |      User Query        |
                +----------+-------------+
                           |
                           v
                +------------------------+
                |   INPUT GUARDRAILS     |
                |   (guardrails.py)      |
                |                        |
                |   1. PII scan          |
                |   2. Advisory detect   |
                |   3. Comparison detect |
                |   4. Scope check       |
                +----------+-------------+
                           |
              +------------+------------+
              |                         |
         FACTUAL /                 REFUSED
         PROCEDURAL            (advisory / PII /
              |                 out-of-scope)
              |                         |
              v                         v
     +-----------------+     Return refusal template
     |   RETRIEVAL     |     with educational link
     |   (Phase 3)     |
     +--------+--------+
              |
              v
     +-----------------+
     |  CONFIDENCE     |
     |  CHECK          |
     |  (>= 0.65?)    |
     +--------+--------+
              |
     +--------+--------+
     |                  |
   >= 0.65          < 0.65
     |                  |
     v                  v
+-----------+    "I don't have reliable
|  GEMINI   |    information about that
|  LLM CALL |    in my sources."
|           |
|  System   |
|  prompt + |
|  Context  |
|  + Query  |
+-----+-----+
      |
      v
+-------------------+
| OUTPUT GUARDRAILS |
|                   |
| 1. Sentence cap   |
|    (max 3)        |
| 2. Advice scan    |
|    (keyword check)|
| 3. PII scan       |
|    (in output)    |
| 4. Add citation   |
| 5. Add footer     |
+--------+----------+
         |
         v
  +-------------+
  | Final       |
  | Response    |
  +-------------+
```

### 9.3 System Prompt Design (`config/prompts.py`)

**SYSTEM_PROMPT** (see `config/prompts.py` for the canonical version):

```
You are a facts-only mutual fund FAQ assistant.

STRICT RULES:
1. Answer only factual, verifiable queries using the provided context.
2. Maximum 3 sentences.
3. Always include exactly ONE source link in the response.
4. NEVER provide investment advice, recommendations, opinions, or comparisons.
5. NEVER fabricate or extrapolate beyond the context.
6. Do not mention "context" or "documents" explicitly.
7. If the query is advisory, refuse politely and include exactly one AMFI or SEBI link.
```

**CONTEXT_INJECTION_TEMPLATE:**

```
Use ONLY the following context to answer the user's question.

Context:
---
{chunk_1}
---
{chunk_2}
---
{chunk_3}
---

User Question: {user_query}
```

**REFUSAL_TEMPLATE (advisory queries):**

Single educational URL placeholder `{educational_link}` — prefer `https://www.amfiindia.com/investor-corner` or `https://www.sebi.gov.in/sebi_data/faqfiles/mutual_funds.html` (exact choice is configured in code).

```
I'm designed to provide factual information only and cannot offer investment advice
or recommendations. For investment guidance, please consult a SEBI-registered
investment advisor. You may find helpful resources at: {educational_link}
```

**NO_INFO_TEMPLATE (low confidence):**

```
I don't have reliable information about that in my current sources. You can check
the relevant AMC website, AMFI, or SEBI for the latest details.
```

### 9.4 Gemini LLM Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Model | `gemini-2.0-flash` | Fast, free tier generous (15 RPM / 1M tokens/min) |
| Temperature | `0.1` | Near-deterministic; factual content needs consistency |
| Max output tokens | `256` | 3 sentences rarely exceed 150 tokens; safety buffer |
| Top-p | `0.95` | Standard; combined with low temp ensures focused output |
| Safety settings | Default | Gemini's built-in safety + our custom guardrails |

### 9.5 Response Formatting (`app/services/generator.py`)

Post-processing steps applied to every Gemini response:

1. **Sentence count check:** Split on `. `, count sentences. If >3, truncate to first 3 sentences.
2. **Advice language scan:** Regex check for "you should", "I recommend", "consider investing". If detected, replace entire response with refusal template.
3. **PII scan in output:** Regex check (same patterns as input). If detected, replace response with generic safe response.
4. **Append citation:** `\n\nSource: {primary_source_url}`
5. **Append footer:** `\nLast updated from sources: {primary_source_date}`

**Final response format example:**

```
Illustrative answer (must be grounded in retrieved chunks): expense ratio and plan types as stated on the official scheme page.

Source: https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund
Last updated from sources: 2026-04-01
```

### 9.6 Hallucination Mitigation Strategies

| Strategy | Implementation | Layer |
|----------|---------------|-------|
| Grounded generation | System prompt: "use ONLY the provided context" | Prompt |
| Low temperature | `temperature=0.1` for near-deterministic output | Model config |
| Confidence threshold | Skip LLM if retrieval `confidence < 0.65` | Pre-generation |
| Number verification | Check that numbers in response appear in context chunks | Post-generation |
| Source-only response | If context is insufficient, return "no info" template | Pre-generation |

### 9.7 Educational Redirect Links

Stored in `config/prompts.py`:

| Category | Link |
|----------|------|
| General investing education | `https://www.amfiindia.com/investor-corner/knowledge-center` |
| SEBI registered advisors | `https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13` |
| Mutual fund basics | `https://www.amfiindia.com/mutual-fund/new-to-mutual-fund` |

### 9.8 Key Files

| File | Purpose |
|------|---------|
| `app/services/generator.py` | Gemini LLM call, response formatting, output validation |
| `app/services/guardrails.py` | Input guardrails (PII, advisory, comparison, scope) + output guardrails |
| `app/services/rag_engine.py` | Orchestrates the full pipeline (guardrails -> retrieval -> generation) |
| `config/prompts.py` | All prompt templates, refusal messages, educational links |

### 9.9 Dependencies

- `google-generativeai` — Gemini API (gemini-2.0-flash)
- `re` — Regex for guardrail patterns (stdlib)

---

## 10. Phase 5 — Backend API (FastAPI)

### 10.1 Objective

Expose the RAG engine as a RESTful API with multi-thread chat session management, rate limiting, structured error handling, and health monitoring.

### 10.2 API Endpoint Design

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| `POST` | `/api/chat` | `routers/chat.py` | Send a message, get a response |
| `GET` | `/api/threads` | `routers/threads.py` | List all thread summaries |
| `POST` | `/api/threads` | `routers/threads.py` | Create a new thread |
| `GET` | `/api/threads/{thread_id}` | `routers/threads.py` | Get full thread history |
| `DELETE` | `/api/threads/{thread_id}` | `routers/threads.py` | Delete a thread |
| `GET` | `/api/health` | `routers/health.py` | System health + Qdrant check |

### 10.3 Request/Response Schemas (`app/models/schemas.py`)

**ChatRequest:**

```
{
  "thread_id": "uuid-string",
  "message": "What is the expense ratio of HDFC Flexi Cap Fund?"  // max 500 chars
}
```

**ChatResponse:**

```
{
  "thread_id": "uuid-string",
  "message_id": "uuid-string",
  "response": "The expense ratio for HDFC Flexi Cap Fund...\n\nSource: https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund\nLast updated from sources: 2026-04-01",
  "source_url": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund",
  "intent": "FACTUAL",
  "timestamp": "2026-04-14T10:30:00Z"
}
```

**ThreadSummary:**

```
{
  "thread_id": "uuid-string",
  "title": "What is the expense ratio of HDFC...",
  "created_at": "2026-04-14T10:30:00Z",
  "message_count": 4
}
```

**ThreadDetail:**

```
{
  "thread_id": "uuid-string",
  "title": "What is the expense ratio of HDFC...",
  "messages": [
    {
      "role": "user",
      "content": "What is the expense ratio of HDFC Flexi Cap Fund?",
      "timestamp": "2026-04-14T10:30:00Z",
      "source_url": null
    },
    {
      "role": "assistant",
      "content": "The expense ratio for HDFC Flexi Cap Fund...",
      "timestamp": "2026-04-14T10:30:01Z",
      "source_url": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund"
    }
  ]
}
```

### 10.4 Request Processing Flow

```
Streamlit --POST /api/chat--> FastAPI (app/main.py)
                                  |
                                  v
                          Pydantic Validation
                          (ChatRequest schema)
                                  |
                                  v
                          thread_manager.get_or_create(thread_id)
                                  |
                                  v
                          rag_engine.process_query(
                              query = message,
                              chat_history = thread.last_3_messages
                          )
                                  |
                                  |-- guardrails.classify_intent()
                                  |-- retriever.retrieve()  [if factual]
                                  |-- generator.generate()  [if factual]
                                  |-- guardrails.validate_output()
                                  |
                                  v
                          thread_manager.add_messages(
                              thread_id,
                              user_msg,
                              assistant_msg
                          )
                                  |
                                  v
                          Return ChatResponse
```

### 10.5 Multi-Thread Chat Session Manager (`app/services/thread_manager.py`)

**Storage:** In-memory Python `dict[str, ThreadState]` keyed by `thread_id` (UUID v4).

| Feature | Specification |
|---------|---------------|
| Thread ID | UUID v4, generated on creation |
| Auto-title | First user message, truncated to 50 characters + "..." |
| Max threads | 50 (oldest auto-evicted via LRU when exceeded) |
| Max messages per thread | 100 (to prevent unbounded memory growth) |
| Thread deletion | Remove from dict, free memory |

**Why in-memory?** This is a demo/single-user deployment. The thread manager is written against an abstract interface (`BaseThreadManager`) so it can be swapped to SQLite or Redis later without changing the rest of the code.

### 10.6 Error Handling

**Custom exception hierarchy:**

```
AppException (base)
  |-- GuardrailException    -> 400 Bad Request
  |-- RetrievalException    -> 502 Bad Gateway
  |-- GenerationException   -> 502 Bad Gateway
  |-- ThreadNotFoundException -> 404 Not Found
  |-- RateLimitException    -> 429 Too Many Requests
```

All exceptions caught by FastAPI middleware, returning JSON error responses.

**Gemini API resilience:**
- Retry: max 2 retries, exponential backoff (1s, 2s)
- On persistent failure: return "Service temporarily unavailable. Please try again."

### 10.7 Rate Limiting

- Library: `slowapi` (lightweight, FastAPI-compatible)
- Limit: 10 requests/minute per IP address
- Response on limit: HTTP 429 with message "Please wait a moment before sending another question."

### 10.8 Logging

- Structured JSON logging via Python `logging` module
- Log every request with: `thread_id`, `intent`, `retrieval_confidence`, `response_time_ms`
- Log levels: INFO for normal requests, WARNING for rate limits and low confidence, ERROR for exceptions

### 10.9 Health Endpoint (`GET /api/health`)

```
Response:
{
  "status": "healthy",
  "qdrant_connected": true,
  "qdrant_collection_points": 187,
  "gemini_api": "configured",
  "uptime_seconds": 3600
}
```

If Qdrant is unreachable: returns HTTP 503 with `"status": "degraded"`.

### 10.10 Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app initialization, middleware, exception handlers |
| `app/routers/chat.py` | `POST /api/chat` endpoint |
| `app/routers/threads.py` | Thread CRUD endpoints |
| `app/routers/health.py` | Health check endpoint |
| `app/models/schemas.py` | Pydantic v2 request/response models |
| `app/models/enums.py` | Intent types, document types enums |
| `app/services/rag_engine.py` | Core RAG orchestrator |
| `app/services/thread_manager.py` | In-memory thread state management |
| `config/settings.py` | Central configuration (env vars, defaults) |

### 10.11 Dependencies

- `fastapi` — Web framework
- `uvicorn` — ASGI server
- `pydantic` v2 — Schema validation
- `slowapi` — Rate limiting
- `python-dotenv` — Environment variable loading

---

## 11. Phase 6 — Frontend Chat UI (Streamlit)

### 11.1 Objective

Build a minimal, clean chat interface using Streamlit with multi-thread support, disclaimer display, example questions, and seamless API integration.

### 11.2 UI Layout

```
+------------------------------------------------------------+
|  SIDEBAR                    |  MAIN AREA                   |
|                             |                               |
|  +------------------------+ |  +-------------------------+  |
|  | Mutual Fund FAQ        | |  | DISCLAIMER BANNER       |  |
|  | Assistant              | |  | "Facts-only. No         |  |
|  +------------------------+ |  |  investment advice."     |  |
|                             |  +-------------------------+  |
|  [+ New Chat]               |                               |
|                             |  +-------------------------+  |
|  Thread List:               |  | WELCOME MESSAGE          |  |
|  > Expense ratio of...      |  | (shown on new threads)   |  |
|    ELSS lock-in per...      |  |                          |  |
|    How to download...       |  | "Hello! I can help with  |  |
|                             |  |  factual questions about |  |
|  +------------------------+ |  |  ICICI, HDFC, Nippon    |  |
|  | About                  | |  |  schemes, Groww Help,   |  |
|  | Facts-only assistant.  | |  |  AMFI, and SEBI."        |  |
|  | Sources: Official AMC, | |  |                          |  |
|  | AMFI, SEBI only.       | |  | Try asking:              |  |
|  +------------------------+ |  | o "What is the expense  |  |
|                             |  |    ratio of HDFC Flexi  |  |
|                             |  |    Cap Fund?"            |  |
|                             |  | o "What is the lock-in  |  |
|                             |  |    period for ELSS?"     |  |
|                             |  | o "How do I download my |  |
|                             |  |    capital gains         |  |
|                             |  |    report on Groww?"     |  |
|                             |  +-------------------------+  |
|                             |                               |
|                             |  Chat Messages (scrollable):  |
|                             |  User: ...                    |
|                             |  Assistant: ...               |
|                             |    Source: [link]             |
|                             |    Last updated: date         |
|                             |                               |
|                             |  [Ask a question...]          |
+------------------------------------------------------------+
```

### 11.3 Session State Management

| Key | Type | Purpose |
|-----|------|---------|
| `current_thread_id` | `str or None` | Currently active thread |
| `threads` | `dict[str, ThreadSummary]` | Thread list cache (refreshed from API) |
| `messages` | `list[MessageEntry]` | Current thread's messages |
| `api_base_url` | `str` | FastAPI backend URL (default: `http://localhost:8000`) |

### 11.4 UI Behaviors

| Trigger | Action |
|---------|--------|
| App load | Call `GET /api/threads`, populate sidebar. Auto-create thread if none exist. |
| "New Chat" click | Call `POST /api/threads`, switch `current_thread_id`, clear messages. |
| Thread selection | Call `GET /api/threads/{id}`, load messages into main area. |
| Message send | Call `POST /api/chat`. Show `st.spinner("Thinking...")` during API call. Append user + assistant messages. |
| Example question click | `st.button` for each example; injects question and triggers send. |
| Backend unavailable | Show `st.error("Backend not available. Ensure API server is running.")` |

### 11.5 Citation Rendering

- Parse `source_url` from `ChatResponse`
- Render as clickable markdown link below assistant message
- Footer ("Last updated from sources: date") rendered in smaller, muted text

### 11.6 API Integration

Helper functions in `frontend/streamlit_app.py`:

```
api_send_message(thread_id, message) -> ChatResponse
api_list_threads() -> list[ThreadSummary]
api_create_thread() -> ThreadSummary
api_get_thread(thread_id) -> ThreadDetail
api_delete_thread(thread_id) -> bool
```

All functions use Python `requests` library. Errors wrapped with user-friendly messages.

### 11.7 Key Files

| File | Purpose |
|------|---------|
| `frontend/streamlit_app.py` | Complete Streamlit chat application |

### 11.8 Dependencies

- `streamlit` — UI framework
- `requests` — HTTP client for API calls

---

## 12. Configuration Reference

### 12.1 Central Configuration (`config/settings.py`)

All values loaded from environment variables with sensible defaults:

| Setting | Env Variable | Default | Description |
|---------|-------------|---------|-------------|
| Gemini API Key | `GEMINI_API_KEY` | (required) | Google AI API key |
| Gemini Model | `GEMINI_MODEL` | `gemini-2.0-flash` | LLM model name |
| Embedding Model | `EMBEDDING_MODEL` | `gemini` | `"gemini"` or `"local"` |
| Qdrant Host | `QDRANT_HOST` | `localhost` | Qdrant server host |
| Qdrant Port | `QDRANT_PORT` | `6333` | Qdrant server port |
| Qdrant Collection | `QDRANT_COLLECTION` | `mutual_fund_faq` | Collection name |
| Retrieval Top-K | `RETRIEVAL_TOP_K` | `5` | Chunks to retrieve |
| Score Threshold | `RETRIEVAL_THRESHOLD` | `0.65` | Minimum similarity score |
| Re-rank Top-N | `RERANK_TOP_N` | `3` | Chunks after MMR |
| Max Sentences | `MAX_RESPONSE_SENTENCES` | `3` | Response length cap |
| Rate Limit | `RATE_LIMIT` | `10/minute` | API rate limit per IP |
| Log Level | `LOG_LEVEL` | `INFO` | Logging verbosity |

### 12.2 Environment File (`.env.example`)

```
# Required
GEMINI_API_KEY=your-gemini-api-key-here

# Optional (defaults shown)
GEMINI_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=gemini
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=mutual_fund_faq
RETRIEVAL_TOP_K=5
RETRIEVAL_THRESHOLD=0.65
RERANK_TOP_N=3
MAX_RESPONSE_SENTENCES=3
RATE_LIMIT=10/minute
LOG_LEVEL=INFO
```

---

## 13. Startup & Run Sequence

```
# Step 1: Start Qdrant (one-time, keep running)
docker run -p 6333:6333 qdrant/qdrant

# Step 2: Initial data pipeline (and same steps scheduled daily @ 09:15)
python scripts/scrape_sources.py
python scripts/process_documents.py
python scripts/generate_embeddings.py

# Optional: single entrypoint for the scheduler (when implemented)
# python scripts/daily_ingest.py

# Step 3: Start backend API
uvicorn app.main:app --reload --port 8000

# Step 4: Start frontend (separate terminal)
streamlit run frontend/streamlit_app.py --server.port 8501
```

**Scheduler (production):** Configure the host to run `scrape_sources.py` (and optionally the full `daily_ingest.py` chain) every day at **09:15** local time. Ensure the job runs in the project virtual environment and has network access to the official URLs.

---

## 14. Key Design Decisions & Trade-offs

| Decision | Chosen Approach | Alternative Considered | Rationale |
|----------|----------------|----------------------|-----------|
| Intent classification | Rule-based regex | LLM-based classification | Zero latency, zero cost, deterministic; sufficient for clear advisory vs. factual distinction |
| Re-ranking | MMR (no extra model) | Cross-encoder reranker | Small corpus (~200 chunks) doesn't warrant complexity; MMR adds diversity cheaply |
| Thread storage | In-memory dict | SQLite / Redis | Demo scope; abstract interface allows easy swap later |
| Embedding model | Gemini primary + MiniLM fallback | Single model only | Resilience against API rate limits during bulk ingestion |
| Chunking size | 500 chars, section-aware | Larger chunks (1000+) | Short factual answers need precise, focused chunks; less noise in context |
| LLM temperature | 0.1 | 0.0 or 0.3+ | Near-deterministic but allows natural phrasing; not fully rigid |
| Frontend-Backend split | Streamlit + FastAPI | Streamlit-only with embedded logic | Separation of concerns; API testable independently; frontend swappable |
| Scraping approach | requests + BS4 | Selenium/Playwright | Official AMC pages don't require JS rendering; lightweight is better |

---

## 15. Known Limitations

1. **In-memory thread storage** — All chat threads are lost on server restart. Adequate for demo; swap to SQLite for persistence.
2. **Scheduler operations** — The architecture assumes a daily 09:15 job; failure of cron/Task Scheduler must be monitored. Scraping must stay within sites’ terms and rate limits.
3. **Multi-source corpus** — Phase 1 spans Groww Help plus three AMCs and regulators; out-of-scope schemes are not in `sources.json` until added.
4. **Free tier rate limits** — Gemini free tier has rate limits (15 RPM). Heavy concurrent usage may hit limits.
5. **No authentication** — API is open. Add auth middleware for production deployment.
6. **Rule-based intent classification** — May miss nuanced advisory queries. Could upgrade to LLM-based classification later.
7. **No conversation context** — Each query is treated independently (last 3 messages passed for context, but no deep conversation tracking).
