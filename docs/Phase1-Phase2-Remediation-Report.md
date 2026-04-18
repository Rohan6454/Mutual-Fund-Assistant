# Phase 1/2 Remediation Report

This document records the stabilization work done before moving deeper into later phases.

## Scope

- Fixed scraper file naming collisions.
- Replaced dead URLs in `data/sources.json` with reachable equivalents.
- Migrated embedding integration to the supported Google GenAI SDK path.
- Re-ran scrape -> chunk -> embed indexing and measured coverage.

## What Failed

### 1) Scraper filename collisions

**Symptom**
- Multiple sources overwrote each other in `data/raw/html/` because the filename only used `source_type + scheme/batch + date`.
- Example: Groww help pages shared the same generated filename on the same date.

**Impact**
- Corpus silently lost documents.
- Metadata sidecars did not represent all source URLs uniquely.

### 2) Dead and outdated source URLs

**Symptom**
- Several initial URLs returned `404` or TLS errors (notably old AMC/regulatory paths).

**Impact**
- Scrape success ratio dropped significantly.
- Downstream chunking had low coverage and sparse retrieval.

### 3) Deprecated/unsupported embedding integration path

**Symptom**
- The old `google.generativeai` embedding flow failed with model/method mismatch (`text-embedding-004` not found in the used endpoint path).

**Impact**
- Embedding step failed.
- Qdrant was either empty or partially populated.

### 4) Gemini free-tier embedding quota limits

**Symptom**
- `429 RESOURCE_EXHAUSTED` on `gemini-embedding-001` during full-corpus embedding.

**Impact**
- Full Gemini upsert could not complete in one run under free-tier limits.

## What Was Required

- Stable file naming keyed by source identity.
- Reachable source registry with 2xx responses.
- SDK migration to supported embedding client.
- A practical fallback path when Gemini quota is exhausted.

## What Was Changed

## Code/Data changes

### Scraper reliability

- Updated `phase-1-data-collection/scrape_sources.py`:
  - Filename now includes `source_id` and URL-path slug to guarantee uniqueness.
  - Added startup cleanup for previous `data/raw/html/*` and `data/raw/pdf/*` artifacts (except `.gitkeep`), preventing stale/duplicate accumulation across runs.

### Source refresh

- Updated broken entries in `data/sources.json`:
  - HDFC scheme URLs migrated to working `/explore/.../regular` paths.
  - Nippon scheme URLs migrated to working `mf.nipponindiaim.com/FundsAndPerformance/Pages/...` paths.
  - Factsheet endpoints updated to live pages:
    - ICICI: `digitalfactsheet.icicipruamc.com/fact/`
    - HDFC: `hdfcfund.com/investor-services/factsheets`
    - Nippon: `mf.nipponindiaim.com/investor-service/downloads/factsheet-portfolio-and-other-disclosures`
  - AMFI and SEBI regulatory URLs updated to current reachable endpoints.

### Embedding SDK migration

- Updated `phase-2-document-processing/embeddings.py`:
  - Gemini path now uses `google.genai` (`Client().models.embed_content`).
  - Added support for configurable embedding model and output dimensionality.
  - Uses batch embed calls per input batch.
- Added dependency: `google-genai` in `requirements.txt`.
- Added settings in `config/settings.py` and `.env.example`:
  - `GEMINI_EMBEDDING_MODEL` (default `gemini-embedding-001`)
  - `GEMINI_EMBEDDING_DIMENSION` (default `768`)

## Execution and outcomes

### Full pipeline rerun

1. `phase-1-data-collection/scrape_sources.py` rerun on refreshed URLs.
2. `phase-2-document-processing/process_documents.py` rerun.
3. `phase-2-document-processing/generate_embeddings.py` rerun.

### Coverage stats (latest run)

- Sources in registry: **21**
- Sources scraped successfully: **21**
- Sources failed: **0**
- Raw HTML files: **20**
- Raw PDF files: **4**
- Processed chunks: **4366**

### Retrieval hit-rate sample

Measured on 15 factual/procedural test queries using current Phase 3 retrieval:

- Queries tested: **15**
- Guardrail-blocked: **0**
- Queries returning retrieval chunks: **7**
- Top-k retrieval hit rate (`retrieved_any`): **46.67%**
- Queries above threshold confidence (>= `0.65`): **7** (**46.67%**)

## Notes on remaining constraints

- Some AMC pages are JS-heavy and still produce low text extraction with the current static HTML parser.
- Full Gemini embedding of the entire chunk set can hit free-tier quota (`429 RESOURCE_EXHAUSTED`).
- Local embedding fallback completed full indexing successfully and is the current reliable operational path under quota limits.

## Recommended next improvements

- Add JS-aware fetch for high-value pages (Playwright/requests-html) to improve extraction from script-rendered scheme pages.
- Add retry logic that honors server-provided `RetryInfo` delays for Gemini quota responses.
- Add ingestion controls for PDF volume per source and document prioritization (latest only, by recency/title patterns).
- Add retrieval evaluation set and automated hit-rate regression tracking in CI.
