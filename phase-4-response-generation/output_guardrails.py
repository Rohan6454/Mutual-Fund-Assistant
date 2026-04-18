"""Phase 4 output guardrails and formatting helpers."""

from __future__ import annotations

import re

from config.prompts import (
    EDUCATIONAL_LINKS,
    OUT_OF_SCOPE_TEMPLATE,
    PII_WARNING_TEMPLATE,
    REFUSAL_TEMPLATE,
)
from enums import Intent

_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
_PII_RE = re.compile(
    r"(?:\b[A-Z]{5}[0-9]{4}[A-Z]\b)|"
    r"(?:\b\d{4}\s?\d{4}\s?\d{4}\b)|"
    r"(?:\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b)|"
    r"(?:\b(?:\+91[\-\s]?)?[6-9]\d{9}\b)",
    re.IGNORECASE,
)
_ADVICE_RE = re.compile(
    r"\b(?:buy|sell|hold|invest|recommend|suggest|best fund|better fund)\b",
    re.IGNORECASE,
)


def limit_sentences(text: str, max_sentences: int) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    parts = [p.strip() for p in parts if p.strip()]
    return " ".join(parts[:max_sentences]).strip()


def remove_extra_urls(text: str, *, keep: str | None = None) -> str:
    urls = list(_URL_RE.finditer(text))
    if not urls:
        return text
    out = text
    for m in reversed(urls):
        u = m.group(0)
        if keep and u == keep:
            continue
        out = out[: m.start()] + out[m.end() :]
    return re.sub(r"\s{2,}", " ", out).strip()


def output_has_violations(answer: str) -> bool:
    return bool(_PII_RE.search(answer) or _ADVICE_RE.search(answer))


def refusal_for_intent(intent: Intent) -> str:
    if intent in (Intent.ADVISORY, Intent.COMPARISON):
        return REFUSAL_TEMPLATE.format(educational_link=EDUCATIONAL_LINKS["general"])
    if intent == Intent.PII_DETECTED:
        return PII_WARNING_TEMPLATE
    if intent == Intent.OUT_OF_SCOPE:
        return OUT_OF_SCOPE_TEMPLATE
    return OUT_OF_SCOPE_TEMPLATE

