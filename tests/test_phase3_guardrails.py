"""Intent classification rules."""

from __future__ import annotations

import pytest

from enums import Intent
from guardrails import classify_intent


@pytest.mark.parametrize(
    "query,expected_intent,blocked",
    [
        ("What is the expense ratio of HDFC Flexi Cap Fund?", Intent.FACTUAL, False),
        ("How do I download my capital gains report?", Intent.PROCEDURAL, False),
        ("Should I invest in this ELSS fund?", Intent.ADVISORY, True),
        ("Which fund is better, large cap or flexi cap?", Intent.COMPARISON, True),
        ("My PAN is ABCDE1234F and what is SIP?", Intent.PII_DETECTED, True),
        ("Contact me at user@example.com about NAV", Intent.PII_DETECTED, True),
        ("Call me at 9876543210", Intent.PII_DETECTED, True),
        ("What's the weather in Mumbai?", Intent.OUT_OF_SCOPE, True),
        ("", Intent.OUT_OF_SCOPE, True),
    ],
)
def test_classify_intent(query: str, expected_intent: Intent, blocked: bool) -> None:
    intent, is_blocked = classify_intent(query)
    assert intent == expected_intent
    assert is_blocked is blocked
