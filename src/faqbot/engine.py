"""The presentation's topic-and-keyword rules, independent of any UI."""

import re
from collections.abc import Sequence
from typing import Final

from faqbot.models import FAQ, ChatReply

FALLBACK: Final[str] = "No answer saved. Ask your class rep."


def answer_question(question: str, faqs: Sequence[FAQ]) -> ChatReply:
    """Match complete words, ignoring case and punctuation.

    A rule needs its topic and any one of its keywords. If several rules match,
    return all of their saved answers with topic labels.
    """
    words = set(re.findall(r"\b\w+\b", question.lower()))
    matches = tuple(
        faq
        for faq in faqs
        if faq.topic in words and any(keyword in words for keyword in faq.keywords)
    )
    if matches:
        message = (
            matches[0].answer
            if len(matches) == 1
            else "\n".join(f"{faq.topic.capitalize()}: {faq.answer}" for faq in matches)
        )
        return ChatReply(message=message, matches=matches)

    suggestions = tuple(
        faq.topic if faq.topic in faq.keywords else f"{faq.topic} {faq.keywords[0]}"
        for faq in faqs[:3]
    )
    return ChatReply(message=FALLBACK, suggestions=suggestions)
