import unittest
from datetime import UTC, datetime

from brain_projectbet.domain.models import PrematchOdds
from brain_projectbet.domain.objectives import FAVORITE_GOAL_WITHIN_10M_V1, TargetEvent


class TargetEventTests(unittest.TestCase):
    def test_initial_objective_is_specific_but_extensible(self) -> None:
        objective = FAVORITE_GOAL_WITHIN_10M_V1
        self.assertEqual(objective.target.event_type, "goal")
        self.assertEqual(objective.target.subject, "prematch_favorite")
        self.assertEqual(objective.target.horizon_minutes, 10)
        self.assertTrue(objective.preconditions["prematch_favorite_is_losing"])

    def test_other_targets_use_the_same_contract(self) -> None:
        target = TargetEvent(event_type="corner", subject="home", horizon_minutes=5)
        self.assertEqual(target.event_type, "corner")

    def test_horizon_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            TargetEvent(event_type="goal", horizon_minutes=0)


class PrematchOddsTests(unittest.TestCase):
    def test_probabilities_remove_overround_and_sum_to_one(self) -> None:
        odds = PrematchOdds(
            provider="test",
            provider_match_id="1",
            captured_at=datetime.now(UTC),
            home=1.80,
            draw=3.60,
            away=5.00,
        )
        probabilities = odds.normalized_probabilities()
        self.assertAlmostEqual(sum(probabilities), 1.0)
        self.assertEqual(odds.favorite_side(), "home")

    def test_invalid_decimal_odds_are_rejected(self) -> None:
        odds = PrematchOdds("test", "1", datetime.now(UTC), 1.0, 3.0, 4.0)
        with self.assertRaises(ValueError):
            odds.normalized_probabilities()


if __name__ == "__main__":
    unittest.main()
