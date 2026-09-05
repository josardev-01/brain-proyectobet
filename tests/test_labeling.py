import unittest

from brain_projectbet.domain.labeling import label_goal_objective
from brain_projectbet.domain.objectives import FAVORITE_GOAL_WITHIN_10M_V1


class LabelingTests(unittest.TestCase):
    def test_label_is_unknown_until_full_horizon_is_observed(self) -> None:
        label = label_goal_objective(
            FAVORITE_GOAL_WITHIN_10M_V1,
            trigger_minute=50,
            subject_team_id="2",
            events=[],
            observed_until_minute=59,
        )
        self.assertIsNone(label.outcome)

    def test_goal_by_subject_inside_horizon_is_positive(self) -> None:
        events = [{"type": "Goal", "team": {"id": 2}, "time": {"elapsed": 57}}]
        label = label_goal_objective(
            FAVORITE_GOAL_WITHIN_10M_V1,
            trigger_minute=50,
            subject_team_id="2",
            events=events,
            observed_until_minute=60,
        )
        self.assertTrue(label.outcome)

    def test_opponent_goal_does_not_satisfy_objective(self) -> None:
        events = [{"type": "Goal", "team": {"id": 1}, "time": {"elapsed": 57}}]
        label = label_goal_objective(
            FAVORITE_GOAL_WITHIN_10M_V1,
            trigger_minute=50,
            subject_team_id="2",
            events=events,
            observed_until_minute=60,
        )
        self.assertFalse(label.outcome)


if __name__ == "__main__":
    unittest.main()
