"""FastAPI application factory with local static assets and typed endpoints."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from faqbot import __version__
from faqbot.engine import answer_question
from faqbot.models import FAQ, ChatReply, ChatRequest
from faqbot.storage import DuplicateTopicError, FAQRepository, TopicNotFoundError


def create_app(database: Path = Path("data/faqs.sqlite3")) -> FastAPI:
    """Create an isolated app backed by the supplied SQLite database."""
    repository = FAQRepository(database)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        repository.initialize()
        yield

    app = FastAPI(
        title="FAQbot",
        description="Student questions, saved answers, and editable FAQ rules.",
        version=__version__,
        docs_url="/api/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    assets = Path(__file__).with_name("static")
    app.mount("/static", StaticFiles(directory=assets), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(assets / "index.html")

    @app.get("/api/faqs")
    def list_faqs() -> list[FAQ]:
        return repository.list_faqs()

    @app.post("/api/chat")
    def chat(request: ChatRequest) -> ChatReply:
        return answer_question(request.message, repository.list_faqs())

    @app.post("/api/faqs", status_code=201)
    def add_faq(faq: FAQ) -> FAQ:
        try:
            repository.add(faq)
        except DuplicateTopicError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return faq

    @app.put("/api/faqs/{topic}")
    def update_faq(topic: str, faq: FAQ) -> FAQ:
        if topic != faq.topic:
            raise HTTPException(
                status_code=422, detail="An existing topic cannot be renamed."
            )
        try:
            repository.update(faq)
        except TopicNotFoundError as error:
            raise HTTPException(status_code=404, detail="Topic not found.") from error
        return faq

    @app.delete("/api/faqs/{topic}", status_code=204)
    def delete_faq(topic: str) -> Response:
        try:
            repository.delete(topic)
        except TopicNotFoundError as error:
            raise HTTPException(status_code=404, detail="Topic not found.") from error
        return Response(status_code=204)

    return app
