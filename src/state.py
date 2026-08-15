from __future__ import annotations

import json
from datetime import date
from pathlib import Path


class StateStore:
    def __init__(self, path: str = "data/last_sent.json"):
        self.path = Path(path)

    def last_sent_date(self) -> date | None:
        if not self.path.exists():
            return None
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            value = payload.get("last_sent_date")
            return date.fromisoformat(value) if value else None
        except (json.JSONDecodeError, ValueError, TypeError):
            return None

    def mark_sent(self, day: date) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"last_sent_date": day.isoformat()}, indent=2) + "\n",
            encoding="utf-8",
        )
