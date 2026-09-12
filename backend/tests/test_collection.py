import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from brain_projectbet.collection.series import derive_window
from brain_projectbet.collection.storage import append_snapshot, load_snapshots
from brain_projectbet.domain.models import MatchSnapshot


def snapshot(minute: int, shots: int, *, shots_on_target: int | None = None) -> MatchSnapshot:
    return MatchSnapshot(
        provider="test",
        provider_match_id="fixture-1",
        captured_at=datetime(2026, 9, 5, 12, tzinfo=UTC) + timedelta(minutes=minute),
        minute=minute,
        status="2H",
        shots_home=shots,
        shots_on_target_home=shots_on_target,
    )


class WindowTests(unittest.TestCase):
    def test_derives_accumulated_metric_delta(self) -> None:
        result = derive_window(
            [snapshot(50, 4, shots_on_target=1), snapshot(60, 9, shots_on_target=3)],
            window_minutes=10,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.deltas["shots_home"], 5)
        self.assertEqual(result.deltas["shots_on_target_home"], 2)

    def test_requires_enough_history(self) -> None:
        result = derive_window([snapshot(55, 4), snapshot(60, 7)], window_minutes=10)
        self.assertIsNone(result)

    def test_provider_correction_is_not_treated_as_negative_activity(self) -> None:
        result = derive_window([snapshot(50, 8), snapshot(60, 7)], window_minutes=10)
        self.assertIsNone(result.deltas["shots_home"])

    def test_jsonl_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshots.jsonl"
            append_snapshot(path, snapshot(50, 4))
            append_snapshot(path, snapshot(51, 5))
            restored = load_snapshots(path)
        self.assertEqual([item.shots_home for item in restored], [4, 5])
        self.assertEqual(restored[0].captured_at.tzinfo, UTC)


if __name__ == "__main__":
    unittest.main()
