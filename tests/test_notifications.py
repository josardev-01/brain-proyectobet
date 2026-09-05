import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from brain_projectbet.domain.alerts import AlertEvent
from brain_projectbet.notifications.storage import (
    DeliveryReceipt,
    append_receipt_once,
    delivered_ids,
    delivery_id,
)
from brain_projectbet.notifications.telegram import TelegramNotifier, format_telegram_alert


def alert():
    return AlertEvent(
        alert_id="alert-1",
        candidate_id="candidate-1",
        fixture_id="10",
        favorite_team_id="2",
        rule_id="favorite_losing_pressure",
        rule_version=2,
        created_at=datetime.now(UTC),
        minute=68,
        minute_extra=None,
        score_favorite=0,
        score_opponent=1,
        home_team_name="Manchester X",
        away_team_name="Team Y",
        favorite_team_name="Manchester X",
        favorite_odds=1.45,
        favorite_probability=0.67,
        shots_10m=6,
        shots_on_target_10m=3,
        corners_10m=2,
    )


class NotificationTests(unittest.TestCase):
    def test_formats_explainable_message(self) -> None:
        message = format_telegram_alert(alert())
        self.assertIn("Manchester X vs Team Y", message)
        self.assertIn("Cuota pre-partido: 1.45", message)
        self.assertIn("A puerta: 3", message)
        self.assertIn("HEURÍSTICA", message)

    def test_telegram_uses_injected_transport(self) -> None:
        calls = []

        def fake_post(url, payload, timeout):
            calls.append((url, payload, timeout))
            return {"ok": True}

        notifier = TelegramNotifier("secret", "123", post_json=fake_post)
        notifier.send(alert())
        self.assertEqual(calls[0][1]["chat_id"], "123")
        self.assertNotIn("secret", calls[0][1]["text"])

    def test_receipt_prevents_duplicate_delivery(self) -> None:
        identifier = delivery_id("alert-1", "telegram", "123")
        receipt = DeliveryReceipt(identifier, "alert-1", "telegram", datetime.now(UTC))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipts.jsonl"
            self.assertTrue(append_receipt_once(path, receipt))
            self.assertFalse(append_receipt_once(path, receipt))
            self.assertEqual(delivered_ids(path), {identifier})

    def test_transport_error_does_not_expose_bot_token(self) -> None:
        def failing_post(url, payload, timeout):
            raise OSError(url)

        notifier = TelegramNotifier("super-secret", "123", post_json=failing_post)
        with self.assertRaises(RuntimeError) as caught:
            notifier.send(alert())
        self.assertNotIn("super-secret", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
