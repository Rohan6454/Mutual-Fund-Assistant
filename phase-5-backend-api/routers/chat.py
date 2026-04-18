from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.enums import MessageRole
from models.schemas import ChatRequest, ChatResponse
from services.rag_service import answer_query
from services.thread_manager import thread_manager
from config.settings import settings

router = APIRouter(tags=["chat"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT)
def chat(request: Request, payload: ChatRequest) -> ChatResponse:
    thread = thread_manager.get_or_create(payload.thread_id)
    thread_manager.add_message(thread.thread_id, MessageRole.USER, payload.message)
    try:
        result = answer_query(payload.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG engine error: {e}") from e

    thread_manager.add_message(
        thread.thread_id,
        MessageRole.ASSISTANT,
        result["answer"],
        metadata={
            "intent": result.get("intent"),
            "blocked": result.get("blocked"),
            "source_url": result.get("source_url"),
            "confidence": result.get("confidence"),
        },
    )
    return ChatResponse(
        thread_id=thread.thread_id,
        answer=result["answer"],
        intent=result.get("intent", "unknown"),
        blocked=bool(result.get("blocked", False)),
        source_url=result.get("source_url"),
        confidence=result.get("confidence"),
    )
