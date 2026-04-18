"""Phase 4 LLM generation + response formatting."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE4 = Path(__file__).resolve().parent
PHASE3 = REPO_ROOT / "phase-3-retrieval-engine"
for _p in (str(PHASE4), str(REPO_ROOT), str(PHASE3)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from config.prompts import CONTEXT_INJECTION_TEMPLATE, NO_INFO_TEMPLATE, SYSTEM_PROMPT
from config.settings import settings
from output_guardrails import limit_sentences, output_has_violations, remove_extra_urls
from schemas import RetrievalResult


def _build_context_prompt(user_query: str, retrieval: RetrievalResult) -> str:
    chunks = [c.text for c in retrieval.chunks[:3]]
    while len(chunks) < 3:
        chunks.append("")
    return CONTEXT_INJECTION_TEMPLATE.format(
        chunk_1=chunks[0],
        chunk_2=chunks[1],
        chunk_3=chunks[2],
        user_query=user_query,
    )


def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL, system_instruction=system_prompt)
    response = model.generate_content(
        user_prompt
    )
    text = (response.text or "").strip()
    return text


def _format_final(answer: str, source_url: str, source_date: str | None) -> str:
    return answer.strip()


def generate_response(user_query: str, retrieval: RetrievalResult) -> str:
    """
    Generate factual response from retrieved chunks.
    Returns formatted output with citation/footer.
    """
    if not retrieval.chunks:
        return NO_INFO_TEMPLATE

    prompt = _build_context_prompt(user_query, retrieval)
    raw = _call_gemini(SYSTEM_PROMPT, prompt)
    if not raw:
        return NO_INFO_TEMPLATE

    answer = limit_sentences(raw, settings.MAX_RESPONSE_SENTENCES)
    answer = remove_extra_urls(answer)
    if output_has_violations(answer):
        return NO_INFO_TEMPLATE

    return _format_final(answer, retrieval.primary_source_url, retrieval.primary_source_date)

