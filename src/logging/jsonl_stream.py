"""Append-only JSONL stream of pipeline events."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class JsonlStream:
    def __init__(self, path: str | Path = "logs/events.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event_type: str, **payload: Any) -> None:
        record = {
            "ts": time.time(),
            "event": event_type,
            **payload,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
