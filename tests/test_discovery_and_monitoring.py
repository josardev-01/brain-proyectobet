import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from brain_projectbet.collection.storage import append_alert_once
from brain_projectbet.discovery.eligible import discover_eligible_fixtures
from brain_projectbet.discovery.storage import load_eligible_fixtures, save_eligible_fixtures
from brain_projectbet.domain.alerts import AlertEvent, trigger_once_alert_id
from brain_projectbet.domain.candidates import CandidateObservation
from brain_projectbet.monitoring.selection import needs_statistics_sample, select_live_eligible


def bookmaker(name, home, draw, away):
    return {"name": name, "bets": [{"name": "Match Winner", "values": [
        {"value": "Home", "odd": str(home)},
        {"value": "Draw", "odd": str(draw)},
        {"value": "Away", "odd": str(away)},
    ]}]}


def odds_entry(fixture_id="10", away_odds=(1.42, 1.45, 1.40)):
    return {
        "fixture": {"id": int(fixture_id), "date": "2026-09-06T18:00:00-03:00"},
        "league": {"id": 1, "name": "Test League", "country": "Test"},
        "bookmakers": [
            bookmaker("A", 7.0, 4.5, away_odds[0]),
            bookmaker("B", 6.8, 4.6, away_odds[1]),
            bookmaker("C", 7.2, 4.4, away_odds[2]),
        ],
    }


class DiscoveryTests(unittest.TestCase):
    def test_discovers_clear_favorite_from_consensus(self) -> None:
        result = discover_eligible_fixtures(
            [{"response": [odds_entry()]}], discovered_at=datetime.now(UTC)
        )
        self.assertEqual(len(result.eligible), 1)
        self.assertEqual(result.eligible[0].favorite_side, "away")
        self.assertEqual(result.eligible[0].bookmaker_count, 3)

    def test_outlier_does_not_move_median_past_threshold(self) -> None:
        result = discover_eligible_fixtures(
            [{"response": [odds_entry(away_odds=(1.40, 1.45, 9.0))]}],
            discovered_at=datetime.now(UTC),
        )
        self.assertEqual(result.eligible[0].median_away_odds, 1.45)

    def test_registry_round_trip(self) -> None:
        result = discover_eligible_fixtures(
            [{"response": [odds_entry()]}], discovered_at=datetime.now(UTC)
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "eligible.json"
            save_eligible_fixtures(path, result.eligible)
            restored = load_eligible_fixtures(path)
        self.assertEqual(restored[0].fixture_id, "10")
        self.assertIsNotNone(restored[0].kickoff_at.tzinfo)


class MonitoringSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.eligible = list(discover_eligible_fixtures(
            [{"response": [odds_entry()]}], discovered_at=datetime.now(UTC)
        ).eligible)

    def test_selects_only_registered_fixture_after_warmup(self) -> None:
        live = {"response": [
            {"fixture": {"id": 10, "status": {"elapsed": 35}}},
            {"fixture": {"id": 99, "status": {"elapsed": 70}}},
        ]}
        selected = select_live_eligible(live, self.eligible)
        self.assertEqual([item[0].fixture_id for item in selected], ["10"])

    def test_does_not_select_before_warmup(self) -> None:
        live = {"response": [{"fixture": {"id": 10, "status": {"elapsed": 34}}}]}
        self.assertEqual(select_live_eligible(live, self.eligible), [])

    def test_collects_baseline_once_before_candidate_activation(self) -> None:
        registered = self.eligible[0]
        fixture = {
            "fixture": {"id": 10, "status": {"elapsed": 35}},
            "goals": {"home": 0, "away": 0},
        }
        self.assertTrue(needs_statistics_sample(registered, fixture, has_snapshots=False))
        self.assertFalse(needs_statistics_sample(registered, fixture, has_snapshots=True))

    def test_collects_after_45_only_when_favorite_is_losing(self) -> None:
        registered = self.eligible[0]
        losing = {
            "fixture": {"id": 10, "status": {"elapsed": 50}},
            "goals": {"home": 1, "away": 0},
        }
        winning = {
            "fixture": {"id": 10, "status": {"elapsed": 50}},
            "goals": {"home": 0, "away": 1},
        }
        self.assertTrue(needs_statistics_sample(registered, losing, has_snapshots=True))
        self.assertFalse(needs_statistics_sample(registered, winning, has_snapshots=True))

    def test_alert_storage_deduplicates(self) -> None:
        alert = AlertEvent(
            alert_id="alert-1",
            candidate_id="candidate-1",
            fixture_id="10",
            favorite_team_id="2",
            rule_id="favorite_losing_pressure",
            rule_version=2,
            created_at=datetime.now(UTC),
            minute=90,
            minute_extra=4,
            score_favorite=0,
            score_opponent=1,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "alerts.jsonl"
            self.assertTrue(append_alert_once(path, alert))
            self.assertFalse(append_alert_once(path, alert))
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 1)

    def test_alert_identity_does_not_change_with_observation_minute(self) -> None:
        observed_at = datetime.now(UTC)
        base = {
            "fixture_id": "10",
            "objective_id": "favorite_goal_within_10m",
            "objective_version": 1,
            "observed_at": observed_at,
            "minute_extra": None,
            "favorite_team_id": "2",
            "favorite_side": "away",
            "favorite_odds": 1.45,
            "favorite_probability": 0.66,
            "score_favorite": 0,
            "score_opponent": 1,
            "eligible_prematch": True,
            "episode_active": True,
        }
        minute_70 = CandidateObservation(candidate_id="candidate:70", minute=70, **base)
        minute_71 = CandidateObservation(candidate_id="candidate:71", minute=71, **base)
        first = trigger_once_alert_id(
            minute_70, rule_id="favorite_losing_pressure", rule_version=2
        )
        second = trigger_once_alert_id(
            minute_71, rule_id="favorite_losing_pressure", rule_version=2
        )
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
