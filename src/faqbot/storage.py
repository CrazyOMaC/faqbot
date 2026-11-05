"""A small SQLite repository; each operation owns and closes its connection."""

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from pydantic import TypeAdapter

from faqbot.models import DEFAULT_FAQS, FAQ


class DuplicateTopicError(ValueError):
    """An FAQ with this topic already exists."""


class TopicNotFoundError(KeyError):
    """An FAQ was edited or deleted after it had already been removed."""


def _parse_row(row: tuple[object, ...]) -> FAQ:
    topic, keywords, answer = row
    if not isinstance(topic, str) or not isinstance(keywords, str):
        raise ValueError("Invalid topic or keywords in the FAQ database.")
    if not isinstance(answer, str):
        raise ValueError("Invalid answer in the FAQ database.")
    return FAQ(
        topic=topic,
        keywords=TypeAdapter(tuple[str, ...]).validate_json(keywords),
        answer=answer,
    )


class FAQRepository:
    """Persist FAQ rules and seed the presentation's examples on first use."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            # Lock initialization so two processes cannot seed the same new DB.
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'faqs'"
            ).fetchone()
            connection.execute(
                "CREATE TABLE IF NOT EXISTS faqs "
                "(topic TEXT PRIMARY KEY, keywords TEXT NOT NULL, answer TEXT NOT NULL)"
            )
            if existing is None:
                connection.executemany(
                    "INSERT INTO faqs (topic, keywords, answer) VALUES (?, ?, ?)",
                    [
                        (faq.topic, json.dumps(faq.keywords), faq.answer)
                        for faq in DEFAULT_FAQS
                    ],
                )

    def list_faqs(self) -> list[FAQ]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT topic, keywords, answer FROM faqs ORDER BY rowid"
            ).fetchall()
        return [_parse_row(row) for row in rows]

    def add(self, faq: FAQ) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO faqs (topic, keywords, answer) VALUES (?, ?, ?)",
                    (faq.topic, json.dumps(faq.keywords), faq.answer),
                )
        except sqlite3.IntegrityError as error:
            raise DuplicateTopicError(
                f"The topic '{faq.topic}' already exists."
            ) from error

    def update(self, faq: FAQ) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE faqs SET keywords = ?, answer = ? WHERE topic = ?",
                (json.dumps(faq.keywords), faq.answer, faq.topic),
            )
            if cursor.rowcount == 0:
                raise TopicNotFoundError(faq.topic)

    def delete(self, topic: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM faqs WHERE topic = ?", (topic,))
            if cursor.rowcount == 0:
                raise TopicNotFoundError(topic)
