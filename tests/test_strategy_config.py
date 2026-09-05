import json
import tempfile
import unittest
from pathlib import Path

from brain_projectbet.domain.candidates import CandidatePolicy
from brain_projectbet.rules.favorite_pressure import FavoritePressurePolicy
from brain_projectbet.strategies.config import DEFAULT_STRATEGY_PATH, load_strategy


class StrategyConfigTests(unittest.TestCase):
    def test_loads_default_versioned_strategy(self) -> None:
        strategy = load_strategy(DEFAULT_STRATEGY_PATH)
        self.assertEqual(strategy.strategy_id, "favorite_losing_pressure")
        self.assertEqual(strategy.version, 2)
        self.assertEqual(strategy.objective.objective_id, "favorite_goal_within_10m")
        self.assertEqual(strategy.candidate_policy.maximum_favorite_odds, 1.55)
        self.assertEqual(strategy.pressure_policy.rule_id, "favorite_losing_pressure")
        self.assertEqual(strategy.pressure_policy.window_minutes, 10)

    def test_rejects_unsupported_rule_type(self) -> None:
        payload = json.loads(DEFAULT_STRATEGY_PATH.read_text(encoding="utf-8"))
        payload["rule"]["type"] = "unknown"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "strategy.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "tipo de regla no soportado"):
                load_strategy(path)

    def test_rejects_invalid_candidate_timing(self) -> None:
        with self.assertRaisesRegex(ValueError, "warmup_minute"):
            CandidatePolicy(minimum_minute=45, warmup_minute=46)

    def test_rejects_invalid_pressure_status(self) -> None:
        with self.assertRaisesRegex(ValueError, "status"):
            FavoritePressurePolicy(status="INVENTADA")


if __name__ == "__main__":
    unittest.main()
