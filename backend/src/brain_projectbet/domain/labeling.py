from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from brain_projectbet.domain.objectives import ObjectiveDefinition


@dataclass(frozen=True, slots=True)
class ObjectiveLabel:
    objective_id: str
    objective_version: int
    trigger_minute: int
    observable_until_minute: int
    outcome: bool | None
    censored_reason: str | None = None


def label_goal_objective(
    objective: ObjectiveDefinition,
    *,
    trigger_minute: int,
    trigger_minute_extra: int | None = None,
    subject_team_id: str,
    events: Iterable[Mapping[str, Any]],
    observed_until_minute: int,
    match_ended: bool = False,
) -> ObjectiveLabel:
    if objective.target.event_type != "goal":
        raise ValueError("este etiquetador solo admite objetivos de gol")
    horizon_end = trigger_minute + objective.target.horizon_minutes
    trigger_extra = trigger_minute_extra or 0

    def minutes_after_trigger(event: Mapping[str, Any]) -> int | None:
        event_time = event.get("time", {})
        try:
            elapsed = int(event_time.get("elapsed", -1))
            extra = int(event_time.get("extra") or 0)
        except (TypeError, ValueError):
            return None
        if elapsed < trigger_minute:
            return None
        if elapsed == trigger_minute:
            return extra - trigger_extra
        return elapsed - trigger_minute

    goal_observed = False
    for event in events:
        distance = minutes_after_trigger(event)
        if (
            event.get("type") == "Goal"
            and str(event.get("team", {}).get("id")) == subject_team_id
            and distance is not None
            and 0 < distance <= objective.target.horizon_minutes
            and int(event.get("time", {}).get("elapsed", -1)) <= observed_until_minute
        ):
            goal_observed = True
            break
    censored_reason = None
    if goal_observed:
        outcome = True
    elif observed_until_minute >= horizon_end:
        outcome = False
    else:
        outcome = None
        if match_ended:
            censored_reason = "match_ended_before_horizon"
    return ObjectiveLabel(
        objective_id=objective.objective_id,
        objective_version=objective.version,
        trigger_minute=trigger_minute,
        observable_until_minute=horizon_end,
        outcome=outcome,
        censored_reason=censored_reason,
    )
