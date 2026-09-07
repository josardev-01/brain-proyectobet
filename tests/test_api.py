import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from brain_projectbet.api.main import create_app
from brain_projectbet.database.models import MatchRecord
from brain_projectbet.database.session import Base, build_engine, get_db


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        database = Path(self.directory.name) / "test.db"
        self.engine = build_engine(f"sqlite:///{database.as_posix()}")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)
        app = create_app()

        def override_db():
            session = self.sessions()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.engine.dispose()
        self.directory.cleanup()

    def auth_headers(self) -> dict[str, str]:
        response = self.client.post("/api/v1/auth/register", json={
            "email": "owner@example.com",
            "display_name": "Owner",
            "password": "a-secure-password",
        })
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def test_health_and_empty_dashboard(self) -> None:
        self.assertEqual(self.client.get("/health").status_code, 200)
        dashboard = self.client.get("/api/v1/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.json()["matches"], 0)
        self.assertIsNone(dashboard.json()["precision"])

    def test_lists_matches(self) -> None:
        with self.sessions.begin() as session:
            session.add(MatchRecord(
                provider="test",
                provider_match_id="42",
                kickoff_at=datetime.now(UTC),
                league_id="1",
                league_name="Liga Test",
                country="PY",
                favorite_side="home",
                favorite_odds=1.4,
                favorite_probability=0.68,
                bookmaker_count=3,
                discovered_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ))
        response = self.client.get("/api/v1/matches")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["provider_match_id"], "42")

    def test_strategy_versions_are_immutable(self) -> None:
        payload = {
            "strategy_key": "corner_pressure",
            "version": 1,
            "name": "Corner pressure",
            "objective_type": "corner",
            "objective_subject": "home",
            "horizon_minutes": 10,
            "config": {"strategy_id": "corner_pressure", "version": 1},
        }
        headers = self.auth_headers()
        self.assertEqual(self.client.post("/api/v1/strategies", json=payload, headers=headers).status_code, 201)
        self.assertEqual(self.client.post("/api/v1/strategies", json=payload, headers=headers).status_code, 409)

    def test_rejects_mismatched_strategy_config(self) -> None:
        payload = {
            "strategy_key": "corner_pressure",
            "version": 2,
            "name": "Corner pressure",
            "objective_type": "corner",
            "objective_subject": "home",
            "horizon_minutes": 10,
            "config": {"strategy_id": "other", "version": 2},
        }
        self.assertEqual(self.client.post("/api/v1/strategies", json=payload, headers=self.auth_headers()).status_code, 422)

    def test_evaluates_declarative_rule(self) -> None:
        response = self.client.post("/api/v1/rules/evaluate", json={
            "expression": {"metric": "corners_last_10", "operator": ">=", "value": 2},
            "metrics": {"corners_last_10": 3},
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["matched"])

    def test_register_login_and_current_user(self) -> None:
        headers = self.auth_headers()
        current = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(current.status_code, 200)
        self.assertEqual(current.json()["email"], "owner@example.com")
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 200)
        login = self.client.post("/api/v1/auth/login", json={
            "email": "owner@example.com", "password": "a-secure-password",
        })
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/logout").status_code, 204)
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)

    def test_strategy_write_requires_authentication(self) -> None:
        response = self.client.post("/api/v1/strategies", json={})
        self.assertIn(response.status_code, (401, 422))

    def test_manages_owned_notification_endpoint(self) -> None:
        self.auth_headers()
        created = self.client.post("/api/v1/notification-endpoints", json={
            "channel": "telegram", "destination": "-123456", "label": "Principal",
        })
        self.assertEqual(created.status_code, 201)
        endpoint_id = created.json()["id"]
        listed = self.client.get("/api/v1/notification-endpoints")
        self.assertEqual(listed.json()[0]["destination"], "-123456")
        disabled = self.client.patch(
            f"/api/v1/notification-endpoints/{endpoint_id}/activation?enabled=false"
        )
        self.assertFalse(disabled.json()["enabled"])
        self.assertEqual(
            self.client.delete(f"/api/v1/notification-endpoints/{endpoint_id}").status_code,
            204,
        )


if __name__ == "__main__":
    unittest.main()
