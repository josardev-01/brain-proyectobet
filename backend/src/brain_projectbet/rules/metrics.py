from __future__ import annotations

from typing import Any

from brain_projectbet.collection.series import WindowFeatures
from brain_projectbet.domain.models import MatchSnapshot


def build_rule_metrics(
    snapshot: MatchSnapshot,
    window: WindowFeatures | None,
    *,
    favorite_side: str,
) -> dict[str, Any]:
    if favorite_side not in {"home", "away"}:
        raise ValueError("favorite_side debe ser home o away")
    opponent_side = "away" if favorite_side == "home" else "home"
    favorite_score = getattr(snapshot, f"score_{favorite_side}")
    opponent_score = getattr(snapshot, f"score_{opponent_side}")
    metrics: dict[str, Any] = {
        "minute": snapshot.minute,
        "minute_extra": snapshot.minute_extra,
        "match_status": snapshot.status,
        "score_home": snapshot.score_home,
        "score_away": snapshot.score_away,
        "home_is_losing": (
            snapshot.score_home < snapshot.score_away
            if snapshot.score_home is not None and snapshot.score_away is not None
            else None
        ),
        "away_is_losing": (
            snapshot.score_away < snapshot.score_home
            if snapshot.score_home is not None and snapshot.score_away is not None
            else None
        ),
        "score_difference_home": (
            snapshot.score_home - snapshot.score_away
            if snapshot.score_home is not None and snapshot.score_away is not None
            else None
        ),
        "score_difference_away": (
            snapshot.score_away - snapshot.score_home
            if snapshot.score_home is not None and snapshot.score_away is not None
            else None
        ),
        "favorite_score": favorite_score,
        "opponent_score": opponent_score,
        "score_difference": (
            favorite_score - opponent_score
            if favorite_score is not None and opponent_score is not None
            else None
        ),
        "favorite_is_losing": (
            favorite_score < opponent_score
            if favorite_score is not None and opponent_score is not None
            else None
        ),
        "favorite_shots": getattr(snapshot, f"shots_{favorite_side}"),
        "opponent_shots": getattr(snapshot, f"shots_{opponent_side}"),
        "favorite_shots_on_target": getattr(snapshot, f"shots_on_target_{favorite_side}"),
        "opponent_shots_on_target": getattr(snapshot, f"shots_on_target_{opponent_side}"),
        "favorite_shots_off_target": getattr(snapshot, f"shots_off_target_{favorite_side}"),
        "opponent_shots_off_target": getattr(snapshot, f"shots_off_target_{opponent_side}"),
        "favorite_attacks": getattr(snapshot, f"attacks_{favorite_side}"),
        "opponent_attacks": getattr(snapshot, f"attacks_{opponent_side}"),
        "favorite_dangerous_attacks": getattr(snapshot, f"dangerous_attacks_{favorite_side}"),
        "opponent_dangerous_attacks": getattr(snapshot, f"dangerous_attacks_{opponent_side}"),
        "favorite_corners": getattr(snapshot, f"corners_{favorite_side}"),
        "opponent_corners": getattr(snapshot, f"corners_{opponent_side}"),
        "favorite_possession": getattr(snapshot, f"possession_{favorite_side}"),
        "opponent_possession": getattr(snapshot, f"possession_{opponent_side}"),
        "favorite_red_cards": getattr(snapshot, f"red_cards_{favorite_side}"),
        "opponent_red_cards": getattr(snapshot, f"red_cards_{opponent_side}"),
        "favorite_yellow_cards": getattr(snapshot, f"yellow_cards_{favorite_side}"),
        "opponent_yellow_cards": getattr(snapshot, f"yellow_cards_{opponent_side}"),
    }
    for metric in (
        "shots", "shots_on_target", "shots_off_target", "attacks",
        "dangerous_attacks", "corners", "possession", "xg",
        "yellow_cards", "red_cards",
    ):
        for side in ("home", "away"):
            metrics[f"{metric}_{side}"] = getattr(snapshot, f"{metric}_{side}")
    if window is None:
        metrics["window_complete"] = False
        return metrics
    suffix = f"last_{window.requested_window_minutes}"
    metrics["window_complete"] = window.actual_window_minutes == window.requested_window_minutes
    for metric in (
        "shots", "shots_on_target", "shots_off_target", "attacks",
        "dangerous_attacks", "corners", "xg"
    ):
        metrics[f"{metric}_home_{suffix}"] = window.deltas.get(f"{metric}_home")
        metrics[f"{metric}_away_{suffix}"] = window.deltas.get(f"{metric}_away")
        metrics[f"favorite_{metric}_{suffix}"] = window.deltas.get(f"{metric}_{favorite_side}")
        metrics[f"opponent_{metric}_{suffix}"] = window.deltas.get(f"{metric}_{opponent_side}")
    return metrics
