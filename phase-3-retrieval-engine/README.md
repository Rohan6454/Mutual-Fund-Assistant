# Phase 3 — RAG Retrieval Engine

## Objective

Process user queries, classify intent, perform vector similarity search against Qdrant, re-rank results for relevance and diversity, and assemble context for LLM generation.

## Scope

- Query preprocessing (normalization, abbreviation expansion, scheme name extraction)
- Intent classification (rule-based: FACTUAL, ADVISORY, PII, OUT_OF_SCOPE)
- Vector similarity search against Qdrant (top_k=5, threshold=0.65)
- MMR re-ranking (select top 3 diverse, relevant chunks)
- Context assembly with source attribution tracking

## Key files (this folder)

| File | Purpose |
|------|---------|
| `phase-3-retrieval-engine/retriever.py` | Qdrant search, MMR, `retrieve()` pipeline |
| `phase-3-retrieval-engine/guardrails.py` | Rule-based intent (PII, advisory, comparison, scope, procedural) |
| `phase-3-retrieval-engine/query_processing.py` | Normalize, expand abbreviations, detect scheme (`config/prompts.KNOWN_SCHEMES`) |
| `phase-3-retrieval-engine/mmr.py` | Maximal marginal relevance (numpy) |
| `phase-3-retrieval-engine/schemas.py` | `RetrievedChunk`, `RetrievalResult`, `GuardrailResult` (Pydantic) |
| `phase-3-retrieval-engine/enums.py` | `Intent` enum |

Imports assume `phase-3-retrieval-engine` is on `sys.path` (see `tests/conftest.py`) or run via adding this folder to the path. Phase 2 `embeddings.py` is on the path when using `retriever.py` (for `embed_query`).

### Usage (repository root)

```text
python -c "from pathlib import Path; import sys; sys.path[:0]=[str(Path('phase-3-retrieval-engine')), str(Path('phase-2-document-processing')), '.']; from retriever import retrieve; print(retrieve('What is NAV?'))"
```

Prefer setting `EMBEDDING_MODEL=local` for local dev without Gemini when testing retrieval against Qdrant.

## Intent Classification (Rule-Based)

| Intent | Example | Action |
|--------|---------|--------|
| FACTUAL | "What is the expense ratio?" | Proceed to retrieval |
| PROCEDURAL | "How to download statement?" | Proceed to retrieval |
| ADVISORY | "Should I invest in this fund?" | Refuse |
| COMPARISON | "Which fund is better?" | Refuse |
| PII_DETECTED | "My PAN is ABCDE1234F" | Refuse + warn |
| OUT_OF_SCOPE | "What's the weather?" | Refuse + redirect |

## Search Configuration

| Parameter | Value |
|-----------|-------|
| top_k | 5 |
| score_threshold | 0.65 |
| MMR lambda | 0.7 (70% relevance, 30% diversity) |
| Final chunks | 3 (after MMR) |

## Dependencies

- `qdrant-client` — Vector search
- `numpy` — Cosine similarity for MMR

## Connections

- **Inputs from Phase 2:** Populated Qdrant vector store
- **Outputs to Phase 4:** RetrievalResult (chunks, source URL, date, confidence)
