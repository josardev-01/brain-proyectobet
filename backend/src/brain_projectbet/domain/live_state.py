from __future__ import annotations

from datetime import UTC, datetime, timedelta


LIVE_STATUSES = frozenset({"1H", "HT", "2H", "ET", "BT", "P", "LIVE"})
TERMINAL_STATUSES = frozenset({"FT", "AET", "PEN", "CANC", "ABD", "AWD", "WO"})
FRESHNESS_LIMIT = timedelta(minutes=10)
MATCH_DURATION_LIMIT = timedelta(hours=4)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def observation_state(
    status: str,
    kickoff_at: datetime,
    last_snapshot_at: datetime | None,
    *,
    now: datetime | None = None,
) -> str:
    current = as_utc(now or datetime.now(UTC))
    kickoff = as_utc(kickoff_at)
    if status in TERMINAL_STATUSES:
        return "FINISHED"
    if status not in LIVE_STATUSES:
        return "STALE" if current - kickoff > MATCH_DURATION_LIMIT else "SCHEDULED"
    if last_snapshot_at is None:
        return "STALE"
    captured = as_utc(last_snapshot_at)
    if (timedelta(0) <= current - captured <= FRESHNESS_LIMIT
            and timedelta(0) <= current - kickoff <= MATCH_DURATION_LIMIT):
        return "LIVE"
    return "STALE"
