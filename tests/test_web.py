"""HTTP contract checks against the app and a temporary SQLite database."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from faqbot.models import DEFAULT_FAQS, FAQ, ChatReply
from faqbot.web import create_app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(tmp_path / "faqs.sqlite3")) as client:
        yield client


def test_ui_and_assets_are_served(client: TestClient) -> None:
    page = client.get("/")
    assert page.status_code == 200
    assert "FAQbot - Student FAQs" in page.text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/api/docs").status_code == 200


def test_list_and_chat(client: TestClient) -> None:
    response = client.get("/api/faqs")
    assert TypeAdapter(list[FAQ]).validate_json(response.text) == list(DEFAULT_FAQS)
    response = client.post("/api/chat", json={"message": "When is the assignment due?"})
    assert response.status_code == 200
    assert ChatReply.model_validate_json(response.text).message == "Friday, 5 PM."


def test_crud_changes_are_immediately_used_by_chat(client: TestClient) -> None:
    faq = FAQ(topic="canteen", keywords=("hours", "open"), answer="Until 6 PM.")
    response = client.post("/api/faqs", json=faq.model_dump(mode="json"))
    assert response.status_code == 201
    assert FAQ.model_validate_json(response.text) == faq
    assert client.post("/api/faqs", json=faq.model_dump(mode="json")).status_code == 409
    updated = FAQ(topic="canteen", keywords=("open",), answer="Until 7 PM.")
    response = client.put("/api/faqs/canteen", json=updated.model_dump(mode="json"))
    assert response.status_code == 200
    reply = client.post("/api/chat", json={"message": "canteen open?"})
    assert ChatReply.model_validate_json(reply.text).message == "Until 7 PM."
    assert client.delete("/api/faqs/canteen").status_code == 204
    assert client.delete("/api/faqs/canteen").status_code == 404
    reply = client.post("/api/chat", json={"message": "canteen open?"})
    assert not ChatReply.model_validate_json(reply.text).matches


def test_missing_topic_and_rename_are_rejected(client: TestClient) -> None:
    faq = FAQ(topic="missing", keywords=("open",), answer="Answer")
    assert client.put("/api/faqs/missing", json=faq.model_dump()).status_code == 404
    assert client.put("/api/faqs/notes", json=faq.model_dump()).status_code == 422


@pytest.mark.parametrize("message", ["", "  ", "x" * 2001, 123, None])
def test_invalid_messages(client: TestClient, message: object) -> None:
    assert client.post("/api/chat", json={"message": message}).status_code == 422


def test_invalid_faq_does_not_change_storage(client: TestClient) -> None:
    response = client.post(
        "/api/faqs", json={"topic": "two words", "keywords": ["open"], "answer": "Hi"}
    )
    assert response.status_code == 422
    response = client.get("/api/faqs")
    assert TypeAdapter(list[FAQ]).validate_json(response.text) == list(DEFAULT_FAQS)


def test_app_restart_keeps_saved_answers(tmp_path: Path) -> None:
    database = tmp_path / "faqs.sqlite3"
    faq = FAQ(topic="canteen", keywords=("open",), answer="Until 6 PM.")
    with TestClient(create_app(database)) as first:
        assert first.post("/api/faqs", json=faq.model_dump()).status_code == 201
    with TestClient(create_app(database)) as second:
        reply = second.post("/api/chat", json={"message": "canteen open?"})
        assert ChatReply.model_validate_json(reply.text).message == "Until 6 PM."
