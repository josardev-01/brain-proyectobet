from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class FinalizationState:
    quota_date: str | None = None
    daily_remaining: int | None = None
    deferred_until: dict[str, datetime] = field(default_factory=dict)

    def can_spend(self, *, on_date: str, requested: int, reserve: int) -> bool:
        if self.quota_date != on_date or self.daily_remaining is None:
            return True
        return self.daily_remaining - requested >= reserve

    def can_check_fixture(self, fixture_id: str, *, now: datetime) -> bool:
        retry_at = self.deferred_until.get(fixture_id)
        return retry_at is None or retry_at <= now


def load_finalization_state(path: Path) -> FinalizationState:
    if not path.exists():
        return FinalizationState()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return FinalizationState(
        quota_date=payload.get("quota_date"),
        daily_remaining=payload.get("daily_remaining"),
        deferred_until={
            str(fixture_id): datetime.fromisoformat(value)
            for fixture_id, value in payload.get("deferred_until", {}).items()
        },
    )


def save_finalization_state(path: Path, state: FinalizationState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "quota_date": state.quota_date,
        "daily_remaining": state.daily_remaining,
        "deferred_until": {
            fixture_id: retry_at.isoformat()
            for fixture_id, retry_at in state.deferred_until.items()
        },
    }
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
