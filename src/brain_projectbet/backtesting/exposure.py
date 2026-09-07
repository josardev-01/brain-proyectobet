from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True, slots=True)
class ScenarioExposure:
    fixture_id: str
    favorite_team_id: str
    score_reconciled: bool
    scenario_ever_active: bool | None
    first_active_minute: int | None
    first_active_minute_extra: int | None


def _is_counted_goal(event: Mapping[str, Any]) -> bool:
    if event.get("type") != "Goal":
        return False
    detail = str(event.get("detail", "")).lower()
    return "missed" not in detail and "cancel" not in detail


def audit_favorite_losing_exposure(
    *,
    fixture_id: str,
    home_team_id: str,
    away_team_id: str,
    favorite_team_id: str,
    final_home_score: int,
    final_away_score: int,
    events: Iterable[Mapping[str, Any]],
    minimum_minute: int = 45,
) -> ScenarioExposure:
    if favorite_team_id not in {home_team_id, away_team_id}:
        raise ValueError("el favorito debe ser uno de los equipos del fixture")
    goals = sorted(
        (event for event in events if _is_counted_goal(event)),
        key=lambda event: (
            int(event.get("time", {}).get("elapsed", -1)),
            int(event.get("time", {}).get("extra") or 0),
        ),
    )
    home_score = 0
    away_score = 0
    first_clock: tuple[int, int] | None = None
    threshold_checked = False

    def favorite_is_losing() -> bool:
        favorite_score = home_score if favorite_team_id == home_team_id else away_score
        opponent_score = away_score if favorite_team_id == home_team_id else home_score
        return favorite_score < opponent_score

    for event in goals:
        elapsed = int(event.get("time", {}).get("elapsed", -1))
        extra = int(event.get("time", {}).get("extra") or 0)
        if elapsed >= minimum_minute and not threshold_checked:
            if favorite_is_losing():
                first_clock = (minimum_minute, 0)
            threshold_checked = True
        team_id = str(event.get("team", {}).get("id", ""))
        if team_id == home_team_id:
            home_score += 1
        elif team_id == away_team_id:
            away_score += 1
        if elapsed >= minimum_minute and first_clock is None and favorite_is_losing():
            first_clock = (elapsed, extra)

    if not threshold_checked and favorite_is_losing():
        first_clock = (minimum_minute, 0)
    reconciled = home_score == final_home_score and away_score == final_away_score
    return ScenarioExposure(
        fixture_id=fixture_id,
        favorite_team_id=favorite_team_id,
        score_reconciled=reconciled,
        scenario_ever_active=(first_clock is not None) if reconciled else None,
        first_active_minute=first_clock[0] if reconciled and first_clock else None,
        first_active_minute_extra=first_clock[1] if reconciled and first_clock else None,
    )
