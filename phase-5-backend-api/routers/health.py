from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from qdrant_client import QdrantClient

from models.schemas import HealthResponse
from config.settings import settings

router = APIRouter(tags=["health"])


def _qdrant_client() -> QdrantClient:
    if settings.QDRANT_URL:
        return QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY or None)
    return QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, api_key=settings.QDRANT_API_KEY or None)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    qdrant_state = "ok"
    status = "ok"
    try:
        _qdrant_client().get_collections()
    except Exception:
        qdrant_state = "degraded"
        status = "degraded"
    return HealthResponse(status=status, qdrant=qdrant_state, timestamp=datetime.now(timezone.utc))
