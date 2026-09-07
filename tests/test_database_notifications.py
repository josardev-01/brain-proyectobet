import tempfile
import unittest
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import sessionmaker

from brain_projectbet.database.models import AlertRecord, NotificationEndpointRecord, UserRecord
from brain_projectbet.database.session import Base, build_engine
from brain_projectbet.domain.alerts import AlertEvent
from brain_projectbet.notifications.delivery import deliver_pending_alerts


class RecordingNotifier:
    channel = "telegram"

    def __init__(self, sent):
        self.sent = sent

    def send(self, alert):
        self.sent.append(alert.alert_id)


class DatabaseNotificationTests(unittest.TestCase):
    def test_delivery_is_deduplicated_per_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = build_engine(f"sqlite:///{(Path(directory) / 'test.db').as_posix()}")
            Base.metadata.create_all(engine)
            sessions = sessionmaker(bind=engine, expire_on_commit=False)
            now = datetime.now(UTC)
            alert = AlertEvent(
                alert_id="alert-1", candidate_id="candidate-1", fixture_id="7",
                favorite_team_id="10", rule_id="pressure", rule_version=1,
                created_at=now, minute=60, minute_extra=None,
                score_favorite=0, score_opponent=1,
            )
            payload = asdict(alert)
            payload["created_at"] = now.isoformat()
            with sessions.begin() as session:
                user = UserRecord(email="test@example.com", display_name="Test", active=True, created_at=now)
                session.add(user)
                session.flush()
                session.add(NotificationEndpointRecord(
                    owner_id=user.id, channel="telegram", destination="123", label="Test",
                    enabled=True, created_at=now,
                ))
                session.add(AlertRecord(
                    alert_id=alert.alert_id, fixture_id="7", strategy_key="pressure",
                    strategy_version=1, created_at=now, minute=60,
                    favorite_team_name="Favorite", score_favorite=0, score_opponent=1,
                    explanation=payload,
                ))
            sent = []
            factory = lambda token, destination: RecordingNotifier(sent)
            with sessions() as session:
                first = deliver_pending_alerts(
                    session, telegram_token="secret", notifier_factory=factory
                )
                second = deliver_pending_alerts(
                    session, telegram_token="secret", notifier_factory=factory
                )
            self.assertEqual(first["sent"], 1)
            self.assertEqual(second["sent"], 0)
            self.assertEqual(sent, ["alert-1"])
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
