import unittest
from datetime import UTC, datetime, timedelta

from brain_projectbet.backtesting.replay import replay_first_alert
from brain_projectbet.domain.models import MatchSnapshot, PrematchOdds
from brain_projectbet.domain.objectives import FAVORITE_GOAL_WITHIN_10M_V1


START = datetime(2026, 9, 5, 20, 0, tzinfo=UTC)


def snapshot(minute, *, shots, shots_on_target, corners, score_away=0, status="2H"):
    return MatchSnapshot(
        provider="api-football",
        provider_match_id="10",
        captured_at=START + timedelta(minutes=minute),
        minute=minute,
        status=status,
        home_team_id="1",
        away_team_id="2",
        score_home=1,
        score_away=score_away,
        shots_home=2,
        shots_away=shots,
        shots_on_target_home=1,
        shots_on_target_away=shots_on_target,
        corners_home=1,
        corners_away=corners,
        red_cards_home=0,
        red_cards_away=0,
    )


ODDS = PrematchOdds(
    provider="api-football-consensus",
    provider_match_id="10",
    captured_at=START,
    home=7.0,
    draw=4.5,
    away=1.42,
)


class ReplayTests(unittest.TestCase):
    def test_replays_first_alert_and_labels_future_goal(self) -> None:
        snapshots = [
            snapshot(45, shots=1, shots_on_target=0, corners=0),
            snapshot(55, shots=4, shots_on_target=2, corners=1),
            snapshot(65, shots=6, shots_on_target=3, corners=2, score_away=1),
        ]
        events = [{"type": "Goal", "team": {"id": 2}, "time": {"elapsed": 60}}]
        result = replay_first_alert(snapshots, ODDS, FAVORITE_GOAL_WITHIN_10M_V1, events)
        self.assertEqual(result.first_alert.trigger_minute, 55)
        self.assertTrue(result.first_alert.label.outcome)

    def test_rule_cannot_use_future_snapshot_to_build_window(self) -> None:
        snapshots = [
            snapshot(45, shots=1, shots_on_target=0, corners=0),
            snapshot(50, shots=1, shots_on_target=0, corners=0),
            snapshot(60, shots=4, shots_on_target=2, corners=1),
        ]
        result = replay_first_alert(snapshots, ODDS, FAVORITE_GOAL_WITHIN_10M_V1, [])
        self.assertEqual(result.first_alert.trigger_minute, 60)

    def test_returns_no_alert_when_pressure_never_meets_rule(self) -> None:
        snapshots = [
            snapshot(45, shots=1, shots_on_target=0, corners=0),
            snapshot(55, shots=2, shots_on_target=0, corners=0, status="FT"),
        ]
        result = replay_first_alert(snapshots, ODDS, FAVORITE_GOAL_WITHIN_10M_V1, [])
        self.assertIsNone(result.first_alert)


if __name__ == "__main__":
    unittest.main()
