import unittest
from datetime import UTC, datetime

from brain_projectbet.discovery.eligible import EligibleFixture
from brain_projectbet.orchestration.planner import action_at, build_matchday_plan


def fixture(fixture_id: str, hour: int) -> EligibleFixture:
    return EligibleFixture(
        provider="api-football",
        fixture_id=fixture_id,
        kickoff_at=datetime(2026, 9, 7, hour, tzinfo=UTC),
        league_id="1",
        league_name="Test",
        country="Test",
        favorite_side="home",
        median_home_odds=1.3,
        median_draw_odds=5.0,
        median_away_odds=8.0,
        favorite_probability=0.7,
        bookmaker_count=3,
        discovered_at=datetime(2026, 9, 6, tzinfo=UTC),
    )


class MatchdayPlannerTests(unittest.TestCase):
    def test_merges_overlapping_windows(self) -> None:
        plan = build_matchday_plan([
            fixture("a", 14), fixture("b", 16), fixture("d", 16), fixture("c", 23)
        ])
        self.assertEqual(len(plan.windows), 3)
        self.assertEqual(plan.windows[0].fixture_ids, ("a",))
        self.assertEqual(plan.windows[1].fixture_ids, ("b", "d"))
        self.assertEqual(plan.windows[0].starts_at, datetime(2026, 9, 7, 14, 35, tzinfo=UTC))
        self.assertEqual(plan.windows[0].ends_at, datetime(2026, 9, 7, 16, 30, tzinfo=UTC))
        self.assertEqual(plan.finalize_at, datetime(2026, 9, 8, 2, tzinfo=UTC))

    def test_reports_wait_monitor_and_finalize(self) -> None:
        plan = build_matchday_plan([fixture("a", 14)])
        self.assertEqual(action_at(plan, datetime(2026, 9, 7, 14, tzinfo=UTC))[0], "wait")
        self.assertEqual(action_at(plan, datetime(2026, 9, 7, 15, tzinfo=UTC))[0], "monitor")
        self.assertEqual(action_at(plan, datetime(2026, 9, 7, 17, 30, tzinfo=UTC))[0], "finalize")

    def test_empty_plan_is_complete(self) -> None:
        plan = build_matchday_plan([])
        self.assertEqual(action_at(plan, datetime.now(UTC))[0], "complete")

    def test_rejects_finalization_before_monitoring_ends(self) -> None:
        with self.assertRaises(ValueError):
            build_matchday_plan(
                [fixture("a", 14)],
                monitor_after_kickoff_minutes=150,
                finalize_after_kickoff_minutes=120,
            )


if __name__ == "__main__":
    unittest.main()
