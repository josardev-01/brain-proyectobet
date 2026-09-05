from __future__ import annotations

from typing import Any, Mapping

from brain_projectbet.discovery.eligible import EligibleFixture


def select_live_eligible(
    live_payload: Mapping[str, Any],
    eligible: list[EligibleFixture],
    *,
    warmup_minute: int = 35,
    maximum_matches: int = 2,
) -> list[tuple[EligibleFixture, Mapping[str, Any]]]:
    eligible_by_id = {fixture.fixture_id: fixture for fixture in eligible}
    selected = []
    for fixture_payload in live_payload.get("response", []):
        fixture_id = str(fixture_payload.get("fixture", {}).get("id", ""))
        eligible_fixture = eligible_by_id.get(fixture_id)
        minute = fixture_payload.get("fixture", {}).get("status", {}).get("elapsed")
        if eligible_fixture is None or minute is None or int(minute) < warmup_minute:
            continue
        selected.append((eligible_fixture, fixture_payload))
    selected.sort(key=lambda item: int(item[1]["fixture"]["status"]["elapsed"]), reverse=True)
    return selected[:maximum_matches]


def needs_statistics_sample(
    registered: EligibleFixture,
    fixture_payload: Mapping[str, Any],
    *,
    has_snapshots: bool,
    minimum_minute: int = 45,
) -> bool:
    """Collect one baseline, then spend quota only while the episode is active."""
    if not has_snapshots:
        return True
    minute = fixture_payload.get("fixture", {}).get("status", {}).get("elapsed")
    if minute is None or int(minute) < minimum_minute:
        return False
    goals = fixture_payload.get("goals", {})
    favorite_key = "home" if registered.favorite_side == "home" else "away"
    opponent_key = "away" if registered.favorite_side == "home" else "home"
    favorite_score = goals.get(favorite_key)
    opponent_score = goals.get(opponent_key)
    if favorite_score is None or opponent_score is None:
        return False
    return int(favorite_score) < int(opponent_score)
