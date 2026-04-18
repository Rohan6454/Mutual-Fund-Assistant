"""Intent taxonomy for rule-based guardrails (Phase 3)."""

from __future__ import annotations

from enum import Enum


class Intent(str, Enum):
    FACTUAL = "factual"
    PROCEDURAL = "procedural"
    ADVISORY = "advisory"
    COMPARISON = "comparison"
    PII_DETECTED = "pii_detected"
    OUT_OF_SCOPE = "out_of_scope"
