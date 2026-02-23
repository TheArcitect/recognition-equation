"""Tests for the recognition journal."""

import tempfile
from pathlib import Path

from rec_eq.model import Situation
from rec_eq.journal import Journal


def _tmp_journal() -> Journal:
    d = tempfile.mkdtemp()
    return Journal(Path(d) / "test_journal.jsonl")


def test_journal_creates_file():
    j = _tmp_journal()
    assert not j.path.exists()
    j.ensure_exists()
    assert j.path.exists()


def test_journal_append_and_read():
    j = _tmp_journal()
    j.append(Situation(name="s1", contact=8, agenda=2))
    j.append(Situation(name="s2", contact=3, agenda=7))

    entries = j.read_all()
    assert len(entries) == 2
    assert entries[0].name == "s1"
    assert entries[1].recognition == -4.0


def test_journal_read_last():
    j = _tmp_journal()
    for i in range(10):
        j.append(Situation(name=f"s{i}", contact=i, agenda=0))

    last3 = j.read_last(3)
    assert len(last3) == 3
    assert last3[0].name == "s7"


def test_journal_count():
    j = _tmp_journal()
    assert j.count == 0
    j.append(Situation(contact=5, agenda=5))
    assert j.count == 1


def test_journal_stats():
    j = _tmp_journal()
    j.append(Situation(name="a", domain="work", contact=8, agenda=2))
    j.append(Situation(name="b", domain="work", contact=6, agenda=4))
    j.append(Situation(name="c", domain="personal", contact=9, agenda=1))

    stats = j.stats()
    assert stats["total"] == 3
    assert stats["avg_r"] > 0
    assert "work" in stats["domain_avg_r"]
    assert "personal" in stats["domain_avg_r"]
    assert stats["max_r"] == 8.0  # 9-1
    assert stats["min_r"] == 2.0  # 6-4


def test_journal_empty_stats():
    j = _tmp_journal()
    assert j.stats() == {}
