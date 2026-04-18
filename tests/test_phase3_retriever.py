"""Retriever orchestration with mocked Qdrant (no live DB)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from enums import Intent
from retriever import retrieve, vector_search_and_rerank


def test_retrieve_blocks_advisory() -> None:
    gr, res = retrieve("Should I buy HDFC Flexi Cap Fund?")
    assert gr.blocked is True
    assert gr.intent == Intent.ADVISORY
    assert res is None


def test_vector_search_and_rerank_mocked() -> None:
    fake_hits = [
        {
            "id": "1",
            "score": 0.9,
            "payload": {
                "text": "alpha chunk",
                "source_url": "https://example.com/a",
                "last_updated": "2026-04-01",
                "scheme_name": "HDFC Flexi Cap Fund",
            },
            "vector": [1.0, 0.0, 0.0],
        },
        {
            "id": "2",
            "score": 0.88,
            "payload": {
                "text": "beta chunk",
                "source_url": "https://example.com/b",
                "last_updated": "2026-04-02",
                "scheme_name": "HDFC Flexi Cap Fund",
            },
            "vector": [0.99, 0.1, 0.0],
        },
        {
            "id": "3",
            "score": 0.7,
            "payload": {
                "text": "gamma chunk",
                "source_url": "https://example.com/c",
                "scheme_name": "HDFC Flexi Cap Fund",
            },
            "vector": [0.0, 1.0, 0.0],
        },
    ]

    with patch("retriever.search_qdrant", return_value=fake_hits):
        out = vector_search_and_rerank(
            "What is the expense ratio of HDFC Flexi Cap Fund?",
            query_vector=[0.0, 0.0, 0.0],
        )

    assert len(out.chunks) <= 3
    assert out.scheme_filter_applied == "HDFC Flexi Cap Fund"
    texts = {c.text for c in out.chunks}
    assert "alpha chunk" in texts
    assert out.primary_source_url in (
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    )
