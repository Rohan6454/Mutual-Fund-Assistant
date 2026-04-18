from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_embedding_checkpoint_on_quota(tmp_path, monkeypatch) -> None:
    root = Path(__file__).resolve().parents[1]
    emb_mod = _load_module(root / "phase-2-document-processing" / "embeddings.py", "p2_emb")
    gen_mod = _load_module(root / "phase-2-document-processing" / "generate_embeddings.py", "p2_gen")

    class _DummyClient:
        def upsert(self, *args, **kwargs):
            return None

    monkeypatch.setattr(gen_mod, "_qdrant_client", lambda: _DummyClient())
    monkeypatch.setattr(gen_mod, "_ensure_collection", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        gen_mod,
        "_load_chunks",
        lambda: [{"chunk_id": "1", "text": "abc", "metadata": {"source_url": "x"}}],
    )

    def _raise_quota(*args, **kwargs):
        raise emb_mod.EmbeddingQuotaExceededError("quota exceeded", retry_after_seconds=15)

    monkeypatch.setattr(gen_mod.emb, "embed_texts", _raise_quota)

    cp = tmp_path / "resume_checkpoint.json"
    monkeypatch.setattr(gen_mod, "CHECKPOINT_FILE", cp)
    gen_mod.main()

    assert cp.is_file()
    data = json.loads(cp.read_text(encoding="utf-8"))
    assert data["reason"] == "quota_exceeded"
    assert data["next_index"] == 0
