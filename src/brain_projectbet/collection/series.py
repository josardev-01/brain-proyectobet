from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Iterable

from brain_projectbet.domain.models import MatchSnapshot


ACCUMULATED_METRICS = (
    "shots_home",
    "shots_away",
    "shots_on_target_home",
    "shots_on_target_away",
    "dangerous_attacks_home",
    "dangerous_attacks_away",
    "corners_home",
    "corners_away",
    "xg_home",
    "xg_away",
)


@dataclass(frozen=True, slots=True)
class WindowFeatures:
    provider_match_id: str
    from_minute: int
    to_minute: int
    requested_window_minutes: int
    actual_window_minutes: int
    deltas: dict[str, int | float | None]


def _safe_delta(current: int | float | None, previous: int | float | None):
    if current is None or previous is None or current < previous:
        return None
    return current - previous


def derive_window(
    snapshots: Iterable[MatchSnapshot],
    *,
    window_minutes: int,
) -> WindowFeatures | None:
    if window_minutes <= 0:
        raise ValueError("window_minutes debe ser mayor que cero")
    ordered = sorted(
        (snapshot for snapshot in snapshots if snapshot.minute is not None),
        key=lambda snapshot: (snapshot.minute, snapshot.captured_at),
    )
    if len(ordered) < 2:
        return None
    current = ordered[-1]
    target_minute = current.minute - window_minutes
    candidates = [snapshot for snapshot in ordered[:-1] if snapshot.minute <= target_minute]
    if not candidates:
        return None
    previous = candidates[-1]
    deltas = {
        metric: _safe_delta(getattr(current, metric), getattr(previous, metric))
        for metric in ACCUMULATED_METRICS
    }
    return WindowFeatures(
        provider_match_id=current.provider_match_id,
        from_minute=previous.minute,
        to_minute=current.minute,
        requested_window_minutes=window_minutes,
        actual_window_minutes=current.minute - previous.minute,
        deltas=deltas,
    )


def snapshot_field_names() -> set[str]:
    return {field.name for field in fields(MatchSnapshot)}
