from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from routers import chat, health, threads

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Mutual Fund FAQ Backend API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = chat.limiter
app.add_middleware(SlowAPIMiddleware)

app.include_router(chat.router, prefix="/api")
app.include_router(threads.router, prefix="/api")
app.include_router(health.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Preload models on startup to prevent timeout issues."""
    try:
        from services.rag_service import _preload_models
        _preload_models()
        logger.info("Backend startup completed - models preloaded")
    except Exception as e:
        logger.error(f"Failed to preload models during startup: {e}")
        # Continue startup even if preloading fails


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
