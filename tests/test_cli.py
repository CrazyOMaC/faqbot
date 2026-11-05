"""Verify the installed entry point and the shared terminal workflow."""

from pathlib import Path

import pytest

from faqbot.cli import main, run_terminal
from faqbot.storage import FAQRepository


def test_terminal_entry_point_saves_faqs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    database = tmp_path / "faqs.sqlite3"
    questions = iter(
        [
            "When is the assignment due?",
            "/add",
            "canteen",
            "hours, open",
            "Open until 6 PM.",
            "canteen open?",
            "/topics",
            "exit",
        ]
    )

    def read_input(_prompt: str) -> str:
        return next(questions)

    monkeypatch.setattr("builtins.input", read_input)
    monkeypatch.setattr("sys.argv", ["faqbot", "--cli", "--database", str(database)])
    main()
    output = capsys.readouterr().out
    assert "Bot: Friday, 5 PM." in output
    assert "Bot: Open until 6 PM." in output
    assert "canteen: hours, open" in output
    assert output.endswith("Bot: Goodbye!\n")
    assert FAQRepository(database).list_faqs()[-1].topic == "canteen"


@pytest.mark.parametrize("ending", [EOFError(), KeyboardInterrupt()])
def test_terminal_handles_interruption(
    ending: BaseException,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def read_input(_prompt: str) -> str:
        raise ending

    monkeypatch.setattr("builtins.input", read_input)
    run_terminal(FAQRepository(tmp_path / "faqs.sqlite3"))
    assert capsys.readouterr().out.endswith("Bot: Goodbye!\n")


def test_invalid_port_is_a_usage_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["faqbot", "--port", "0"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert "between 1 and 65535" in capsys.readouterr().err
