"""Console entry point for the web server and terminal chatbot."""

import argparse
from dataclasses import dataclass
from pathlib import Path

import uvicorn
from pydantic import ValidationError

from faqbot import __version__
from faqbot.engine import answer_question
from faqbot.models import FAQ, ChatRequest
from faqbot.storage import DuplicateTopicError, FAQRepository
from faqbot.web import create_app


@dataclass
class Options:
    cli: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    database: Path = Path("data/faqs.sqlite3")


def _port(value: str) -> int:
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("The port must be between 1 and 65535.")
    return port


def _add_faq(repository: FAQRepository) -> None:
    topic = input("Topic (one word): ")
    keywords = tuple(input("Keywords (spaces or commas): ").replace(",", " ").split())
    answer = input("Answer: ")
    try:
        repository.add(FAQ(topic=topic, keywords=keywords, answer=answer))
    except (ValidationError, DuplicateTopicError) as error:
        print(f"Bot: Could not add FAQ: {error}")
    else:
        print("Bot: FAQ saved.")


def run_terminal(repository: FAQRepository) -> None:
    """Use the same database and matching rules as the web UI."""
    repository.initialize()
    print("Bot: Student FAQ chatbot.")
    print("Bot: Ask about assignments, notes, or exams. Commands: /topics, /add, exit.")
    try:
        while True:
            question = input("You: ").strip()
            if question.lower() == "exit":
                break
            if question == "/add":
                _add_faq(repository)
            elif question == "/topics":
                for faq in repository.list_faqs():
                    print(f"Bot: {faq.topic}: {', '.join(faq.keywords)}")
            elif question:
                try:
                    request = ChatRequest(message=question)
                except ValidationError:
                    print("Bot: Keep questions under 2,000 characters.")
                    continue
                reply = answer_question(request.message, repository.list_faqs())
                print(f"Bot: {reply.message}")
    except EOFError, KeyboardInterrupt:
        print()
    print("Bot: Goodbye!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Student FAQ chatbot and local web UI."
    )
    parser.add_argument("--version", action="version", version=f"FAQbot {__version__}")
    parser.add_argument(
        "--cli", action="store_true", help="Chat in the terminal instead."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Web server host.")
    parser.add_argument("--port", type=_port, default=8000, help="Web server port.")
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/faqs.sqlite3"),
        help="SQLite file path.",
    )
    options = Options()
    parser.parse_args(namespace=options)
    if options.cli:
        run_terminal(FAQRepository(options.database))
    else:
        uvicorn.run(create_app(options.database), host=options.host, port=options.port)
