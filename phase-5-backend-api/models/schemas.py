from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from models.enums import MessageRole


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    thread_id: str | None = None


class ChatResponse(BaseModel):
    thread_id: str
    answer: str
    intent: str
    blocked: bool
    confidence: float | None = None
    source_url: str | None = None


class MessageItem(BaseModel):
    role: MessageRole
    text: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ThreadCreateResponse(BaseModel):
    thread_id: str
    title: str
    created_at: datetime


class ThreadSummary(BaseModel):
    thread_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ThreadListResponse(BaseModel):
    threads: list[ThreadSummary]


class ThreadDetailResponse(BaseModel):
    thread_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageItem]


class HealthResponse(BaseModel):
    status: str
    qdrant: str
    timestamp: datetime
