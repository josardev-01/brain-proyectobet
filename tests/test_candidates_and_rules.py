import unittest
from datetime import UTC, datetime

from brain_projectbet.collection.series import WindowFeatures
from brain_projectbet.domain.candidates import observe_candidate
from brain_projectbet.domain.models import MatchSnapshot, PrematchOdds
from brain_projectbet.domain.objectives import FAVORITE_GOAL_WITHIN_10M_V1
from brain_projectbet.rules.favorite_pressure import evaluate_favorite_pressure


def snapshot(*, minute=45, extra=None, home_score=1, away_score=0, away_red=0):
    return MatchSnapshot(
        provider="api-football",
        provider_match_id="1556663",
        captured_at=datetime.now(UTC),
        minute=minute,
        minute_extra=extra,
        status="2H",
        home_team_id="251",
        away_team_id="247",
        score_home=home_score,
        score_away=away_score,
        red_cards_home=0,
        red_cards_away=away_red,
    )


def odds(away=1.42):
    return PrematchOdds(
        provider="api-football",
        provider_match_id="1556663",
        captured_at=datetime.now(UTC),
        home=7.0,
        draw=4.75,
        away=away,
    )


def window(*, shots=4, shots_on_target=1, corners=2):
    return WindowFeatures(
        provider_match_id="1556663",
        from_minute=80,
        to_minute=90,
        requested_window_minutes=10,
        actual_window_minutes=10,
        deltas={
            "shots_home": 0,
            "shots_away": shots,
            "shots_on_target_home": 0,
            "shots_on_target_away": shots_on_target,
            "dangerous_attacks_home": None,
            "dangerous_attacks_away": None,
            "corners_home": 0,
            "corners_away": corners,
            "xg_home": None,
            "xg_away": None,
        },
    )


class CandidateTests(unittest.TestCase):
    def test_clear_favorite_losing_from_minute_45_is_active(self) -> None:
        candidate = observe_candidate(snapshot(), odds(), FAVORITE_GOAL_WITHIN_10M_V1)
        self.assertTrue(candidate.eligible_prematch)
        self.assertTrue(candidate.episode_active)
        self.assertEqual(candidate.favorite_team_id, "247")

    def test_candidate_remains_active_in_stoppage_time(self) -> None:
        candidate = observe_candidate(
            snapshot(minute=90, extra=6), odds(), FAVORITE_GOAL_WITHIN_10M_V1
        )
        self.assertTrue(candidate.episode_active)
        self.assertIn(":90+6", candidate.candidate_id)

    def test_minute_44_is_not_active(self) -> None:
        candidate = observe_candidate(
            snapshot(minute=44), odds(), FAVORITE_GOAL_WITHIN_10M_V1
        )
        self.assertFalse(candidate.episode_active)

    def test_favorite_above_odds_threshold_is_not_eligible(self) -> None:
        candidate = observe_candidate(snapshot(), odds(away=1.60), FAVORITE_GOAL_WITHIN_10M_V1)
        self.assertFalse(candidate.eligible_prematch)
        self.assertFalse(candidate.episode_active)

    def test_finished_match_does_not_create_live_candidate(self) -> None:
        current = snapshot()
        finished = MatchSnapshot(
            **{
                field: getattr(current, field)
                for field in current.__dataclass_fields__
                if field != "status"
            },
            status="FT",
        )
        self.assertIsNone(
            observe_candidate(finished, odds(), FAVORITE_GOAL_WITHIN_10M_V1)
        )


class FavoritePressureRuleTests(unittest.TestCase):
    def test_alerts_with_shots_and_corners_branch(self) -> None:
        current = snapshot(minute=90, extra=6)
        candidate = observe_candidate(current, odds(), FAVORITE_GOAL_WITHIN_10M_V1)
        decision = evaluate_favorite_pressure(candidate, current, window())
        self.assertTrue(decision.should_alert)
        self.assertEqual(decision.status, "HEURÍSTICA")

    def test_alerts_with_shots_on_target_branch(self) -> None:
        current = snapshot()
        candidate = observe_candidate(current, odds(), FAVORITE_GOAL_WITHIN_10M_V1)
        decision = evaluate_favorite_pressure(
            candidate, current, window(shots=1, shots_on_target=2, corners=0)
        )
        self.assertTrue(decision.should_alert)

    def test_does_not_alert_without_full_window(self) -> None:
        current = snapshot()
        candidate = observe_candidate(current, odds(), FAVORITE_GOAL_WITHIN_10M_V1)
        decision = evaluate_favorite_pressure(candidate, current, None)
        self.assertFalse(decision.should_alert)
        self.assertIn("insufficient_window_history", decision.reasons)

    def test_does_not_alert_when_favorite_has_red_card_disadvantage(self) -> None:
        current = snapshot(away_red=1)
        candidate = observe_candidate(current, odds(), FAVORITE_GOAL_WITHIN_10M_V1)
        decision = evaluate_favorite_pressure(candidate, current, window())
        self.assertFalse(decision.should_alert)
        self.assertIn("favorite_has_red_card_disadvantage", decision.reasons)


if __name__ == "__main__":
    unittest.main()
