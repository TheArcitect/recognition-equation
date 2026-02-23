"""Tests for the CLI."""

import tempfile
from pathlib import Path

from rec_eq.cli import main


def _tmp_path() -> str:
    d = tempfile.mkdtemp()
    return str(Path(d) / "test.jsonl")


def test_cli_no_args(capsys):
    result = main([])
    assert result == 0


def test_cli_version(capsys):
    try:
        main(["--version"])
    except SystemExit:
        pass
    out = capsys.readouterr().out
    assert "0.1.0" in out


def test_cli_calc(capsys):
    result = main(["calc", "8", "2", "--name", "test"])
    assert result == 0


def test_cli_calc_with_log():
    p = _tmp_path()
    result = main(["--file", p, "calc", "7", "3", "--name", "logged", "--log"])
    assert result == 0
    # Verify it was logged
    from rec_eq.journal import Journal
    j = Journal(Path(p))
    assert j.count == 1


def test_cli_compare(capsys):
    result = main(["compare",
                    "--name-a", "Bad", "--c-a", "3", "--a-a", "8",
                    "--name-b", "Good", "--c-b", "9", "--a-b", "2"])
    assert result == 0


def test_cli_domain_list(capsys):
    result = main(["domain"])
    assert result == 0


def test_cli_domain_specific(capsys):
    result = main(["domain", "education"])
    assert result == 0


def test_cli_domain_not_found(capsys):
    result = main(["domain", "nonexistent"])
    assert result == 1


def test_cli_journal_empty(capsys):
    p = _tmp_path()
    result = main(["--file", p, "journal"])
    assert result == 0


def test_cli_journal_stats_empty(capsys):
    p = _tmp_path()
    result = main(["--file", p, "journal", "--stats"])
    assert result == 0


def test_cli_explain(capsys):
    result = main(["explain"])
    assert result == 0
