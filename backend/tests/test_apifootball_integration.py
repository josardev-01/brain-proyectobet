import unittest
from datetime import UTC, datetime

from brain_projectbet.discovery.eligible import EligibleFixture
from brain_projectbet.monitoring.reconciliation import (
    canonical_team_name,
    reconcile_apifootball_live,
)
from brain_projectbet.normalization.apifootball_com import normalize_snapshot


def eligible(fixture_id="10", home="Atlético FC", away="Cerro Largo"):
    now = datetime(2026, 9, 10, tzinfo=UTC)
    return EligibleFixture(
        provider="api-football", fixture_id=fixture_id, kickoff_at=now,
        league_id="1", league_name="Test", country="PY", favorite_side="home",
        median_home_odds=1.4, median_draw_odds=4.0, median_away_odds=7.0,
        favorite_probability=.65, bookmaker_count=3, discovered_at=now,
        home_team_name=home, away_team_name=away,
    )


def live(match_id="900", home="Atletico", away="Cerro Largo"):
    return {
        "match_id": match_id,
        "match_status": "90+3",
        "match_hometeam_id": "44",
        "match_awayteam_id": "55",
        "match_hometeam_name": home,
        "match_awayteam_name": away,
        "match_hometeam_score": "1",
        "match_awayteam_score": "2",
        "statistics": [
            {"type": "On Target", "home": "4", "away": "2"},
            {"type": "Off Target", "home": "6", "away": "3"},
            {"type": "Corners", "home": "7", "away": "1"},
            {"type": "Dangerous Attacks", "home": "30", "away": "15"},
            {"type": "Ball Possession", "home": "63%", "away": "37%"},
        ],
    }


class ApiFootballComNormalizationTests(unittest.TestCase):
    def test_normalizes_clock_scores_and_embedded_statistics(self) -> None:
        snapshot = normalize_snapshot(
            live(), captured_at=datetime.now(UTC),
            canonical_provider="api-football", canonical_match_id="10",
        )
        self.assertEqual((snapshot.minute, snapshot.minute_extra), (90, 3))
        self.assertEqual(snapshot.status, "2H")
        self.assertEqual(snapshot.provider_match_id, "10")
        self.assertEqual(snapshot.shots_home, 10)
        self.assertEqual(snapshot.shots_on_target_away, 2)
        self.assertEqual(snapshot.possession_home, 63)
        self.assertEqual(snapshot.raw_metadata["source_match_id"], "900")

    def test_maps_half_time_to_observable_minute_45(self) -> None:
        item = live()
        item["match_status"] = "Half Time"
        snapshot = normalize_snapshot(item, captured_at=datetime.now(UTC))
        self.assertEqual(snapshot.status, "HT")
        self.assertEqual(snapshot.minute, 45)


class ProviderReconciliationTests(unittest.TestCase):
    def test_canonicalizes_accents_and_club_suffixes(self) -> None:
        self.assertEqual(canonical_team_name("Atlético F.C."), "atletico")

    def test_links_same_ordered_teams_across_provider_ids(self) -> None:
        result = reconcile_apifootball_live(
            [eligible()], {"response": [live()]}
        )
        self.assertEqual(len(result.links), 1)
        self.assertEqual(result.links[0].live_fixture["match_id"], "900")
        self.assertEqual(result.unmatched_fixture_ids, ())

    def test_missing_names_fail_closed(self) -> None:
        result = reconcile_apifootball_live(
            [eligible(home="", away="")], {"response": [live()]}
        )
        self.assertEqual(result.links, ())
        self.assertEqual(result.unmatched_fixture_ids, ("10",))

    def test_rejects_ambiguous_candidates(self) -> None:
        result = reconcile_apifootball_live(
            [eligible()], {"response": [live("900"), live("901")]}
        )
        self.assertEqual(result.links, ())
        self.assertEqual(result.ambiguous_fixture_ids, ("10",))


if __name__ == "__main__":
    unittest.main()
