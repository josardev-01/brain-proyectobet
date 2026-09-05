from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class TargetEvent:
    """Evento observable que permitirá etiquetar triggers y hacer backtesting."""

    event_type: str
    horizon_minutes: int
    subject: str = "match"
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_type.strip():
            raise ValueError("event_type no puede estar vacío")
        if self.horizon_minutes <= 0:
            raise ValueError("horizon_minutes debe ser mayor que cero")
        if not self.subject.strip():
            raise ValueError("subject no puede estar vacío")


@dataclass(frozen=True, slots=True)
class ObjectiveDefinition:
    """Objetivo versionado; no contiene umbrales del motor de señales."""

    objective_id: str
    version: int
    target: TargetEvent
    preconditions: Mapping[str, Any] = field(default_factory=dict)
    status: str = "HEURÍSTICA"

    def __post_init__(self) -> None:
        if not self.objective_id.strip():
            raise ValueError("objective_id no puede estar vacío")
        if self.version <= 0:
            raise ValueError("version debe ser mayor que cero")
        if self.status not in {"HEURÍSTICA", "EXPERIMENTAL", "VALIDADA"}:
            raise ValueError("status estadístico no reconocido")


FAVORITE_GOAL_WITHIN_10M_V1 = ObjectiveDefinition(
    objective_id="favorite_goal_within_10m",
    version=1,
    target=TargetEvent(
        event_type="goal",
        subject="prematch_favorite",
        horizon_minutes=10,
    ),
    preconditions={"prematch_favorite_is_losing": True},
    status="HEURÍSTICA",
)
