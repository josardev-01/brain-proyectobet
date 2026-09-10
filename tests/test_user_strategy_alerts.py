import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from brain_projectbet.database.models import AlertRecord, MatchRecord, SnapshotRecord, StrategyRecord, UserRecord
from brain_projectbet.database.session import Base, build_engine
from brain_projectbet.rules.strategy_alerts import evaluate_owned_strategy_alerts


class UserStrategyAlertTests(unittest.TestCase):
    def test_active_owned_strategy_creates_one_private_alert(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = build_engine(f"sqlite:///{(Path(directory) / 'strategy.db').as_posix()}")
            Base.metadata.create_all(engine)
            sessions = sessionmaker(bind=engine, expire_on_commit=False)
            now = datetime.now(UTC)
            with sessions.begin() as session:
                owner = UserRecord(
                    email="owner@example.com", display_name="Owner", active=True,
                    role="USER", approval_status="APPROVED", created_at=now,
                )
                session.add(owner)
                session.flush()
                match = MatchRecord(
                    provider="api-football", provider_match_id="77", kickoff_at=now,
                    league_id="1", league_name="Liga", country="PY",
                    home_team_name="Local", away_team_name="Visitante",
                    favorite_side="away", favorite_odds=1.50, favorite_probability=0.65,
                    home_odds=5.0, draw_odds=3.5, away_odds=1.5,
                    home_probability=0.18, draw_probability=0.17, away_probability=0.65,
                    bookmaker_count=3, status="2H", discovered_at=now, updated_at=now,
                )
                session.add(match)
                session.flush()
                session.add_all([
                    SnapshotRecord(
                        match_id=match.id, captured_at=now, minute=50, status="2H",
                        score_home=0, score_away=1, shots_home=2, shots_away=4,
                        shots_on_target_home=1, shots_on_target_away=2,
                    ),
                    SnapshotRecord(
                        match_id=match.id, captured_at=now + timedelta(minutes=10),
                        minute=60, status="2H", score_home=0, score_away=1,
                        shots_home=6, shots_away=5, shots_on_target_home=3,
                        shots_on_target_away=2,
                    ),
                ])
                session.add(StrategyRecord(
                    owner_id=owner.id, strategy_key="local_shots", version=1,
                    name="Tiros del local", statistical_status="HEURÍSTICA",
                    objective_type="goal", objective_subject="home", horizon_minutes=10,
                    config={
                        "strategy_id": "local_shots", "version": 1,
                        "feature_window_minutes": 10,
                        "conditions": [{
                            "metric": "shots_home_last_10", "operator": ">=", "value": 4,
                        }],
                        "alert_fields": ["score", "shots"],
                    },
                    active=True, created_at=now,
                ))

            with sessions.begin() as session:
                first = evaluate_owned_strategy_alerts(session)
            with sessions.begin() as session:
                second = evaluate_owned_strategy_alerts(session)
                alert = session.scalar(select(AlertRecord))

            self.assertEqual(first["created"], 1)
            self.assertEqual(second["created"], 0)
            self.assertEqual(alert.owner_id, owner.id)
            self.assertEqual(alert.explanation["strategy_name"], "Tiros del local")
            self.assertEqual(alert.explanation["metrics"]["shots_home_last_10"], 4)
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
