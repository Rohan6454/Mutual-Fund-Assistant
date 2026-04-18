"""
Vector search (Qdrant), MMR re-ranking, and retrieval orchestration.
Run with repo root as cwd or ensure config/.env is discoverable via python-dotenv.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

_PHASE3 = Path(__file__).resolve().parent
REPO_ROOT = _PHASE3.parent
_PHASE2 = REPO_ROOT / "phase-2-document-processing"

for _p in (str(REPO_ROOT), str(_PHASE3), str(_PHASE2)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from config.settings import settings

import embeddings as emb_module
from enums import Intent
import importlib.util
import sys
from pathlib import Path

# Import classify_intent from the correct location (phase-3 guardrails)
def _get_classify_intent():
    """Import classify_intent from the correct guardrails module."""
    current_dir = Path(__file__).resolve().parent
    guardrails_path = current_dir / "guardrails.py"
    spec = importlib.util.spec_from_file_location("phase3_guardrails", guardrails_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load phase-3 guardrails from {guardrails_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.classify_intent

classify_intent = _get_classify_intent()

from mmr import maximal_marginal_relevance
from query_processing import (
    build_enhanced_query,
    detect_scheme_name,
    expand_abbreviations,
    normalize_query,
)
from schemas import GuardrailResult, RetrievedChunk, RetrievalResult

logger = logging.getLogger(__name__)


def _qdrant_client() -> QdrantClient:
    if settings.QDRANT_URL:
        return QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
        )
    return QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        api_key=settings.QDRANT_API_KEY or None,
    )


def search_qdrant(
    query_vector: list[float],
    *,
    scheme_filter: str | None,
    top_k: int,
    score_threshold: float,
) -> list[dict]:
    """
    Returns list of dicts: id, score, payload, vector (list[float]).
    """
    client = _qdrant_client()
    fl = None
    if scheme_filter:
        fl = Filter(
            must=[
                FieldCondition(
                    key="scheme_name",
                    match=MatchValue(value=scheme_filter),
                )
            ]
        )

    response = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        limit=top_k,
        score_threshold=score_threshold,
        query_filter=fl,
        with_payload=True,
        with_vectors=True,
    )

    # qdrant-client versions return either QueryResponse(points=[...]) or list-like result payloads.
    hits = getattr(response, "points", None)
    if hits is None:
        hits = getattr(response, "result", None)
    if hits is None:
        hits = response if isinstance(response, list) else []

    out: list[dict] = []
    for h in hits:
        vec = h.vector
        if isinstance(vec, dict):
            vec = next(iter(vec.values()), None)
        if vec is None:
            logger.warning("Hit %s missing vector; skipping for MMR", h.id)
            continue
        if hasattr(vec, "tolist"):
            vec = vec.tolist()
        out.append(
            {
                "id": str(h.id),
                "score": float(h.score),
                "payload": dict(h.payload or {}),
                "vector": list(vec),
            }
        )
    return out


def vector_search_and_rerank(
    raw_query: str,
    *,
    query_vector: list[float] | None = None,
) -> RetrievalResult:
    """
    Embed query (unless vector provided), search Qdrant, apply MMR, assemble RetrievalResult.
    Does not run guardrails — call `retrieve` for full pipeline.
    """
    normalized = normalize_query(raw_query)
    expanded = expand_abbreviations(normalized)
    scheme = detect_scheme_name(expanded)
    enhanced = build_enhanced_query(expanded, scheme)

    qvec = query_vector if query_vector is not None else emb_module.embed_query(enhanced)

    hits = search_qdrant(
        qvec,
        scheme_filter=scheme,
        top_k=settings.RETRIEVAL_TOP_K,
        score_threshold=settings.RETRIEVAL_THRESHOLD,
    )

    # Fallback: if no hits with scheme filter, search without filter
    if not hits and scheme:
        hits = search_qdrant(
            qvec,
            scheme_filter=None,
            top_k=settings.RETRIEVAL_TOP_K,
            score_threshold=settings.RETRIEVAL_THRESHOLD,
        )

    if not hits:
        return RetrievalResult(
            chunks=[],
            confidence=0.0,
            scheme_filter_applied=scheme,
            enhanced_query=enhanced,
        )

    embeddings = [h["vector"] for h in hits]
    scores = [h["score"] for h in hits]
    order = maximal_marginal_relevance(
        embeddings,
        scores,
        lambda_mult=settings.MMR_LAMBDA,
        k=min(settings.RERANK_TOP_N, len(hits)),
    )

    chunks: list[RetrievedChunk] = []
    for idx in order:
        h = hits[idx]
        pl = h["payload"]
        text = pl.get("text", "")
        meta = {k: v for k, v in pl.items() if k != "text"}
        chunks.append(
            RetrievedChunk(
                text=text,
                score=h["score"],
                metadata=meta,
            )
        )

    conf = float(np.mean([c.score for c in chunks])) if chunks else 0.0
    primary = max(chunks, key=lambda c: c.score)
    pmeta = primary.metadata
    return RetrievalResult(
        chunks=chunks,
        primary_source_url=str(pmeta.get("source_url", "")),
        primary_source_date=pmeta.get("last_updated"),
        confidence=conf,
        scheme_filter_applied=scheme,
        enhanced_query=enhanced,
    )


def retrieve(raw_query: str) -> tuple[GuardrailResult, RetrievalResult | None]:
    """
    Full Phase 3 pipeline: guardrails → embed → search → MMR.

    Returns (GuardrailResult, RetrievalResult or None).
    When guardrails block, RetrievalResult is None.
    When not blocked, RetrievalResult is always returned (possibly empty chunks).
    """
    intent, blocked = classify_intent(raw_query)
    gr = GuardrailResult(intent=intent, blocked=blocked)
    if blocked:
        return gr, None
    try:
        result = vector_search_and_rerank(raw_query)
    except Exception:
        logger.exception("Retrieval failed")
        raise
    return gr, result
