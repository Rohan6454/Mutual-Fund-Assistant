from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from models.enums import MessageRole
from models.schemas import MessageItem, ThreadSummary


@dataclass
class ThreadState:
    thread_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageItem] = field(default_factory=list)


class ThreadManager:
    def __init__(self, max_threads: int = 50, max_messages_per_thread: int = 100) -> None:
        self.max_threads = max_threads
        self.max_messages_per_thread = max_messages_per_thread
        self._threads: OrderedDict[str, ThreadState] = OrderedDict()

    def create_thread(self, title: str = "New chat") -> ThreadState:
        now = datetime.now(timezone.utc)
        thread_id = str(uuid4())
        state = ThreadState(thread_id=thread_id, title=title, created_at=now, updated_at=now)
        self._threads[thread_id] = state
        self._threads.move_to_end(thread_id)
        self._evict_if_needed()
        return state

    def get_or_create(self, thread_id: str | None) -> ThreadState:
        if thread_id and thread_id in self._threads:
            self._threads.move_to_end(thread_id)
            return self._threads[thread_id]
        return self.create_thread()

    def get(self, thread_id: str) -> ThreadState | None:
        t = self._threads.get(thread_id)
        if t:
            self._threads.move_to_end(thread_id)
        return t

    def delete(self, thread_id: str) -> bool:
        return self._threads.pop(thread_id, None) is not None

    def add_message(self, thread_id: str, role: MessageRole, text: str, metadata: dict | None = None) -> ThreadState:
        state = self.get_or_create(thread_id)
        item = MessageItem(
            role=role,
            text=text,
            created_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
        state.messages.append(item)
        if len(state.messages) > self.max_messages_per_thread:
            state.messages = state.messages[-self.max_messages_per_thread :]
        state.updated_at = item.created_at
        if role == MessageRole.USER and (not state.title or state.title == "New chat"):
            state.title = text[:60] + ("..." if len(text) > 60 else "")
        self._threads.move_to_end(state.thread_id)
        return state

    def list_summaries(self) -> list[ThreadSummary]:
        out: list[ThreadSummary] = []
        for thread_id in reversed(self._threads.keys()):
            t = self._threads[thread_id]
            out.append(
                ThreadSummary(
                    thread_id=t.thread_id,
                    title=t.title,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                    message_count=len(t.messages),
                )
            )
        return out

    def _evict_if_needed(self) -> None:
        while len(self._threads) > self.max_threads:
            self._threads.popitem(last=False)


thread_manager = ThreadManager()
