"""Rule-based intent classification (no LLM). Layer order: PII → advisory → comparison → scope → procedural → factual."""

from __future__ import annotations

import re

from enums import Intent

_PAN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
_AADHAAR = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_IN = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b")

_ADVISORY = re.compile(
    r"(?:should\s+i\s+(?:invest|buy|sell|redeem|switch))|"
    r"(?:recommend|suggestion|suggest).{0,40}fund|"
    r"(?:best|top|worst).{0,20}fund|"
    r"(?:good|bad)\s+(?:investment|fund|scheme)|"
    r"will\s+(?:it|this|the\s+fund)\s+(?:give|generate|earn).{0,30}return",
    re.IGNORECASE | re.DOTALL,
)

_COMPARISON = re.compile(
    r"\b(?:compare|vs\.?|versus|better\s+than|which\s+fund|which\s+is\s+better)\b",
    re.IGNORECASE,
)

_OUT_OF_SCOPE = re.compile(
    r"\b(?:weather|cricket|football|movie|recipe|bitcoin\s+price|stock\s+tip|"
    r"who\s+won|election\s+result)\b",
    re.IGNORECASE,
)

_PROCEDURAL = re.compile(
    r"^(?:how\s+(?:do\s+i|to|can\s+i)|where\s+(?:do\s+i|can\s+i)|steps?\s+to)\b",
    re.IGNORECASE,
)


def classify_intent(raw_query: str) -> tuple[Intent, bool]:
    """
    Returns (intent, blocked).
    blocked=True means do not call retrieval / generation with normal flow.
    """
    q = raw_query.strip()
    if not q:
        return Intent.OUT_OF_SCOPE, True

    if _PAN.search(q) or _AADHAAR.search(q) or _EMAIL.search(q) or _PHONE_IN.search(q):
        return Intent.PII_DETECTED, True

    if _ADVISORY.search(q):
        return Intent.ADVISORY, True

    if _COMPARISON.search(q):
        return Intent.COMPARISON, True

    if _OUT_OF_SCOPE.search(q):
        return Intent.OUT_OF_SCOPE, True

    n = q.lower()
    if _PROCEDURAL.search(n):
        return Intent.PROCEDURAL, False

    return Intent.FACTUAL, False
