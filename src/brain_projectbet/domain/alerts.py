from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from brain_projectbet.domain.candidates import CandidateObservation


@dataclass(frozen=True, slots=True)
class AlertEvent:
    alert_id: str
    candidate_id: str
    fixture_id: str
    favorite_team_id: str
    rule_id: str
    rule_version: int
    created_at: datetime
    minute: int
    minute_extra: int | None
    score_favorite: int
    score_opponent: int


def trigger_once_alert_id(
    candidate: CandidateObservation,
    *,
    rule_id: str,
    rule_version: int,
) -> str:
    """Return a stable identity for one alert per objective episode and rule."""
    return (
        f"{candidate.fixture_id}:{candidate.objective_id}:v{candidate.objective_version}:"
        f"{rule_id}:v{rule_version}"
    )
