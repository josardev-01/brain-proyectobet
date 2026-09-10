import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from brain_projectbet.collection.storage import append_snapshot
from brain_projectbet.database.models import MatchRecord, SnapshotRecord
from brain_projectbet.database.session import Base, build_engine
from brain_projectbet.database.sync import sync_registry
from brain_projectbet.discovery.eligible import EligibleFixture
from brain_projectbet.discovery.storage import save_eligible_fixtures
from brain_projectbet.domain.models import MatchSnapshot


class DatabaseSyncTests(unittest.TestCase):
    def test_sqlite_engine_creates_missing_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "nested" / "projectbet.db"

            engine = build_engine(f"sqlite:///{database_path.as_posix()}")
            try:
                Base.metadata.create_all(engine)
                self.assertTrue(database_path.is_file())
            finally:
                engine.dispose()

    def test_registry_and_snapshots_are_idempotent_on_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / "eligible.json"
            captured = datetime(2026, 9, 7, 15, tzinfo=UTC)
            save_eligible_fixtures(registry, (EligibleFixture(
                provider="api-football", fixture_id="7", kickoff_at=captured,
                league_id="1", league_name="Test", country="PY", favorite_side="home",
                median_home_odds=1.4, median_draw_odds=4.0, median_away_odds=7.0,
                favorite_probability=.65, bookmaker_count=3, discovered_at=captured,
                home_team_name="Home", away_team_name="Away",
            ),))
            snapshot_path = root / "data/raw/snapshots/api-football-7.jsonl"
            append_snapshot(snapshot_path, MatchSnapshot(
                provider="api-football", provider_match_id="7", captured_at=captured,
                minute=45, status="HT",
            ))
            engine = build_engine(f"sqlite:///{(root / 'test.db').as_posix()}")
            Base.metadata.create_all(engine)
            sessions = sessionmaker(bind=engine)
            def path_factory(value):
                return root / value if value == "data/raw/snapshots" else Path(value)

            with patch("brain_projectbet.database.sync.Path", side_effect=path_factory):
                with sessions.begin() as session:
                    sync_registry(session, registry)
                with sessions.begin() as session:
                    sync_registry(session, registry)
                    self.assertEqual(session.scalar(select(func.count()).select_from(MatchRecord)), 1)
                    self.assertEqual(session.scalar(select(func.count()).select_from(SnapshotRecord)), 1)
                    match = session.scalar(select(MatchRecord))
                    self.assertEqual((match.home_team_name, match.away_team_name), ("Home", "Away"))
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
