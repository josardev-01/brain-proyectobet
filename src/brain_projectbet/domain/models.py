from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class MatchSnapshot:
    """Estado normalizado disponible en un instante real del partido."""

    provider: str
    provider_match_id: str
    captured_at: datetime
    minute: int | None
    status: str
    home_team_id: str | None = None
    away_team_id: str | None = None
    score_home: int | None = None
    score_away: int | None = None
    shots_home: int | None = None
    shots_away: int | None = None
    shots_on_target_home: int | None = None
    shots_on_target_away: int | None = None
    dangerous_attacks_home: int | None = None
    dangerous_attacks_away: int | None = None
    corners_home: int | None = None
    corners_away: int | None = None
    possession_home: float | None = None
    possession_away: float | None = None
    xg_home: float | None = None
    xg_away: float | None = None
    raw_metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class PrematchOdds:
    provider: str
    provider_match_id: str
    captured_at: datetime
    home: float
    draw: float
    away: float

    def normalized_probabilities(self) -> tuple[float, float, float]:
        odds = (self.home, self.draw, self.away)
        if any(value <= 1 for value in odds):
            raise ValueError("las odds decimales deben ser mayores que 1")
        raw = tuple(1 / value for value in odds)
        total = sum(raw)
        return tuple(value / total for value in raw)

    def favorite_side(self) -> str:
        home_probability, _, away_probability = self.normalized_probabilities()
        return "home" if home_probability >= away_probability else "away"
