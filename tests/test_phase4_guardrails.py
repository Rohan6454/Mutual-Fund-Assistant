from __future__ import annotations

import importlib.util
from pathlib import Path

from enums import Intent

_PHASE4_GUARDRAILS = (
    Path(__file__).resolve().parents[1] / "phase-4-response-generation" / "output_guardrails.py"
)
_spec = importlib.util.spec_from_file_location("phase4_guardrails", _PHASE4_GUARDRAILS)
assert _spec and _spec.loader
guardrails = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guardrails)


def test_limit_sentences() -> None:
    text = "A. B. C. D."
    assert guardrails.limit_sentences(text, 3) == "A. B. C."


def test_remove_extra_urls() -> None:
    text = "Answer https://a.com and https://b.com"
    out = guardrails.remove_extra_urls(text, keep="https://b.com")
    assert "https://a.com" not in out
    assert "https://b.com" in out


def test_refusal_for_advisory() -> None:
    out = guardrails.refusal_for_intent(Intent.ADVISORY)
    assert "cannot offer investment advice" in out

