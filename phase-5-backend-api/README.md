# Phase 5 — Backend API (FastAPI)

## Objective

Expose the RAG engine as a RESTful API with multi-thread chat session management, rate limiting, error handling, and health monitoring.

## Scope

- FastAPI application setup with CORS and middleware
- REST endpoints for chat, threads, and health
- Pydantic v2 request/response schemas
- In-memory multi-thread chat session manager
- Rate limiting (10 req/min per IP)
- Structured JSON logging
- Custom exception handling with Gemini retry logic

## Key Files to Implement

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app init, middleware, exception handlers |
| `app/routers/chat.py` | `POST /api/chat` |
| `app/routers/threads.py` | Thread CRUD endpoints |
| `app/routers/health.py` | Health check endpoint |
| `app/models/schemas.py` | Pydantic v2 models |
| `app/models/enums.py` | Enum definitions |
| `app/services/thread_manager.py` | In-memory thread state |
| `config/settings.py` | Central configuration |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Send message, get response |
| GET | `/api/threads` | List thread summaries |
| POST | `/api/threads` | Create new thread |
| GET | `/api/threads/{thread_id}` | Get thread history |
| DELETE | `/api/threads/{thread_id}` | Delete thread |
| GET | `/api/health` | System health check |

## Thread Manager

- In-memory `dict[str, ThreadState]`
- Max 50 threads (LRU eviction)
- Max 100 messages per thread
- Auto-title from first user message

## Dependencies

- `fastapi`, `uvicorn` — Web framework + server
- `pydantic` v2 — Validation
- `slowapi` — Rate limiting
- `python-dotenv` — Env vars

## Connections

- **Inputs from Phase 4:** RAG engine (rag_engine.py, generator.py, guardrails.py)
- **Outputs to Phase 6:** REST API consumed by Streamlit frontend
