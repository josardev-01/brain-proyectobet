import unittest
from datetime import UTC, datetime, timedelta

from brain_projectbet.domain.models import MatchSnapshot
from brain_projectbet.rules.expression import InvalidExpression
from brain_projectbet.rules.runtime import evaluate_strategy_config


def snapshot(minute: int, **overrides) -> MatchSnapshot:
    values = {
        "provider": "test", "provider_match_id": "1",
        "captured_at": datetime(2026, 9, 7, 15, tzinfo=UTC) + timedelta(minutes=minute),
        "minute": minute, "status": "2H", "score_home": 0, "score_away": 1,
        "shots_home": 2, "shots_away": 3,
        "shots_on_target_home": 0, "shots_on_target_away": 1,
        "corners_home": 1, "corners_away": 1,
    }
    values.update(overrides)
    return MatchSnapshot(**values)


class RuleRuntimeTests(unittest.TestCase):
    def test_builds_favorite_window_metrics_and_evaluates(self) -> None:
        config = {
            "strategy_id": "dynamic", "version": 1, "feature_window_minutes": 10,
            "conditions": [
                {"metric": "favorite_is_losing", "operator": "=", "value": True},
                {"metric": "favorite_shots_on_target_last_10", "operator": ">=", "value": 2},
            ],
        }
        result = evaluate_strategy_config(config, [
            snapshot(50),
            snapshot(60, shots_home=6, shots_on_target_home=2, corners_home=3),
        ], favorite_side="home")
        self.assertTrue(result.matched)
        self.assertEqual(result.metrics["favorite_shots_last_10"], 4)
        self.assertTrue(result.metrics["window_complete"])

    def test_missing_window_metric_fails_closed(self) -> None:
        config = {
            "conditions": [
                {"metric": "favorite_corners_last_10", "operator": ">=", "value": 1},
            ]
        }
        result = evaluate_strategy_config(config, [snapshot(50)], favorite_side="home")
        self.assertFalse(result.matched)
        self.assertEqual(result.missing_metrics, ("favorite_corners_last_10",))

    def test_requires_snapshots_and_conditions(self) -> None:
        with self.assertRaises(InvalidExpression):
            evaluate_strategy_config({"conditions": []}, [], favorite_side="home")


if __name__ == "__main__":
    unittest.main()
