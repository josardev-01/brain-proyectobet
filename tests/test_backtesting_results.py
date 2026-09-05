import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from brain_projectbet.backtesting.results import BacktestRecord, summarize_backtests
from brain_projectbet.backtesting.storage import append_backtest_once, load_backtests


def record(fixture_id, *, alert=True, outcome=True, snapshots=3, active=1):
    return BacktestRecord(
        record_id=f"record-{fixture_id}",
        fixture_id=fixture_id,
        league_id="1",
        league_name="League",
        favorite_side="home",
        favorite_odds=1.4,
        favorite_probability=0.68,
        objective_id="favorite_goal_within_10m",
        objective_version=1,
        rule_id="favorite_losing_pressure",
        rule_version=2,
        rule_status="HEURÍSTICA",
        match_status="FT",
        finalized_at=datetime.now(UTC),
        snapshots_read=snapshots,
        active_candidate_observations=active,
        alert_triggered=alert,
        trigger_minute=60 if alert else None,
        trigger_minute_extra=None,
        outcome=outcome if alert else None,
        censored_reason=None,
    )


class BacktestResultTests(unittest.TestCase):
    def test_storage_deduplicates_and_round_trips(self) -> None:
        item = record("10")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.jsonl"
            self.assertTrue(append_backtest_once(path, item))
            self.assertFalse(append_backtest_once(path, item))
            restored = load_backtests(path)
        self.assertEqual(restored, [item])

    def test_summary_calculates_precision_only_from_resolved_alerts(self) -> None:
        records = [
            record("1", outcome=True),
            record("2", outcome=False),
            record("3", outcome=None),
            record("4", alert=False, outcome=None, active=0),
        ]
        summary = summarize_backtests(records)
        self.assertEqual(summary.alerts, 3)
        self.assertEqual(summary.resolved_alerts, 2)
        self.assertEqual(summary.censored_or_unresolved_alerts, 1)
        self.assertEqual(summary.precision, 0.5)
        self.assertIsNone(summary.recall)
        self.assertIsNone(summary.f1)
        self.assertIsNone(summary.lift)


if __name__ == "__main__":
    unittest.main()
