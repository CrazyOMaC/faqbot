"""Examples and matching boundaries from the project presentation."""

import pytest
from pydantic import ValidationError

from faqbot.engine import FALLBACK, answer_question
from faqbot.models import DEFAULT_FAQS, FAQ, ChatRequest


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("When is the assignment due?", "Friday, 5 PM."),
        ("When should I submit the assignment?", "Friday, 5 PM."),
        ("ASSIGNMENT: DEADLINE!!!", "Friday, 5 PM."),
        ("Where are the notes?", "Python folder in the class drive."),
        ("NOTES.", "Python folder in the class drive."),
        (
            "Exam timetable?",
            "Python exam: 14 December 2026, 10 AM-12 PM, Room 204. "
            "Arrive by 9:30 AM with your student ID.",
        ),
        (
            "Schedule for the exam?",
            "Python exam: 14 December 2026, 10 AM-12 PM, Room 204. "
            "Arrive by 9:30 AM with your student ID.",
        ),
    ],
)
def test_presentation_questions(question: str, expected: str) -> None:
    reply = answer_question(question, DEFAULT_FAQS)
    assert reply.message == expected
    assert len(reply.matches) == 1


@pytest.mark.parametrize(
    "question",
    ["assignment", "exam", "due", "schedule", "noteworthy", "assignments due"],
)
def test_requires_whole_topic_and_keyword(question: str) -> None:
    reply = answer_question(question, DEFAULT_FAQS)
    assert reply.message == FALLBACK
    assert not reply.matches
    assert reply.suggestions
    for suggestion in reply.suggestions:
        assert answer_question(suggestion, DEFAULT_FAQS).matches


def test_multiple_topics_return_all_answers() -> None:
    reply = answer_question("Assignment due and exam schedule?", DEFAULT_FAQS)
    assert reply.message == (
        "Assignment: Friday, 5 PM.\n"
        "Exam: Python exam: 14 December 2026, 10 AM-12 PM, Room 204. "
        "Arrive by 9:30 AM with your student ID."
    )
    assert [faq.topic for faq in reply.matches] == ["assignment", "exam"]


def test_empty_library_has_no_suggestions() -> None:
    reply = answer_question("Where are the notes?", [])
    assert reply.message == FALLBACK
    assert not reply.suggestions


def test_faq_normalizes_input() -> None:
    faq = FAQ(
        topic=" Library ", keywords=("HOURS", "open", "hours"), answer="  6 PM.  "
    )
    assert faq.topic == "library"
    assert faq.keywords == ("hours", "open")
    assert faq.answer == "6 PM."
    assert answer_question("When is the library OPEN?", [faq]).message == "6 PM."


@pytest.mark.parametrize(
    ("topic", "keywords", "answer"),
    [
        ("", ("open",), "answer"),
        ("two words", ("open",), "answer"),
        ("library!", ("open",), "answer"),
        ("library", (), "answer"),
        ("library", ("open!",), "answer"),
        ("library", ("open",), "   "),
    ],
)
def test_invalid_faqs(topic: str, keywords: tuple[str, ...], answer: str) -> None:
    with pytest.raises(ValidationError):
        FAQ(topic=topic, keywords=keywords, answer=answer)


@pytest.mark.parametrize("message", ["", "   ", "x" * 2001])
def test_invalid_questions(message: str) -> None:
    with pytest.raises(ValidationError):
        ChatRequest(message=message)
