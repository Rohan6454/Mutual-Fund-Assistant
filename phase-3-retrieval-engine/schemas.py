"""Retrieval payloads and results (Phase 3 → Phase 4)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from enums import Intent


class RetrievedChunk(BaseModel):
    text: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    """Context for generation when retrieval succeeds above threshold."""

    chunks: list[RetrievedChunk] = Field(default_factory=list)
    primary_source_url: str = ""
    primary_source_date: str | None = None
    confidence: float = 0.0
    scheme_filter_applied: str | None = None
    enhanced_query: str = ""


class GuardrailResult(BaseModel):
    """When retrieval must not run (or query is classified only)."""

    intent: Intent
    blocked: bool = False
