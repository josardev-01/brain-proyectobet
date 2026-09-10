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

    def test_owned_alert_is_only_delivered_to_its_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = build_engine(f"sqlite:///{(Path(directory) / 'private.db').as_posix()}")
            Base.metadata.create_all(engine)
            sessions = sessionmaker(bind=engine, expire_on_commit=False)
            now = datetime.now(UTC)
            alert = AlertEvent(
                alert_id="private-alert", candidate_id="candidate", fixture_id="9",
                favorite_team_id="", rule_id="owner_rule", rule_version=1,
                created_at=now, minute=55, minute_extra=None,
                score_favorite=0, score_opponent=0, owner_id=1,
            )
            payload = asdict(alert)
            payload["created_at"] = now.isoformat()
            with sessions.begin() as session:
                owner = UserRecord(email="owner@example.com", display_name="Owner", active=True, created_at=now)
                other = UserRecord(email="other@example.com", display_name="Other", active=True, created_at=now)
                session.add_all([owner, other])
                session.flush()
                session.add_all([
                    NotificationEndpointRecord(owner_id=owner.id, channel="telegram", destination="111", label="Owner", enabled=True, created_at=now),
                    NotificationEndpointRecord(owner_id=other.id, channel="telegram", destination="222", label="Other", enabled=True, created_at=now),
                ])
                session.add(AlertRecord(
                    alert_id=alert.alert_id, owner_id=owner.id, fixture_id="9",
                    strategy_key="owner_rule", strategy_version=1, created_at=now,
                    minute=55, favorite_team_name="", score_favorite=0, score_opponent=0,
                    explanation=payload,
                ))
            destinations = []

            def factory(token, destination):
                destinations.append(destination)
                return RecordingNotifier([])

            with sessions() as session:
                result = deliver_pending_alerts(
                    session, telegram_token="secret", notifier_factory=factory
                )
            self.assertEqual(result["sent"], 1)
            self.assertEqual(destinations, ["111"])
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
