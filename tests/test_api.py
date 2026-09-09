import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from brain_projectbet.api.main import create_app
from brain_projectbet.core.security import hash_password
from brain_projectbet.database.models import MatchRecord, StrategyRecord, UserRecord
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
        self.client.post("/api/v1/auth/register", json={
            "email": "owner@example.com",
            "display_name": "Owner",
            "password": "a-secure-password",
        })
        with self.sessions.begin() as session:
            user = session.scalar(select(UserRecord).where(UserRecord.email == "owner@example.com"))
            user.approval_status = "APPROVED"
        response = self.client.post("/api/v1/auth/login", json={
            "email": "owner@example.com", "password": "a-secure-password",
        })
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def admin_headers(self) -> dict[str, str]:
        with self.sessions.begin() as session:
            session.add(UserRecord(
                email="admin@example.com",
                display_name="Admin",
                password_hash=hash_password("admin-password"),
                active=True,
                role="ADMIN",
                approval_status="APPROVED",
                created_at=datetime.now(UTC),
            ))
        response = self.client.post("/api/v1/auth/login", json={
            "email": "admin@example.com", "password": "admin-password",
        })
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def test_health_and_empty_dashboard(self) -> None:
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(
            self.client.get("/ready").json(),
            {"status": "ready", "database": "ok"},
        )
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

    def test_registration_stays_pending_until_admin_approval(self) -> None:
        registered = self.client.post("/api/v1/auth/register", json={
            "email": "candidate@example.com",
            "display_name": "Candidate",
            "password": "candidate-password",
        })
        self.assertEqual(registered.status_code, 201)
        self.assertEqual(registered.json()["status"], "PENDING")
        denied = self.client.post("/api/v1/auth/login", json={
            "email": "candidate@example.com", "password": "candidate-password",
        })
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(denied.json()["detail"], "cuenta pendiente de aprobación")

        headers = self.admin_headers()
        pending = self.client.get("/api/v1/admin/users", headers=headers)
        self.assertEqual(pending.status_code, 200)
        candidate = next(user for user in pending.json() if user["email"] == "candidate@example.com")
        approved = self.client.patch(
            f"/api/v1/admin/users/{candidate['id']}/approval",
            headers=headers,
            json={"approval_status": "APPROVED"},
        )
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.json()["reviewed_by_id"], 2)
        login = self.client.post("/api/v1/auth/login", json={
            "email": "candidate@example.com", "password": "candidate-password",
        })
        self.assertEqual(login.status_code, 200)

    def test_regular_user_cannot_review_accounts(self) -> None:
        response = self.client.get("/api/v1/admin/users", headers=self.auth_headers())
        self.assertEqual(response.status_code, 403)

    def test_strategy_write_requires_authentication(self) -> None:
        response = self.client.post("/api/v1/strategies", json={})
        self.assertIn(response.status_code, (401, 422))

    def test_regular_user_cannot_modify_system_strategy(self) -> None:
        with self.sessions.begin() as session:
            strategy = StrategyRecord(
                owner_id=None,
                strategy_key="system_strategy",
                version=1,
                name="System strategy",
                objective_type="goal",
                objective_subject="favorite",
                horizon_minutes=10,
                config={"strategy_id": "system_strategy", "version": 1},
                active=True,
                created_at=datetime.now(UTC),
            )
            session.add(strategy)
            session.flush()
            strategy_id = strategy.id
        response = self.client.patch(
            f"/api/v1/strategies/{strategy_id}/activation?active=false",
            headers=self.auth_headers(),
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_modify_system_strategy(self) -> None:
        with self.sessions.begin() as session:
            strategy = StrategyRecord(
                owner_id=None,
                strategy_key="system_strategy",
                version=1,
                name="System strategy",
                objective_type="goal",
                objective_subject="favorite",
                horizon_minutes=10,
                config={"strategy_id": "system_strategy", "version": 1},
                active=True,
                created_at=datetime.now(UTC),
            )
            session.add(strategy)
            session.flush()
            strategy_id = strategy.id
        response = self.client.patch(
            f"/api/v1/strategies/{strategy_id}/activation?active=false",
            headers=self.admin_headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["active"])

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
