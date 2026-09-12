import unittest

from brain_projectbet.backtesting.exposure import audit_favorite_losing_exposure


def goal(minute, team_id, *, extra=None, detail="Normal Goal"):
    return {
        "type": "Goal",
        "detail": detail,
        "team": {"id": int(team_id)},
        "time": {"elapsed": minute, "extra": extra},
    }


def audit(events, final_home, final_away, *, favorite="1"):
    return audit_favorite_losing_exposure(
        fixture_id="10",
        home_team_id="1",
        away_team_id="2",
        favorite_team_id=favorite,
        final_home_score=final_home,
        final_away_score=final_away,
        events=events,
    )


class ScenarioExposureTests(unittest.TestCase):
    def test_detects_favorite_already_losing_at_minute_45(self) -> None:
        report = audit([goal(20, "2")], 0, 1)
        self.assertTrue(report.score_reconciled)
        self.assertTrue(report.scenario_ever_active)
        self.assertEqual(report.first_active_minute, 45)

    def test_detects_scenario_created_after_minute_45(self) -> None:
        report = audit([goal(60, "2")], 0, 1)
        self.assertTrue(report.scenario_ever_active)
        self.assertEqual(report.first_active_minute, 60)

    def test_favorite_never_losing_is_inactive(self) -> None:
        report = audit([goal(50, "1"), goal(70, "2")], 1, 1)
        self.assertFalse(report.scenario_ever_active)

    def test_missed_penalty_does_not_change_score(self) -> None:
        report = audit([goal(70, "2", detail="Missed Penalty")], 0, 0)
        self.assertFalse(report.scenario_ever_active)

    def test_score_mismatch_makes_exposure_unknown(self) -> None:
        report = audit([goal(60, "2")], 1, 1)
        self.assertFalse(report.score_reconciled)
        self.assertIsNone(report.scenario_ever_active)


if __name__ == "__main__":
    unittest.main()
