from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from brain_projectbet.backtesting.storage import load_backtests
from brain_projectbet.collection.storage import load_alerts, load_snapshots
from brain_projectbet.database.models import (
    AlertRecord,
    BacktestRecordModel,
    MatchRecord,
    SnapshotRecord,
    StrategyRecord,
)
from brain_projectbet.discovery.storage import load_eligible_fixtures


def _favorite_odds(fixture) -> float:
    return fixture.median_home_odds if fixture.favorite_side == "home" else fixture.median_away_odds


def _jsonable(value) -> dict:
    return json.loads(json.dumps(asdict(value), default=lambda item: item.isoformat()))


def _timestamp_key(value: datetime) -> datetime:
    """Normaliza SQLite (naive) y PostgreSQL (aware) a la misma identidad UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def sync_registry(session: Session, registry: Path) -> dict[str, int]:
    created_matches = created_snapshots = 0
    for fixture in load_eligible_fixtures(registry):
        match = session.scalar(select(MatchRecord).where(
            MatchRecord.provider == fixture.provider,
            MatchRecord.provider_match_id == fixture.fixture_id,
        ))
        if match is None:
            match = MatchRecord(
                provider=fixture.provider,
                provider_match_id=fixture.fixture_id,
                kickoff_at=fixture.kickoff_at,
                league_id=fixture.league_id,
                league_name=fixture.league_name,
                country=fixture.country,
                favorite_side=fixture.favorite_side,
                favorite_odds=_favorite_odds(fixture),
                favorite_probability=fixture.favorite_probability,
                bookmaker_count=fixture.bookmaker_count,
                discovered_at=fixture.discovered_at,
                updated_at=datetime.now(UTC),
            )
            session.add(match)
            session.flush()
            created_matches += 1

        snapshot_path = Path("data/raw/snapshots") / f"api-football-{fixture.fixture_id}.jsonl"
        existing_times = {
            _timestamp_key(value)
            for value in session.scalars(
                select(SnapshotRecord.captured_at).where(SnapshotRecord.match_id == match.id)
            )
        }
        for snapshot in load_snapshots(snapshot_path):
            captured_key = _timestamp_key(snapshot.captured_at)
            if captured_key in existing_times:
                continue
            session.add(SnapshotRecord(
                match_id=match.id,
                captured_at=snapshot.captured_at,
                minute=snapshot.minute,
                minute_extra=snapshot.minute_extra,
                status=snapshot.status,
                score_home=snapshot.score_home,
                score_away=snapshot.score_away,
                shots_home=snapshot.shots_home,
                shots_away=snapshot.shots_away,
                shots_on_target_home=snapshot.shots_on_target_home,
                shots_on_target_away=snapshot.shots_on_target_away,
                corners_home=snapshot.corners_home,
                corners_away=snapshot.corners_away,
                possession_home=snapshot.possession_home,
                possession_away=snapshot.possession_away,
                xg_home=snapshot.xg_home,
                xg_away=snapshot.xg_away,
                red_cards_home=snapshot.red_cards_home,
                red_cards_away=snapshot.red_cards_away,
                raw_metadata=dict(snapshot.raw_metadata or {}),
            ))
            existing_times.add(captured_key)
            created_snapshots += 1
            match.status = snapshot.status
            match.score_home = snapshot.score_home
            match.score_away = snapshot.score_away
            match.updated_at = datetime.now(UTC)
            names = (snapshot.raw_metadata or {}).get("team_names", {})
            match.home_team_name = str(names.get("home", {}).get("name", match.home_team_name))
            match.away_team_name = str(names.get("away", {}).get("name", match.away_team_name))
    return {"matches": created_matches, "snapshots": created_snapshots}


def sync_strategies(session: Session, directory: Path = Path("config/strategies")) -> int:
    created = 0
    for path in directory.glob("*.json"):
        config = json.loads(path.read_text(encoding="utf-8"))
        existing = session.scalar(select(StrategyRecord).where(
            StrategyRecord.strategy_key == config["strategy_id"],
            StrategyRecord.version == config["version"],
        ))
        if existing is not None:
            continue
        target = config["objective"]["target"]
        session.add(StrategyRecord(
            strategy_key=config["strategy_id"],
            version=config["version"],
            name=config["strategy_id"].replace("_", " ").title(),
            statistical_status=config["status"],
            objective_type=target["event_type"],
            objective_subject=target["subject"],
            horizon_minutes=target["horizon_minutes"],
            config=config,
            active=True,
            created_at=datetime.now(UTC),
        ))
        created += 1
    return created


def sync_alerts(session: Session, path: Path = Path("data/raw/alerts.jsonl")) -> int:
    created = 0
    matches = {item.provider_match_id: item.id for item in session.scalars(select(MatchRecord))}
    for alert in load_alerts(path):
        if session.get(AlertRecord, alert.alert_id) is not None:
            continue
        session.add(AlertRecord(
            alert_id=alert.alert_id,
            match_id=matches.get(alert.fixture_id),
            fixture_id=alert.fixture_id,
            strategy_key=alert.rule_id,
            strategy_version=alert.rule_version,
            created_at=alert.created_at,
            minute=alert.minute,
            minute_extra=alert.minute_extra,
            favorite_team_name=alert.favorite_team_name,
            score_favorite=alert.score_favorite,
            score_opponent=alert.score_opponent,
            explanation=_jsonable(alert),
        ))
        created += 1
    return created


def sync_backtests(
    session: Session,
    path: Path = Path("data/raw/backtesting/results.jsonl"),
) -> int:
    created = 0
    for record in load_backtests(path):
        if session.get(BacktestRecordModel, record.record_id) is not None:
            continue
        session.add(BacktestRecordModel(
            record_id=record.record_id,
            fixture_id=record.fixture_id,
            strategy_key=record.rule_id,
            strategy_version=record.rule_version,
            rule_status=record.rule_status,
            finalized_at=record.finalized_at,
            alert_triggered=record.alert_triggered,
            outcome=record.outcome,
            censored_reason=record.censored_reason,
            payload=_jsonable(record),
        ))
        created += 1
    return created
