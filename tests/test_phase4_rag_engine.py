from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

from enums import Intent
from schemas import GuardrailResult, RetrievalResult

_RAG_PATH = Path(__file__).resolve().parents[1] / "phase-4-response-generation" / "rag_engine.py"
_spec = importlib.util.spec_from_file_location("phase4_rag_engine", _RAG_PATH)
assert _spec and _spec.loader
rag_engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rag_engine)


def test_answer_query_blocked() -> None:
    with patch.object(rag_engine, "retrieve", return_value=(GuardrailResult(intent=Intent.ADVISORY, blocked=True), None)):
        out = rag_engine.answer_query("should i invest")
    assert out["blocked"] is True
    assert out["intent"] == "advisory"


def test_answer_query_no_info() -> None:
    rr = RetrievalResult(chunks=[], confidence=0.2)
    with patch.object(rag_engine, "retrieve", return_value=(GuardrailResult(intent=Intent.FACTUAL, blocked=False), rr)):
        out = rag_engine.answer_query("what is nav")
    assert out["blocked"] is False
    assert "I don't have reliable information" in out["answer"]

