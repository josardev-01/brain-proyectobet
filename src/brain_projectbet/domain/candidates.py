from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from brain_projectbet.domain.models import MatchSnapshot, PrematchOdds
from brain_projectbet.domain.objectives import ObjectiveDefinition


TERMINAL_MATCH_STATUSES = {"FT", "AET", "PEN", "PST", "CANC", "ABD", "AWD", "WO"}


@dataclass(frozen=True, slots=True)
class CandidatePolicy:
    maximum_favorite_odds: float = 1.55
    minimum_favorite_probability: float = 0.60
    minimum_minute: int = 45
    warmup_minute: int = 35


@dataclass(frozen=True, slots=True)
class CandidateObservation:
    candidate_id: str
    fixture_id: str
    objective_id: str
    objective_version: int
    observed_at: datetime
    minute: int
    minute_extra: int | None
    favorite_team_id: str
    favorite_side: str
    favorite_odds: float
    favorite_probability: float
    score_favorite: int
    score_opponent: int
    eligible_prematch: bool
    episode_active: bool


def observe_candidate(
    snapshot: MatchSnapshot,
    odds: PrematchOdds,
    objective: ObjectiveDefinition,
    *,
    policy: CandidatePolicy = CandidatePolicy(),
) -> CandidateObservation | None:
    if snapshot.minute is None or snapshot.status in TERMINAL_MATCH_STATUSES:
        return None
    favorite_side = odds.favorite_side()
    favorite_team_id = (
        snapshot.home_team_id if favorite_side == "home" else snapshot.away_team_id
    )
    favorite_score = snapshot.score_home if favorite_side == "home" else snapshot.score_away
    opponent_score = snapshot.score_away if favorite_side == "home" else snapshot.score_home
    if favorite_team_id is None or favorite_score is None or opponent_score is None:
        return None
    probabilities = odds.normalized_probabilities()
    favorite_index = 0 if favorite_side == "home" else 2
    favorite_probability = probabilities[favorite_index]
    favorite_odds = odds.home if favorite_side == "home" else odds.away
    eligible_prematch = (
        favorite_odds <= policy.maximum_favorite_odds
        and favorite_probability >= policy.minimum_favorite_probability
    )
    episode_active = (
        eligible_prematch
        and snapshot.minute >= policy.minimum_minute
        and favorite_score < opponent_score
    )
    extra = snapshot.minute_extra or 0
    candidate_id = (
        f"{snapshot.provider}:{snapshot.provider_match_id}:"
        f"{objective.objective_id}:v{objective.version}:{snapshot.minute}+{extra}"
    )
    return CandidateObservation(
        candidate_id=candidate_id,
        fixture_id=snapshot.provider_match_id,
        objective_id=objective.objective_id,
        objective_version=objective.version,
        observed_at=snapshot.captured_at,
        minute=snapshot.minute,
        minute_extra=snapshot.minute_extra,
        favorite_team_id=favorite_team_id,
        favorite_side=favorite_side,
        favorite_odds=favorite_odds,
        favorite_probability=favorite_probability,
        score_favorite=favorite_score,
        score_opponent=opponent_score,
        eligible_prematch=eligible_prematch,
        episode_active=episode_active,
    )
