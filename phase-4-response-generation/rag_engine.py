"""Phase 4 orchestration: guardrails + retrieval + generation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE4 = Path(__file__).resolve().parent
PHASE3 = REPO_ROOT / "phase-3-retrieval-engine"
for _p in (str(PHASE4), str(REPO_ROOT), str(PHASE3)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from config.prompts import NO_INFO_TEMPLATE
from config.settings import settings
from output_guardrails import refusal_for_intent
from generator import generate_response
from retriever import retrieve


def answer_query(user_query: str) -> dict[str, Any]:
    """
    Returns:
      {
        "answer": str,
        "intent": str,
        "blocked": bool,
        "source_url": str | None,
        "confidence": float | None
      }
    """
    guardrail_result, retrieval = retrieve(user_query)
    intent = guardrail_result.intent.value

    if guardrail_result.blocked:
        return {
            "answer": refusal_for_intent(guardrail_result.intent),
            "intent": intent,
            "blocked": True,
            "source_url": None,
            "confidence": None,
        }

    if retrieval is None or not retrieval.chunks or retrieval.confidence < settings.RETRIEVAL_THRESHOLD:
        return {
            "answer": NO_INFO_TEMPLATE,
            "intent": intent,
            "blocked": False,
            "source_url": retrieval.primary_source_url if retrieval else None,
            "confidence": retrieval.confidence if retrieval else 0.0,
        }

    response_text = generate_response(user_query, retrieval)
    return {
        "answer": response_text,
        "intent": intent,
        "blocked": False,
        "source_url": retrieval.primary_source_url,
        "confidence": retrieval.confidence,
    }

