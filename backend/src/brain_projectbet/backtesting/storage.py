from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from brain_projectbet.backtesting.results import BacktestRecord


def _json_default(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def append_backtest_once(path: Path, record: BacktestRecord) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("record_id") == record.record_id:
                return False
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(asdict(record), ensure_ascii=False, default=_json_default))
        stream.write("\n")
    return True


def load_backtests(path: Path) -> list[BacktestRecord]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        item["finalized_at"] = datetime.fromisoformat(item["finalized_at"])
        records.append(BacktestRecord(**item))
    return records
