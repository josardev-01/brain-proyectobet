from __future__ import annotations

from datetime import datetime
from statistics import median
from typing import Any, Mapping, Sequence

from brain_projectbet.domain.models import MatchSnapshot, PrematchOdds


def _stat_map(statistics: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {str(item.get("type")): item.get("value") for item in statistics}


def _number(value: Any) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, str) and value.endswith("%"):
        value = value[:-1]
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


def normalize_snapshot(
    fixture: Mapping[str, Any],
    team_statistics: Sequence[Mapping[str, Any]],
    *,
    captured_at: datetime,
) -> MatchSnapshot:
    fixture_data = fixture["fixture"]
    teams = fixture["teams"]
    goals = fixture.get("goals", {})
    by_team_id = {
        str(entry["team"]["id"]): _stat_map(entry.get("statistics", []))
        for entry in team_statistics
    }
    home_id = str(teams["home"]["id"])
    away_id = str(teams["away"]["id"])
    home_stats = by_team_id.get(home_id, {})
    away_stats = by_team_id.get(away_id, {})

    return MatchSnapshot(
        provider="api-football",
        provider_match_id=str(fixture_data["id"]),
        captured_at=captured_at,
        minute=_number(fixture_data.get("status", {}).get("elapsed")),
        status=str(fixture_data.get("status", {}).get("short", "UNKNOWN")),
        minute_extra=_number(fixture_data.get("status", {}).get("extra")),
        home_team_id=home_id,
        away_team_id=away_id,
        score_home=_number(goals.get("home")),
        score_away=_number(goals.get("away")),
        shots_home=_number(home_stats.get("Total Shots")),
        shots_away=_number(away_stats.get("Total Shots")),
        shots_on_target_home=_number(home_stats.get("Shots on Goal")),
        shots_on_target_away=_number(away_stats.get("Shots on Goal")),
        dangerous_attacks_home=_number(home_stats.get("Dangerous Attacks")),
        dangerous_attacks_away=_number(away_stats.get("Dangerous Attacks")),
        corners_home=_number(home_stats.get("Corner Kicks")),
        corners_away=_number(away_stats.get("Corner Kicks")),
        possession_home=_number(home_stats.get("Ball Possession")),
        possession_away=_number(away_stats.get("Ball Possession")),
        xg_home=_number(home_stats.get("expected_goals")),
        xg_away=_number(away_stats.get("expected_goals")),
        red_cards_home=_number(home_stats.get("Red Cards")),
        red_cards_away=_number(away_stats.get("Red Cards")),
        raw_metadata={"league": fixture.get("league"), "team_names": teams},
    )


def extract_match_winner_odds(
    odds_response: Mapping[str, Any],
    *,
    fixture_id: str,
    bookmaker_name: str,
    captured_at: datetime,
) -> PrematchOdds:
    for entry in odds_response.get("response", []):
        for bookmaker in entry.get("bookmakers", []):
            if bookmaker.get("name") != bookmaker_name:
                continue
            for bet in bookmaker.get("bets", []):
                if bet.get("name") != "Match Winner":
                    continue
                values = {item["value"]: float(item["odd"]) for item in bet.get("values", [])}
                try:
                    return PrematchOdds(
                        provider="api-football",
                        provider_match_id=fixture_id,
                        captured_at=captured_at,
                        home=values["Home"],
                        draw=values["Draw"],
                        away=values["Away"],
                    )
                except KeyError as error:
                    raise ValueError("mercado Match Winner incompleto") from error
    raise ValueError(f"no se encontró Match Winner para {bookmaker_name}")


def extract_consensus_match_winner_odds(
    odds_response: Mapping[str, Any],
    *,
    fixture_id: str,
    captured_at: datetime,
    minimum_bookmakers: int = 3,
) -> tuple[PrematchOdds, int]:
    markets: list[dict[str, float]] = []
    for entry in odds_response.get("response", []):
        entry_fixture_id = str(entry.get("fixture", {}).get("id", fixture_id))
        if entry_fixture_id != str(fixture_id):
            continue
        for bookmaker in entry.get("bookmakers", []):
            for bet in bookmaker.get("bets", []):
                if bet.get("name") != "Match Winner":
                    continue
                values = {
                    item["value"]: float(item["odd"])
                    for item in bet.get("values", [])
                }
                if {"Home", "Draw", "Away"}.issubset(values):
                    markets.append(values)
    if len(markets) < minimum_bookmakers:
        raise ValueError(
            f"se requieren {minimum_bookmakers} bookmakers completos; disponibles: {len(markets)}"
        )
    return PrematchOdds(
        provider="api-football-consensus",
        provider_match_id=fixture_id,
        captured_at=captured_at,
        home=median(market["Home"] for market in markets),
        draw=median(market["Draw"] for market in markets),
        away=median(market["Away"] for market in markets),
    ), len(markets)
