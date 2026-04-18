"""
Read chunk JSON files, embed with configured model, upsert into Qdrant.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, PayloadSchemaType, VectorParams

_PHASE2 = Path(__file__).resolve().parent
REPO_ROOT = _PHASE2.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(_PHASE2))

from config.settings import settings

import embeddings as emb
from embeddings import EmbeddingQuotaExceededError

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CHUNKS_DIR = REPO_ROOT / "data" / "processed" / "chunks"
CHECKPOINT_FILE = REPO_ROOT / "data" / "processed" / "metadata" / "embedding_resume_checkpoint.json"


def _qdrant_client() -> QdrantClient:
    if settings.QDRANT_URL:
        return QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
            timeout=120,
        )
    return QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        api_key=settings.QDRANT_API_KEY or None,
        timeout=120,
    )


def _ensure_collection(client: QdrantClient, name: str, dim: int) -> None:
    names = {c.name for c in client.get_collections().collections}
    if name in names:
        return

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    for field in ("scheme_name", "doc_type", "section"):
        try:
            client.create_payload_index(
                collection_name=name,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
            )
        except Exception as e:
            logger.debug("payload index %s: %s", field, e)


def _load_chunks() -> list[dict]:
    records: list[dict] = []
    for path in sorted(CHUNKS_DIR.glob("*.json")):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception as e:
            logger.warning("Skip invalid chunk file %s: %s", path, e)
    return records


def _load_checkpoint() -> dict | None:
    if not CHECKPOINT_FILE.is_file():
        return None
    return json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))


def _save_checkpoint(next_index: int, total: int, *, reason: str, retry_after_seconds: int | None = None, message: str | None = None) -> None:
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "next_index": next_index,
        "total_chunks": total,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "retry_after_seconds": retry_after_seconds,
        "message": message,
    }
    CHECKPOINT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _clear_checkpoint() -> None:
    CHECKPOINT_FILE.unlink(missing_ok=True)


def _point_id(chunk_id: str) -> str | uuid.UUID:
    try:
        return uuid.UUID(chunk_id)
    except ValueError:
        return chunk_id


def main() -> None:
    dim = emb.embedding_dimension()
    client = _qdrant_client()
    col = settings.QDRANT_COLLECTION
    _ensure_collection(client, col, dim)

    chunks = _load_chunks()
    if not chunks:
        logger.warning("No chunk JSON files in %s — run process_documents.py first", CHUNKS_DIR)
        return

    batch_size = max(1, settings.EMBEDDING_BATCH_SIZE)
    checkpoint = _load_checkpoint()
    start_index = 0
    if checkpoint:
        cp_total = int(checkpoint.get("total_chunks", 0))
        cp_next = int(checkpoint.get("next_index", 0))
        if cp_total == len(chunks) and 0 <= cp_next < len(chunks):
            start_index = cp_next
            logger.info("Resuming embedding from checkpoint at index %s / %s", start_index, len(chunks))
        else:
            logger.info("Checkpoint ignored (chunk set changed), starting from beginning.")

    total = 0
    for i in range(start_index, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c.get("text") or "" for c in batch]
        valid_pairs: list[tuple[dict, str]] = [(c, t) for c, t in zip(batch, texts) if t.strip()]
        if not valid_pairs:
            continue
        c_list, t_list = zip(*valid_pairs)
        try:
            vectors = emb.embed_texts(list(t_list), is_query=False)
        except Exception as e:
            is_quota = isinstance(e, EmbeddingQuotaExceededError) or hasattr(e, "retry_after_seconds")
            msg = str(e).lower()
            if not is_quota and ("resource_exhausted" in msg or "quota" in msg or "429" in msg):
                is_quota = True
            if is_quota:
                retry_after = getattr(e, "retry_after_seconds", None)
                _save_checkpoint(
                    next_index=i,
                    total=len(chunks),
                    reason="quota_exceeded",
                    retry_after_seconds=retry_after,
                    message=str(e),
                )
                logger.error(
                    "Embedding paused due to quota limits at batch starting %s / %s. "
                    "Checkpoint saved to %s. Retry after ~%ss.",
                    i,
                    len(chunks),
                    CHECKPOINT_FILE,
                    retry_after if retry_after is not None else "unknown",
                )
                return
            raise
        points = []
        for rec, vec in zip(c_list, vectors):
            cid = rec["chunk_id"]
            meta = dict(rec.get("metadata") or {})
            payload = {"text": rec.get("text", ""), **meta}
            points.append(
                PointStruct(
                    id=_point_id(cid),
                    vector=vec,
                    payload=payload,
                )
            )
        client.upsert(collection_name=col, points=points)
        total += len(points)
        logger.info("Upserted %s points (batch ending %s / %s)", len(points), min(i + batch_size, len(chunks)), len(chunks))
        _save_checkpoint(
            next_index=min(i + batch_size, len(chunks)),
            total=len(chunks),
            reason="in_progress",
        )

    logger.info("Done. Total upserted: %s into %r", total, col)
    _clear_checkpoint()


if __name__ == "__main__":
    main()
