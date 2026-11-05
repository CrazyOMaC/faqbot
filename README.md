# FAQbot

A student FAQ chatbot with a local web UI, an editable FAQ library, persistent
SQLite storage, and a terminal mode. Built as a Python 3.14+ package managed by uv.

## Run

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run
these commands from this directory:

```powershell
uv sync --locked
uv run faqbot
```

Open **http://127.0.0.1:8000**. The dark UI has two tabs: Chat and FAQs, with
readable text and high contrast controls. It includes suggested questions,
browser chat history, FAQ search, and forms to add, edit, and delete FAQs.
It works without an API key or a frontend build step.

For the terminal chatbot:

```powershell
uv run faqbot --cli
```

Terminal commands: `/topics`, `/add`, and `exit`. Both interfaces use the same
database. FAQs are saved in `data/faqs.sqlite3`, relative to the working directory.
The 15 starter FAQs are inserted only when the database is first created.

```powershell
uv run faqbot --port 8080 --database data/my-class.sqlite3
uv run python -m faqbot --cli
```

The server listens on `127.0.0.1` by default. The local workspace has no accounts;
anyone who can reach the server can edit its FAQ library. API documentation is
available at **http://127.0.0.1:8000/api/docs**.

## Matching rules

The original presentation's rules are preserved. Questions are lowercased and
split into complete words, ignoring punctuation. An answer needs the topic word
and at least one keyword from its group.

| Topic | Keywords | Initial answer |
| --- | --- | --- |
| assignment | due, deadline, submit | Friday, 5 PM. |
| notes | notes | Python folder in the class drive. |
| exam | timetable, schedule | Python exam: 14 December 2026, 10 AM-12 PM, Room 204. |

The starter library also covers library hours and books, attendance, the syllabus,
fees, results, scholarships, course registration, practicals, projects, transport,
hostel applications, and department contacts. The chat shows six example questions.

“When is the assignment due?” and “When should I submit the assignment?” both
return “Friday, 5 PM.” The word `assignment` on its own does not match. Questions
matching several topics return all matching answers. Unsupported questions get
a fallback and suggested supported questions.

Topic names and keywords each contain one word of English letters. Answers can
contain up to 2,000 characters. Edit the starter answers in the FAQs tab to use
your own class details. There is no language model or fuzzy matching.

## Development

```powershell
uv run pyrefly check
uv run ruff check
uv run ruff format --check
uv run pytest
uv build
```

Pyrefly's `strict` preset and Ruff's Python 3.14 target are configured in
`pyproject.toml`. `uv.lock` fixes dependency versions. Tests use temporary databases
and cover the presentation examples, matching boundaries, input validation,
database restarts, and the HTTP API.

```text
src/faqbot/
  models.py       Validated FAQ and chat types
  engine.py       Shared topic-and-keyword matching
  storage.py      SQLite persistence
  web.py          FastAPI app and HTTP endpoints
  cli.py          Web server and terminal entry points
  static/         HTML, CSS, and JavaScript, bundled in the package
tests/            Matching, storage, and API tests
```

The backend uses FastAPI, Pydantic, and Uvicorn. The frontend uses plain HTML,
CSS, and JavaScript with no CDN dependencies. Browser chat history stays on that
browser; the FAQ library is shared through SQLite. Clearing the conversation
does not delete FAQs.
