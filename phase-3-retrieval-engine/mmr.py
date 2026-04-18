"""Maximal marginal relevance re-ranking (numpy)."""

from __future__ import annotations

import numpy as np


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.asarray(a, dtype=np.float64)
    vb = np.asarray(b, dtype=np.float64)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def maximal_marginal_relevance(
    doc_embeddings: list[list[float]],
    relevance_scores: list[float],
    lambda_mult: float,
    k: int,
) -> list[int]:
    """
    Select up to k document indices. relevance_scores[i] aligns with doc_embeddings[i].
    Higher relevance_scores = more relevant to the query (from the vector DB).
    """
    n = len(doc_embeddings)
    if n == 0 or k <= 0:
        return []
    k = min(k, n)
    selected: list[int] = []
    candidates = set(range(n))

    while len(selected) < k and candidates:
        best_i: int | None = None
        best_score = -float("inf")
        for i in candidates:
            rel = relevance_scores[i]
            if not selected:
                mmr_score = rel
            else:
                max_sim = max(
                    cosine_similarity(doc_embeddings[i], doc_embeddings[j]) for j in selected
                )
                mmr_score = lambda_mult * rel - (1.0 - lambda_mult) * max_sim
            if mmr_score > best_score:
                best_score = mmr_score
                best_i = i
        assert best_i is not None
        selected.append(best_i)
        candidates.discard(best_i)

    return selected
