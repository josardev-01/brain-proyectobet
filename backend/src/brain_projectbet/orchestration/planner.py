from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from brain_projectbet.discovery.eligible import EligibleFixture


@dataclass(frozen=True, slots=True)
class MonitoringWindow:
    starts_at: datetime
    ends_at: datetime
    fixture_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MatchdayPlan:
    windows: tuple[MonitoringWindow, ...]
    finalize_at: datetime | None


def build_matchday_plan(
    fixtures: list[EligibleFixture],
    *,
    warmup_after_kickoff_minutes: int = 35,
    monitor_after_kickoff_minutes: int = 150,
    finalize_after_kickoff_minutes: int = 180,
) -> MatchdayPlan:
    """Agrupa ventanas solapadas para compartir una consulta global por ciclo."""
    if warmup_after_kickoff_minutes < 0:
        raise ValueError("warmup_after_kickoff_minutes no puede ser negativo")
    if monitor_after_kickoff_minutes <= warmup_after_kickoff_minutes:
        raise ValueError("la ventana de monitoreo debe terminar despues de comenzar")
    if finalize_after_kickoff_minutes < monitor_after_kickoff_minutes:
        raise ValueError("la finalizacion no puede preceder al fin del monitoreo")
    if not fixtures:
        return MatchdayPlan(windows=(), finalize_at=None)

    raw_windows = sorted(
        (
            MonitoringWindow(
                starts_at=fixture.kickoff_at + timedelta(minutes=warmup_after_kickoff_minutes),
                ends_at=fixture.kickoff_at + timedelta(minutes=monitor_after_kickoff_minutes),
                fixture_ids=(fixture.fixture_id,),
            )
            for fixture in fixtures
        ),
        key=lambda window: window.starts_at,
    )
    merged: list[MonitoringWindow] = []
    for window in raw_windows:
        if not merged or window.starts_at > merged[-1].ends_at:
            merged.append(window)
            continue
        previous = merged[-1]
        merged[-1] = MonitoringWindow(
            starts_at=previous.starts_at,
            ends_at=max(previous.ends_at, window.ends_at),
            fixture_ids=tuple(dict.fromkeys((*previous.fixture_ids, *window.fixture_ids))),
        )

    return MatchdayPlan(
        windows=tuple(merged),
        finalize_at=max(
            fixture.kickoff_at + timedelta(minutes=finalize_after_kickoff_minutes)
            for fixture in fixtures
        ),
    )


def action_at(plan: MatchdayPlan, now: datetime) -> tuple[str, datetime | None]:
    for window in plan.windows:
        if now < window.starts_at:
            return "wait", window.starts_at
        if window.starts_at <= now <= window.ends_at:
            return "monitor", now
    if plan.finalize_at is not None and now < plan.finalize_at:
        return "wait", plan.finalize_at
    if plan.finalize_at is not None:
        return "finalize", now
    return "complete", None
