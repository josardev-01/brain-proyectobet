import unittest
from datetime import UTC, datetime

from brain_projectbet.normalization.api_football import (
    extract_consensus_match_winner_odds,
    extract_match_winner_odds,
    normalize_snapshot,
)


class ApiFootballNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime.now(UTC)
        self.fixture = {
            "fixture": {"id": 1556663, "status": {"elapsed": 42, "short": "1H"}},
            "league": {"name": "Premiership", "country": "Scotland"},
            "teams": {
                "home": {"id": 1, "name": "ST Mirren"},
                "away": {"id": 2, "name": "Celtic"},
            },
            "goals": {"home": 1, "away": 0},
        }
        self.statistics = [
            {"team": {"id": 1}, "statistics": [
                {"type": "Total Shots", "value": 7},
                {"type": "Shots on Goal", "value": 1},
                {"type": "Corner Kicks", "value": 3},
                {"type": "Ball Possession", "value": "32%"},
            ]},
            {"team": {"id": 2}, "statistics": [
                {"type": "Total Shots", "value": 8},
                {"type": "Shots on Goal", "value": 3},
                {"type": "Corner Kicks", "value": 6},
                {"type": "Ball Possession", "value": "68%"},
            ]},
        ]

    def test_normalizes_snapshot_and_preserves_missing_values(self) -> None:
        snapshot = normalize_snapshot(self.fixture, self.statistics, captured_at=self.now)
        self.assertEqual(snapshot.provider_match_id, "1556663")
        self.assertEqual(snapshot.score_home, 1)
        self.assertEqual(snapshot.shots_on_target_away, 3)
        self.assertEqual(snapshot.possession_away, 68)
        self.assertIsNone(snapshot.dangerous_attacks_away)
        self.assertIsNone(snapshot.xg_away)

    def test_extracts_match_winner_for_selected_bookmaker(self) -> None:
        payload = {"response": [{"bookmakers": [{
            "name": "Bet365",
            "bets": [{"name": "Match Winner", "values": [
                {"value": "Home", "odd": "7.00"},
                {"value": "Draw", "odd": "4.75"},
                {"value": "Away", "odd": "1.42"},
            ]}],
        }]}]}
        odds = extract_match_winner_odds(
            payload,
            fixture_id="1556663",
            bookmaker_name="Bet365",
            captured_at=self.now,
        )
        self.assertEqual(odds.favorite_side(), "away")
        self.assertAlmostEqual(odds.normalized_probabilities()[2], 0.6659, places=4)

    def test_builds_median_consensus_from_complete_bookmakers(self) -> None:
        def bookmaker(name, home, draw, away):
            return {"name": name, "bets": [{"name": "Match Winner", "values": [
                {"value": "Home", "odd": str(home)},
                {"value": "Draw", "odd": str(draw)},
                {"value": "Away", "odd": str(away)},
            ]}]}

        payload = {"response": [{"bookmakers": [
            bookmaker("A", 7.0, 4.75, 1.42),
            bookmaker("B", 6.0, 4.60, 1.44),
            bookmaker("C", 6.8, 4.85, 1.39),
        ]}]}
        consensus, count = extract_consensus_match_winner_odds(
            payload, fixture_id="1556663", captured_at=self.now
        )
        self.assertEqual(count, 3)
        self.assertEqual(consensus.home, 6.8)
        self.assertEqual(consensus.draw, 4.75)
        self.assertEqual(consensus.away, 1.42)


if __name__ == "__main__":
    unittest.main()
