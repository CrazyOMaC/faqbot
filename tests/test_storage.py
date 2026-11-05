"""Real SQLite checks, including restart behavior and rejected changes."""

from pathlib import Path

import pytest

from faqbot.models import DEFAULT_FAQS, FAQ
from faqbot.storage import DuplicateTopicError, FAQRepository, TopicNotFoundError


@pytest.fixture
def repository(tmp_path: Path) -> FAQRepository:
    repository = FAQRepository(tmp_path / "nested" / "faqs.sqlite3")
    repository.initialize()
    return repository


def test_seeded_once_and_deletions_survive_restart(repository: FAQRepository) -> None:
    assert repository.list_faqs() == list(DEFAULT_FAQS)
    for faq in DEFAULT_FAQS:
        repository.delete(faq.topic)
    reopened = FAQRepository(repository.path)
    reopened.initialize()
    assert reopened.list_faqs() == []


def test_add_and_update_survive_restart(repository: FAQRepository) -> None:
    canteen = FAQ(topic="canteen", keywords=("open",), answer="Until 6 PM.")
    repository.add(canteen)
    updated = FAQ(topic="canteen", keywords=("hours", "open"), answer="Until 7 PM.")
    repository.update(updated)
    reopened = FAQRepository(repository.path)
    reopened.initialize()
    assert reopened.list_faqs() == [*DEFAULT_FAQS, updated]


def test_duplicate_does_not_replace_original(repository: FAQRepository) -> None:
    with pytest.raises(DuplicateTopicError):
        repository.add(FAQ(topic="notes", keywords=("new",), answer="Replacement"))
    assert repository.list_faqs() == list(DEFAULT_FAQS)


def test_missing_updates_and_deletes(repository: FAQRepository) -> None:
    with pytest.raises(TopicNotFoundError):
        repository.update(FAQ(topic="missing", keywords=("missing",), answer="Nothing"))
    with pytest.raises(TopicNotFoundError):
        repository.delete("missing")


def test_answers_round_trip_without_interpreting_content(
    repository: FAQRepository,
) -> None:
    answer = "It's in room 2; <script>alert('demo')</script>\nAsk the class rep."
    repository.add(FAQ(topic="help", keywords=("help",), answer=answer))
    assert repository.list_faqs()[-1].answer == answer
