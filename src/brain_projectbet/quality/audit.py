from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from brain_projectbet.domain.candidates import TERMINAL_MATCH_STATUSES
from brain_projectbet.domain.models import MatchSnapshot


QUALITY_METRICS = (
    "shots_home",
    "shots_away",
    "shots_on_target_home",
    "shots_on_target_away",
    "corners_home",
    "corners_away",
    "possession_home",
    "possession_away",
    "red_cards_home",
    "red_cards_away",
    "dangerous_attacks_home",
    "dangerous_attacks_away",
    "xg_home",
    "xg_away",
)


@dataclass(frozen=True, slots=True)
class FixtureQuality:
    fixture_id: str
    snapshots: int
    first_minute: int | None
    last_minute: int | None
    terminal_observed: bool
    exact_ten_minute_window_available: bool
    maximum_gap_minutes: int | None
    duplicate_clock_observations: int
    metric_availability: dict[str, float]


@dataclass(frozen=True, slots=True)
class QualitySummary:
    fixtures: int
    snapshots: int
    terminal_fixtures: int
    fixtures_with_exact_ten_minute_window: int
    weighted_metric_availability: dict[str, float]
    fixture_reports: tuple[FixtureQuality, ...]


def audit_fixture(snapshots: Iterable[MatchSnapshot]) -> FixtureQuality:
    items = list(snapshots)
    if not items:
        raise ValueError("se requiere al menos un snapshot")
    fixture_ids = {item.provider_match_id for item in items}
    if len(fixture_ids) != 1:
        raise ValueError("todos los snapshots deben pertenecer al mismo fixture")
    timed = sorted(
        (item for item in items if item.minute is not None),
        key=lambda item: (item.minute, item.minute_extra or 0, item.captured_at),
    )
    clocks = [(item.minute, item.minute_extra or 0) for item in timed]
    minutes = sorted({item.minute for item in timed})
    gaps = [current - previous for previous, current in zip(minutes, minutes[1:])]
    exact_window = any(
        later - earlier == 10
        for index, earlier in enumerate(minutes)
        for later in minutes[index + 1 :]
    )
    availability = {
        metric: round(sum(getattr(item, metric) is not None for item in items) / len(items), 4)
        for metric in QUALITY_METRICS
    }
    return FixtureQuality(
        fixture_id=items[0].provider_match_id,
        snapshots=len(items),
        first_minute=minutes[0] if minutes else None,
        last_minute=minutes[-1] if minutes else None,
        terminal_observed=any(item.status in TERMINAL_MATCH_STATUSES for item in items),
        exact_ten_minute_window_available=exact_window,
        maximum_gap_minutes=max(gaps) if gaps else None,
        duplicate_clock_observations=len(clocks) - len(set(clocks)),
        metric_availability=availability,
    )


def summarize_quality(fixtures: Iterable[Iterable[MatchSnapshot]]) -> QualitySummary:
    groups = [list(group) for group in fixtures]
    reports = tuple(audit_fixture(group) for group in groups if group)
    total_snapshots = sum(report.snapshots for report in reports)
    weighted = {}
    for metric in QUALITY_METRICS:
        available = sum(
            sum(getattr(snapshot, metric) is not None for snapshot in group)
            for group in groups
        )
        weighted[metric] = round(available / total_snapshots, 4) if total_snapshots else 0.0
    return QualitySummary(
        fixtures=len(reports),
        snapshots=total_snapshots,
        terminal_fixtures=sum(report.terminal_observed for report in reports),
        fixtures_with_exact_ten_minute_window=sum(
            report.exact_ten_minute_window_available for report in reports
        ),
        weighted_metric_availability=weighted,
        fixture_reports=reports,
    )
