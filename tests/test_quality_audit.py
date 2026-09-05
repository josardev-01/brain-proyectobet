import unittest
from datetime import UTC, datetime, timedelta

from brain_projectbet.domain.models import MatchSnapshot
from brain_projectbet.quality.audit import audit_fixture, summarize_quality


START = datetime(2026, 9, 5, tzinfo=UTC)


def snapshot(minute, *, shots=1, xg=None, status="2H"):
    return MatchSnapshot(
        provider="api-football",
        provider_match_id="10",
        captured_at=START + timedelta(minutes=minute),
        minute=minute,
        status=status,
        shots_home=shots,
        shots_away=shots,
        xg_home=xg,
        xg_away=xg,
    )


class QualityAuditTests(unittest.TestCase):
    def test_detects_exact_window_gap_and_missing_metric(self) -> None:
        report = audit_fixture([
            snapshot(35, xg=None),
            snapshot(45, xg=0.4),
            snapshot(60, xg=None, status="FT"),
        ])
        self.assertTrue(report.exact_ten_minute_window_available)
        self.assertEqual(report.maximum_gap_minutes, 15)
        self.assertTrue(report.terminal_observed)
        self.assertEqual(report.metric_availability["shots_home"], 1.0)
        self.assertEqual(report.metric_availability["xg_home"], 0.3333)

    def test_counts_duplicate_match_clock_observations(self) -> None:
        report = audit_fixture([snapshot(45), snapshot(45), snapshot(55)])
        self.assertEqual(report.duplicate_clock_observations, 1)

    def test_aggregate_is_weighted_by_snapshots(self) -> None:
        first = [snapshot(35, xg=0.1), snapshot(45, xg=None)]
        second_item = snapshot(55, xg=0.2)
        second_item = MatchSnapshot(
            **{
                field: getattr(second_item, field)
                for field in second_item.__dataclass_fields__
                if field != "provider_match_id"
            },
            provider_match_id="20",
        )
        summary = summarize_quality([first, [second_item]])
        self.assertEqual(summary.fixtures, 2)
        self.assertEqual(summary.snapshots, 3)
        self.assertEqual(summary.weighted_metric_availability["xg_home"], 0.6667)

    def test_rejects_mixed_fixture_group(self) -> None:
        other = snapshot(45)
        other = MatchSnapshot(
            **{
                field: getattr(other, field)
                for field in other.__dataclass_fields__
                if field != "provider_match_id"
            },
            provider_match_id="20",
        )
        with self.assertRaisesRegex(ValueError, "mismo fixture"):
            audit_fixture([snapshot(35), other])


if __name__ == "__main__":
    unittest.main()
