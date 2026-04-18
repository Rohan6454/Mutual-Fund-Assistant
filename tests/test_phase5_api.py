from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_threads_and_chat_flow(monkeypatch) -> None:
    client = TestClient(app)

    def _fake_answer(message: str) -> dict:
        return {
            "answer": "Sample factual answer.\n\nSource: https://example.com\nLast updated from sources: 2026-04-14",
            "intent": "factual",
            "blocked": False,
            "source_url": "https://example.com",
            "confidence": 0.81,
        }

    monkeypatch.setattr("app.routers.chat.answer_query", _fake_answer)

    create_resp = client.post("/api/threads")
    assert create_resp.status_code == 200
    thread_id = create_resp.json()["thread_id"]

    chat_resp = client.post("/api/chat", json={"thread_id": thread_id, "message": "What is NAV?"})
    assert chat_resp.status_code == 200
    body = chat_resp.json()
    assert body["thread_id"] == thread_id
    assert body["intent"] == "factual"
    assert "Source:" in body["answer"]

    detail = client.get(f"/api/threads/{thread_id}")
    assert detail.status_code == 200
    assert len(detail.json()["messages"]) >= 2

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] in ("ok", "degraded")
