import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from brain_projectbet.orchestration.finalization_state import (
    FinalizationState,
    load_finalization_state,
    save_finalization_state,
)


class FinalizationStateTests(unittest.TestCase):
    def test_cached_quota_fails_closed_at_reserve(self) -> None:
        state = FinalizationState(quota_date="2026-09-12", daily_remaining=15)

        self.assertFalse(state.can_spend(on_date="2026-09-12", requested=1, reserve=15))
        self.assertTrue(state.can_spend(on_date="2026-09-13", requested=1, reserve=15))

    def test_deferred_fixture_waits_until_retry_time(self) -> None:
        now = datetime(2026, 9, 12, 12, tzinfo=UTC)
        state = FinalizationState(deferred_until={"10": now + timedelta(hours=12)})

        self.assertFalse(state.can_check_fixture("10", now=now))
        self.assertTrue(state.can_check_fixture("10", now=now + timedelta(hours=12)))

    def test_state_round_trip(self) -> None:
        retry_at = datetime(2026, 9, 13, tzinfo=UTC)
        state = FinalizationState("2026-09-12", 7, {"10": retry_at})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            save_finalization_state(path, state)
            restored = load_finalization_state(path)

        self.assertEqual(restored.daily_remaining, 7)
        self.assertEqual(restored.deferred_until["10"], retry_at)


if __name__ == "__main__":
    unittest.main()
