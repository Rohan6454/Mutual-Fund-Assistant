"""Query normalization and scheme detection."""

from __future__ import annotations

import pytest

from query_processing import (
    build_enhanced_query,
    detect_scheme_name,
    expand_abbreviations,
    normalize_query,
)


def test_normalize_query() -> None:
    assert normalize_query("  Hello   World  ") == "hello world"


def test_expand_er() -> None:
    n = normalize_query("What is the ER for this fund?")
    assert "expense ratio" in expand_abbreviations(n)


def test_detect_scheme_hdfc_flexi() -> None:
    q = normalize_query("expense ratio hdfc flexi cap fund")
    q = expand_abbreviations(q)
    assert detect_scheme_name(q) == "HDFC Flexi Cap Fund"


def test_detect_scheme_icici_bluechip() -> None:
    q = normalize_query("icici prudential bluechip nav")
    assert detect_scheme_name(q) == "ICICI Prudential Bluechip Fund"


def test_build_enhanced_query() -> None:
    n = normalize_query("expense ratio")
    e = expand_abbreviations(n)
    s = detect_scheme_name(e)
    assert "expense ratio" in build_enhanced_query(e, s).lower()
