"""Recognition journal — log situations over time and find patterns."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .model import Situation


DEFAULT_JOURNAL_PATH = Path.home() / "Documents" / "Recognition-Journal" / "journal.jsonl"


class Journal:
    """Append-only journal of scored situations."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or DEFAULT_JOURNAL_PATH

    def ensure_exists(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def append(self, situation: Situation) -> None:
        self.ensure_exists()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(situation.to_json() + "\n")

    def read_all(self) -> list[Situation]:
        if not self.path.exists():
            return []
        results = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                results.append(Situation.from_json(line))
            except Exception:
                continue
        return results

    def read_last(self, n: int = 1) -> list[Situation]:
        all_entries = self.read_all()
        return all_entries[-n:]

    @property
    def count(self) -> int:
        if not self.path.exists():
            return 0
        return sum(1 for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip())

    def stats(self) -> dict:
        """Compute statistics across all journal entries."""
        entries = self.read_all()
        if not entries:
            return {}

        rs = [e.recognition for e in entries]
        cs = [e.contact for e in entries]
        a_s = [e.agenda for e in entries]

        # By domain
        domains = {}
        for e in entries:
            d = e.domain or "untagged"
            if d not in domains:
                domains[d] = []
            domains[d].append(e.recognition)

        domain_avgs = {d: round(sum(rs) / len(rs), 2) for d, rs in domains.items()}

        # By signal label
        from collections import Counter
        labels = Counter(e.signal_label for e in entries)

        return {
            "total": len(entries),
            "avg_r": round(sum(rs) / len(rs), 2),
            "avg_c": round(sum(cs) / len(cs), 2),
            "avg_a": round(sum(a_s) / len(a_s), 2),
            "max_r": max(rs),
            "min_r": min(rs),
            "domain_avg_r": domain_avgs,
            "signal_distribution": dict(labels.most_common()),
        }
