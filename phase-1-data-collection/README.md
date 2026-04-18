# Phase 1 — Data Collection & Corpus Preparation

## Objective

Collect official public HTML and PDF content from the Phase 1 URL registry (`data/sources.json`) to form the knowledge corpus for the RAG system. Sources cover Groww help (user flows), AMC scheme pages, AMC factsheet index pages, and AMFI/SEBI regulatory material for factual answers and polite refusals.

## Phase 1 scope (URL batches)

All targets are listed in `data/sources.json` with `batch` metadata. The scraping service reads that file and fetches each `url`.

### Batch 1: Groww Help (User Flows)

| URL |
|-----|
| https://groww.in/help |
| https://groww.in/help/mutual-funds |
| https://groww.in/help/mutual-funds/how-to-download-capital-gains-report |
| https://groww.in/help/mutual-funds/how-to-download-account-statement |

### Batch 2: Scheme Pages (Core Data)

| AMC | URL |
|-----|-----|
| ICICI Prudential | https://www.icicipruamc.com/mutual-fund/icici-prudential-bluechip-fund |
| ICICI Prudential | https://www.icicipruamc.com/mutual-fund/icici-prudential-flexicap-fund |
| ICICI Prudential | https://www.icicipruamc.com/mutual-fund/icici-prudential-value-discovery-fund |
| HDFC Mutual Fund | https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund |
| HDFC Mutual Fund | https://www.hdfcfund.com/explore/mutual-funds/hdfc-large-cap-fund |
| HDFC Mutual Fund | https://www.hdfcfund.com/explore/mutual-funds/hdfc-mid-cap-opportunities-fund |
| HDFC Mutual Fund | https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund |
| Nippon India MF | https://www.nipponindiamf.com/funds-and-performance/equity-funds/nippon-india-large-cap-fund |
| Nippon India MF | https://www.nipponindiamf.com/funds-and-performance/equity-funds/nippon-india-small-cap-fund |
| Nippon India MF | https://www.nipponindiamf.com/funds-and-performance/equity-funds/nippon-india-growth-fund |
| Nippon India MF | https://www.nipponindiamf.com/funds-and-performance/solution-oriented-funds/nippon-india-tax-saver-elss-fund |

### Batch 3: Factsheets (index / download listing pages)

| AMC | URL |
|-----|-----|
| ICICI Prudential | https://www.icicipruamc.com/downloads/factsheets |
| HDFC Mutual Fund | https://www.hdfcfund.com/statutory-disclosure/factsheets |
| Nippon India MF | https://www.nipponindiamf.com/downloads/factsheets |

### Batch 4: Regulatory (refusals + education)

| URL |
|-----|
| https://www.amfiindia.com/investor-corner |
| https://www.amfiindia.com/investor-corner/knowledge-center |
| https://www.sebi.gov.in/sebi_data/faqfiles/mutual_funds.html |

## Assistant rules (downstream)

The FAQ assistant is facts-only: answer only factual, verifiable queries; maximum 3 sentences; exactly one source link per answer; no investment advice; for advisory queries, refuse politely and provide a single AMFI or SEBI link (see `config/prompts.py`).

## Scope (implementation)

- Treat `data/sources.json` as the single source of truth for Phase 1 URLs
- Build a web scraping pipeline to download HTML pages and linked PDFs where applicable
- Store raw files with metadata sidecars for traceability
- Implement polite scraping (rate limiting, User-Agent headers)

## Key files (this folder)

| File | Purpose |
|------|---------|
| `phase-1-data-collection/scrape_sources.py` | Fetches every URL in `data/sources.json`; writes `data/raw/` + sidecars; updates registry |
| `phase-1-data-collection/scheduler_service.py` | Local **APScheduler** cron (see `.env` `SCHEDULER_*`) → runs scrape → Phase 2 chunk → embed |

## Scheduler options

| Mechanism | Location / command |
|-----------|-------------------|
| **GitHub Actions** | `.github/workflows/daily-ingest.yml` — UTC cron + manual `workflow_dispatch` |
| **Local daemon** | From repo root: `python phase-1-data-collection/scheduler_service.py` |
| **One-shot pipeline** | `python phase-1-data-collection/scheduler_service.py --run-now` |

## Outputs

- `data/raw/html/` — Downloaded HTML files + `.meta.json` sidecars
- `data/raw/pdf/` — Downloaded PDF files + `.meta.json` sidecars
- Updated `data/sources.json` with scrape timestamps and status

## Dependencies

- `requests` — HTTP fetching
- `beautifulsoup4` — HTML validation
- `pathlib`, `json`, `time`, `datetime` — Stdlib

## Connections

- **Inputs:** URLs in `data/sources.json` (batches above)
- **Outputs to Phase 2:** Raw HTML and PDF files in `data/raw/`
- **Operations:** GitHub Actions or `scheduler_service.py` runs scrape then Phase 2 (see `docs/RAG-Architecture.md`, `docs/Chunking-Embedding-GitHub-Actions-Architecture.md`)
