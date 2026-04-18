"""MMR selection logic."""

from __future__ import annotations

from mmr import cosine_similarity, maximal_marginal_relevance


def test_cosine_orthogonal() -> None:
    a, b = [1.0, 0.0], [0.0, 1.0]
    assert abs(cosine_similarity(a, b)) < 1e-6


def test_cosine_parallel() -> None:
    a, b = [1.0, 2.0], [2.0, 4.0]
    assert abs(cosine_similarity(a, b) - 1.0) < 1e-6


def test_mmr_prefers_diverse_when_lambda_low() -> None:
    # Three docs: d0 very relevant, d1 similar to d0, d2 different direction
    d0 = [1.0, 0.0, 0.0]
    d1 = [0.99, 0.1, 0.0]
    d2 = [0.0, 1.0, 0.0]
    emb = [d0, d1, d2]
    scores = [0.95, 0.94, 0.50]
    # lambda=0.5 → after picking d0, should prefer d2 over near-duplicate d1
    picked = maximal_marginal_relevance(emb, scores, lambda_mult=0.5, k=2)
    assert picked[0] == 0
    assert picked[1] == 2


def test_mmr_k_larger_than_n() -> None:
    emb = [[1.0, 0.0], [0.0, 1.0]]
    scores = [0.8, 0.7]
    picked = maximal_marginal_relevance(emb, scores, lambda_mult=0.7, k=10)
    assert len(picked) == 2
