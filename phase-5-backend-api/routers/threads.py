from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.schemas import ThreadCreateResponse, ThreadDetailResponse, ThreadListResponse
from services.thread_manager import thread_manager

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("", response_model=ThreadListResponse)
def list_threads() -> ThreadListResponse:
    return ThreadListResponse(threads=thread_manager.list_summaries())


@router.post("", response_model=ThreadCreateResponse)
def create_thread() -> ThreadCreateResponse:
    t = thread_manager.create_thread()
    return ThreadCreateResponse(thread_id=t.thread_id, title=t.title, created_at=t.created_at)


@router.get("/{thread_id}", response_model=ThreadDetailResponse)
def get_thread(thread_id: str) -> ThreadDetailResponse:
    t = thread_manager.get(thread_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return ThreadDetailResponse(
        thread_id=t.thread_id,
        title=t.title,
        created_at=t.created_at,
        updated_at=t.updated_at,
        messages=t.messages,
    )


@router.delete("/{thread_id}")
def delete_thread(thread_id: str) -> dict:
    ok = thread_manager.delete(thread_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"deleted": True, "thread_id": thread_id}
