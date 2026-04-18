"""Embedding backends: Gemini (google.genai) primary or local MiniLM fallback."""

from __future__ import annotations

import logging
import re
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.settings import settings

logger = logging.getLogger(__name__)

_LOCAL_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_local_model: SentenceTransformer | None = None


class EmbeddingQuotaExceededError(RuntimeError):
    """Raised when Gemini embedding quota/rate limits prevent progress."""

    def __init__(self, message: str, retry_after_seconds: int | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


def embedding_dimension(mode: Literal["gemini", "local"] | None = None) -> int:
    m = mode or settings.EMBEDDING_MODEL
    return settings.GEMINI_EMBEDDING_DIMENSION if m == "gemini" else 384


def _get_local_model() -> SentenceTransformer:
    from sentence_transformers import SentenceTransformer

    global _local_model
    if _local_model is None:
        _local_model = SentenceTransformer(_LOCAL_MODEL_NAME)
    return _local_model


def embed_texts(texts: list[str], *, is_query: bool = False) -> list[list[float]]:
    """Batch-embed strings; order is preserved."""
    if not texts:
        return []
    mode = settings.EMBEDDING_MODEL
    if mode == "gemini":
        return _embed_gemini_batch(texts, is_query=is_query)
    return _embed_local_batch(texts)


def embed_query(text: str) -> list[float]:
    return embed_texts([text], is_query=True)[0]


def _embed_gemini_batch(texts: list[str], *, is_query: bool) -> list[list[float]]:
    from google import genai
    from google.genai import types

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is required for gemini embeddings")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    task = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
    non_empty = [t for t in texts if t.strip()]
    if not non_empty:
        return [[0.0] * settings.GEMINI_EMBEDDING_DIMENSION for _ in texts]

    response = None
    for attempt in range(5):
        try:
            response = client.models.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                contents=non_empty,
                config=types.EmbedContentConfig(
                    task_type=task,
                    output_dimensionality=settings.GEMINI_EMBEDDING_DIMENSION,
                ),
            )
            break
        except Exception as e:
            wait = 2**attempt
            logger.warning("Gemini batch embed attempt %s failed: %s; sleeping %ss", attempt + 1, e, wait)
            msg = str(e)
            if "RESOURCE_EXHAUSTED" in msg or "429" in msg or "quota" in msg.lower():
                retry_match = re.search(r"retry in ([0-9]+(?:\.[0-9]+)?)s", msg, flags=re.IGNORECASE)
                retry_secs = int(float(retry_match.group(1))) if retry_match else None
                if attempt >= 1:
                    raise EmbeddingQuotaExceededError(msg, retry_after_seconds=retry_secs) from e
            time.sleep(wait)
    if response is None:
        raise RuntimeError("Gemini batch embedding failed after retries")

    embedded_values = []
    for emb in getattr(response, "embeddings", []) or []:
        embedded_values.append(list(emb.values))
    if len(embedded_values) != len(non_empty):
        raise RuntimeError(
            f"Gemini returned {len(embedded_values)} embeddings for {len(non_empty)} inputs"
        )

    out: list[list[float]] = []
    j = 0
    for t in texts:
        if not t.strip():
            out.append([0.0] * settings.GEMINI_EMBEDDING_DIMENSION)
        else:
            out.append(embedded_values[j])
            j += 1
    return out


def _embed_local_batch(texts: list[str]) -> list[list[float]]:
    model = _get_local_model()
    vectors = model.encode(
        texts,
        batch_size=min(32, len(texts) or 1),
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vectors]
