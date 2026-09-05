from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from brain_projectbet.discovery.eligible import EligibleFixture


def _default(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def save_eligible_fixtures(path: Path, fixtures: tuple[EligibleFixture, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(fixture) for fixture in fixtures], ensure_ascii=False, indent=2, default=_default),
        encoding="utf-8",
    )


def load_eligible_fixtures(path: Path) -> list[EligibleFixture]:
    data = json.loads(path.read_text(encoding="utf-8"))
    fixtures = []
    for item in data:
        item["kickoff_at"] = datetime.fromisoformat(item["kickoff_at"])
        item["discovered_at"] = datetime.fromisoformat(item["discovered_at"])
        fixtures.append(EligibleFixture(**item))
    return fixtures
