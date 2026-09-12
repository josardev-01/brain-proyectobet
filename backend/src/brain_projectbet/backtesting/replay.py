from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from brain_projectbet.collection.series import derive_window
from brain_projectbet.domain.candidates import CandidatePolicy, TERMINAL_MATCH_STATUSES, observe_candidate
from brain_projectbet.domain.labeling import ObjectiveLabel, label_goal_objective
from brain_projectbet.domain.models import MatchSnapshot, PrematchOdds
from brain_projectbet.domain.objectives import ObjectiveDefinition
from brain_projectbet.rules.favorite_pressure import FavoritePressurePolicy, evaluate_favorite_pressure


@dataclass(frozen=True, slots=True)
class ReplayAlert:
    candidate_id: str
    fixture_id: str
    trigger_minute: int
    trigger_minute_extra: int | None
    rule_id: str
    rule_version: int
    label: ObjectiveLabel


@dataclass(frozen=True, slots=True)
class ReplayResult:
    fixture_id: str
    snapshots_read: int
    active_candidate_observations: int
    first_alert: ReplayAlert | None


def replay_first_alert(
    snapshots: Iterable[MatchSnapshot],
    odds: PrematchOdds,
    objective: ObjectiveDefinition,
    events: Iterable[Mapping[str, Any]],
    *,
    candidate_policy: CandidatePolicy = CandidatePolicy(),
    pressure_policy: FavoritePressurePolicy = FavoritePressurePolicy(),
) -> ReplayResult:
    """Replay chronologically and evaluate only information available at each instant."""
    ordered = sorted(
        (snapshot for snapshot in snapshots if snapshot.minute is not None),
        key=lambda snapshot: (snapshot.minute, snapshot.minute_extra or 0, snapshot.captured_at),
    )
    fixture_id = odds.provider_match_id
    if not ordered:
        return ReplayResult(fixture_id, 0, 0, None)

    active_count = 0
    observed_until = max(snapshot.minute for snapshot in ordered if snapshot.minute is not None)
    match_ended = ordered[-1].status in TERMINAL_MATCH_STATUSES
    event_list = list(events)

    for index, snapshot in enumerate(ordered):
        candidate = observe_candidate(snapshot, odds, objective, policy=candidate_policy)
        if candidate is None or not candidate.episode_active:
            continue
        active_count += 1
        window = derive_window(
            ordered[: index + 1],
            window_minutes=pressure_policy.window_minutes,
        )
        decision = evaluate_favorite_pressure(
            candidate,
            snapshot,
            window,
            policy=pressure_policy,
        )
        if not decision.should_alert:
            continue
        label = label_goal_objective(
            objective,
            trigger_minute=candidate.minute,
            trigger_minute_extra=candidate.minute_extra,
            subject_team_id=candidate.favorite_team_id,
            events=event_list,
            observed_until_minute=observed_until,
            match_ended=match_ended,
        )
        return ReplayResult(
            fixture_id=fixture_id,
            snapshots_read=len(ordered),
            active_candidate_observations=active_count,
            first_alert=ReplayAlert(
                candidate_id=candidate.candidate_id,
                fixture_id=candidate.fixture_id,
                trigger_minute=candidate.minute,
                trigger_minute_extra=candidate.minute_extra,
                rule_id=decision.rule_id,
                rule_version=decision.rule_version,
                label=label,
            ),
        )
    return ReplayResult(fixture_id, len(ordered), active_count, None)
