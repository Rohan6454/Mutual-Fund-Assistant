# Phase 2 — Document Processing & Embedding Pipeline

## Objective

Extract text from raw HTML/PDF files, clean and normalize it, split into semantically meaningful chunks, generate vector embeddings, and ingest into Qdrant.

## Scope

- Text extraction from HTML (BeautifulSoup) and PDF (PyMuPDF + pdfplumber)
- Text cleaning and normalization (Unicode, financial terms, boilerplate removal)
- Section-aware chunking (500 chars, 75 overlap)
- Embedding generation (Gemini primary, MiniLM fallback)
- Qdrant collection setup and vector ingestion

## Key files (this folder)

| File | Purpose |
|------|---------|
| `phase-2-document-processing/process_documents.py` | HTML/PDF → clean text → chunks → `data/processed/chunks/*.json` |
| `phase-2-document-processing/generate_embeddings.py` | Chunk JSON → embeddings → Qdrant upsert (uses `config/settings.py`) |
| `phase-2-document-processing/embeddings.py` | `embed_texts` / `embed_query` — Gemini **text-embedding-004** or local MiniLM |
| `phase-2-document-processing/text_processing.py` | Normalization, whitespace, light boilerplate stripping |

Run from repository root:

```text
python phase-2-document-processing/process_documents.py
python phase-2-document-processing/generate_embeddings.py
```

## Chunking Configuration

| Parameter | Value |
|-----------|-------|
| `chunk_size` | 500 characters |
| `chunk_overlap` | 75 characters |
| `separators` | `["\n\n", "\n", ". ", " "]` |

## Qdrant Collection

| Setting | Value |
|---------|-------|
| Collection | `mutual_fund_faq` |
| Vector size | 768 (Gemini) or 384 (MiniLM) |
| Distance | Cosine |
| Payload indexes | `scheme_name`, `doc_type`, `section` |

## Outputs

- `data/processed/chunks/` — JSON files per chunk with text + metadata
- Qdrant collection populated with embeddings + payloads

## Dependencies

- `beautifulsoup4`, `PyMuPDF`, `pdfplumber` — Document parsing
- `langchain-text-splitters` — Chunking
- `google-generativeai` — Gemini embeddings
- `sentence-transformers` — Local fallback embeddings
- `qdrant-client` — Qdrant SDK

## Connections

- **Inputs from Phase 1:** Raw files in `data/raw/`
- **Outputs to Phase 3:** Populated Qdrant vector store
