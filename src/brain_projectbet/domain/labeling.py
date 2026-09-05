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


def label_goal_objective(
    objective: ObjectiveDefinition,
    *,
    trigger_minute: int,
    subject_team_id: str,
    events: Iterable[Mapping[str, Any]],
    observed_until_minute: int,
) -> ObjectiveLabel:
    if objective.target.event_type != "goal":
        raise ValueError("este etiquetador solo admite objetivos de gol")
    horizon_end = trigger_minute + objective.target.horizon_minutes
    if observed_until_minute < horizon_end:
        outcome = None
    else:
        outcome = any(
            event.get("type") == "Goal"
            and str(event.get("team", {}).get("id")) == subject_team_id
            and trigger_minute < int(event.get("time", {}).get("elapsed", -1)) <= horizon_end
            for event in events
        )
    return ObjectiveLabel(
        objective_id=objective.objective_id,
        objective_version=objective.version,
        trigger_minute=trigger_minute,
        observable_until_minute=horizon_end,
        outcome=outcome,
    )
