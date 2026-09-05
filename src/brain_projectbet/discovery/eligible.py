from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from brain_projectbet.domain.candidates import CandidatePolicy
from brain_projectbet.normalization.api_football import extract_consensus_match_winner_odds


@dataclass(frozen=True, slots=True)
class EligibleFixture:
    provider: str
    fixture_id: str
    kickoff_at: datetime
    league_id: str
    league_name: str
    country: str
    favorite_side: str
    median_home_odds: float
    median_draw_odds: float
    median_away_odds: float
    favorite_probability: float
    bookmaker_count: int
    discovered_at: datetime


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    eligible: tuple[EligibleFixture, ...]
    fixtures_evaluated: int
    skipped_incomplete_consensus: int


def discover_eligible_fixtures(
    payloads: list[Mapping[str, Any]],
    *,
    discovered_at: datetime,
    policy: CandidatePolicy = CandidatePolicy(),
) -> DiscoveryResult:
    eligible: list[EligibleFixture] = []
    evaluated = 0
    skipped = 0
    for payload in payloads:
        for entry in payload.get("response", []):
            evaluated += 1
            fixture_id = str(entry.get("fixture", {}).get("id", ""))
            if not fixture_id:
                skipped += 1
                continue
            try:
                odds, bookmaker_count = extract_consensus_match_winner_odds(
                    {"response": [entry]},
                    fixture_id=fixture_id,
                    captured_at=discovered_at,
                )
            except ValueError:
                skipped += 1
                continue
            side = odds.favorite_side()
            probabilities = odds.normalized_probabilities()
            favorite_probability = probabilities[0 if side == "home" else 2]
            favorite_odds = odds.home if side == "home" else odds.away
            if (
                favorite_odds > policy.maximum_favorite_odds
                or favorite_probability < policy.minimum_favorite_probability
            ):
                continue
            fixture = entry["fixture"]
            league = entry.get("league", {})
            eligible.append(EligibleFixture(
                provider="api-football",
                fixture_id=fixture_id,
                kickoff_at=datetime.fromisoformat(fixture["date"]),
                league_id=str(league.get("id", "")),
                league_name=str(league.get("name", "")),
                country=str(league.get("country", "")),
                favorite_side=side,
                median_home_odds=odds.home,
                median_draw_odds=odds.draw,
                median_away_odds=odds.away,
                favorite_probability=favorite_probability,
                bookmaker_count=bookmaker_count,
                discovered_at=discovered_at,
            ))
    unique = {fixture.fixture_id: fixture for fixture in eligible}
    return DiscoveryResult(
        eligible=tuple(sorted(unique.values(), key=lambda fixture: fixture.kickoff_at)),
        fixtures_evaluated=evaluated,
        skipped_incomplete_consensus=skipped,
    )
