from __future__ import annotations

from dataclasses import dataclass

from brain_projectbet.collection.series import WindowFeatures
from brain_projectbet.domain.candidates import CandidateObservation
from brain_projectbet.domain.models import MatchSnapshot


@dataclass(frozen=True, slots=True)
class FavoritePressurePolicy:
    version: int = 2
    status: str = "HEURÍSTICA"
    window_minutes: int = 10
    minimum_shots_on_target: int = 2
    minimum_combined_shots_on_target: int = 1
    minimum_shots: int = 3
    minimum_corners: int = 1


@dataclass(frozen=True, slots=True)
class AlertDecision:
    rule_id: str
    rule_version: int
    status: str
    should_alert: bool
    reasons: tuple[str, ...]


def evaluate_favorite_pressure(
    candidate: CandidateObservation,
    snapshot: MatchSnapshot,
    window: WindowFeatures | None,
    *,
    policy: FavoritePressurePolicy = FavoritePressurePolicy(),
) -> AlertDecision:
    reasons: list[str] = []
    if not candidate.episode_active:
        reasons.append("candidate_episode_inactive")
    if window is None or window.requested_window_minutes != policy.window_minutes:
        reasons.append("insufficient_window_history")

    favorite_suffix = "home" if candidate.favorite_side == "home" else "away"
    opponent_suffix = "away" if candidate.favorite_side == "home" else "home"
    favorite_red = getattr(snapshot, f"red_cards_{favorite_suffix}")
    opponent_red = getattr(snapshot, f"red_cards_{opponent_suffix}")
    if favorite_red is not None and opponent_red is not None and favorite_red > opponent_red:
        reasons.append("favorite_has_red_card_disadvantage")

    if window is not None:
        shots = window.deltas[f"shots_{favorite_suffix}"]
        shots_on_target = window.deltas[f"shots_on_target_{favorite_suffix}"]
        corners = window.deltas[f"corners_{favorite_suffix}"]
        opponent_shots = window.deltas[f"shots_{opponent_suffix}"]
        opponent_shots_on_target = window.deltas[f"shots_on_target_{opponent_suffix}"]
        pressure_met = (
            shots_on_target is not None
            and shots_on_target >= policy.minimum_shots_on_target
        ) or (
            shots_on_target is not None
            and shots_on_target >= policy.minimum_combined_shots_on_target
            and shots is not None
            and shots >= policy.minimum_shots
            and corners is not None
            and corners >= policy.minimum_corners
        )
        if not pressure_met:
            reasons.append("pressure_threshold_not_met")
        relative_dominance_met = (
            shots is not None
            and opponent_shots is not None
            and shots >= opponent_shots
            and shots_on_target is not None
            and opponent_shots_on_target is not None
            and shots_on_target >= opponent_shots_on_target
        )
        if not relative_dominance_met:
            reasons.append("favorite_not_dominant_in_window")

    return AlertDecision(
        rule_id="favorite_losing_pressure",
        rule_version=policy.version,
        status=policy.status,
        should_alert=not reasons,
        reasons=tuple(reasons),
    )
