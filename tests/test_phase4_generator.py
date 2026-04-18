from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

from schemas import RetrievedChunk, RetrievalResult

_GEN_PATH = Path(__file__).resolve().parents[1] / "phase-4-response-generation" / "generator.py"
_spec = importlib.util.spec_from_file_location("phase4_generator", _GEN_PATH)
assert _spec and _spec.loader
generator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generator)


def _sample_retrieval() -> RetrievalResult:
    return RetrievalResult(
        chunks=[
            RetrievedChunk(text="Expense ratio is 1.23%.", score=0.91, metadata={}),
            RetrievedChunk(text="Direct plan available.", score=0.86, metadata={}),
        ],
        primary_source_url="https://example.com/source",
        primary_source_date="2026-04-14",
        confidence=0.88,
    )


def test_generate_response_formats_with_source() -> None:
    rr = _sample_retrieval()
    with patch.object(generator, "_call_gemini", return_value="Expense ratio is 1.23%. Direct plan is available."):
        out = generator.generate_response("expense ratio?", rr)
    assert "Source: https://example.com/source" in out
    assert "Last updated from sources: 2026-04-14" in out


def test_generate_response_no_chunks() -> None:
    rr = RetrievalResult(chunks=[], confidence=0.0)
    out = generator.generate_response("x", rr)
    assert "I don't have reliable information" in out

