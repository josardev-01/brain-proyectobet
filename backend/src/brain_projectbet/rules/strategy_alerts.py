from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from brain_projectbet.database.mappers import snapshot_record_to_domain
from brain_projectbet.database.models import AlertRecord, MatchRecord, SnapshotRecord, StrategyRecord, UserRecord
from brain_projectbet.domain.alerts import AlertEvent
from brain_projectbet.rules.expression import InvalidExpression
from brain_projectbet.rules.runtime import evaluate_strategy_config


LIVE_STATUSES = ("1H", "HT", "2H", "ET", "BT", "P", "LIVE")


def _alert_id(owner_id: int, match: MatchRecord, strategy: StrategyRecord) -> str:
    identity = (
        f"{owner_id}:{match.provider}:{match.provider_match_id}:"
        f"{strategy.strategy_key}:{strategy.version}"
    )
    return f"user-strategy:{owner_id}:{hashlib.sha256(identity.encode()).hexdigest()}"


def _jsonable_alert(alert: AlertEvent) -> dict:
    return json.loads(json.dumps(asdict(alert), default=lambda item: item.isoformat()))


def evaluate_owned_strategy_alerts(session: Session) -> dict[str, int]:
    """Evalúa estrategias activas y crea alertas privadas, una vez por partido y versión."""
    strategies = list(session.scalars(
        select(StrategyRecord)
        .join(UserRecord, StrategyRecord.owner_id == UserRecord.id)
        .where(
            StrategyRecord.active.is_(True),
            StrategyRecord.owner_id.is_not(None),
            UserRecord.active.is_(True),
            UserRecord.approval_status == "APPROVED",
        )
    ))
    matches = list(session.scalars(select(MatchRecord).where(MatchRecord.status.in_(LIVE_STATUSES))))
    evaluated = matched = created = invalid = 0
    for match in matches:
        records = list(session.scalars(
            select(SnapshotRecord)
            .where(SnapshotRecord.match_id == match.id)
            .order_by(SnapshotRecord.captured_at)
        ))
        if not records:
            continue
        snapshots = [snapshot_record_to_domain(match, record) for record in records]
        latest = snapshots[-1]
        context = {
            "home_odds": match.home_odds,
            "draw_odds": match.draw_odds,
            "away_odds": match.away_odds,
            "home_probability": match.home_probability,
            "draw_probability": match.draw_probability,
            "away_probability": match.away_probability,
            # Compatibilidad exclusiva con estrategias antiguas del caso inicial.
            "favorite_odds": match.favorite_odds,
            "favorite_probability": match.favorite_probability,
            "league_name": match.league_name,
            "country": match.country,
        }
        for strategy in strategies:
            evaluated += 1
            try:
                result = evaluate_strategy_config(
                    strategy.config,
                    snapshots,
                    favorite_side=match.favorite_side,
                    context=context,
                )
            except InvalidExpression:
                invalid += 1
                continue
            if not result.matched:
                continue
            matched += 1
            identifier = _alert_id(strategy.owner_id, match, strategy)
            if session.get(AlertRecord, identifier) is not None:
                continue
            favorite_is_home = match.favorite_side == "home"
            score_favorite = latest.score_home if favorite_is_home else latest.score_away
            score_opponent = latest.score_away if favorite_is_home else latest.score_home
            alert = AlertEvent(
                alert_id=identifier,
                candidate_id=f"user-strategy:{match.id}:{strategy.id}",
                fixture_id=match.provider_match_id,
                favorite_team_id="",
                rule_id=strategy.strategy_key,
                rule_version=strategy.version,
                created_at=datetime.now(UTC),
                minute=latest.minute or 0,
                minute_extra=latest.minute_extra,
                score_favorite=score_favorite or 0,
                score_opponent=score_opponent or 0,
                objective_id=strategy.objective_type,
                rule_status=strategy.statistical_status,
                home_team_name=match.home_team_name,
                away_team_name=match.away_team_name,
                favorite_team_name=(match.home_team_name if favorite_is_home else match.away_team_name),
                favorite_odds=match.favorite_odds,
                favorite_probability=match.favorite_probability,
                owner_id=strategy.owner_id,
                strategy_name=strategy.name,
                score_home=latest.score_home,
                score_away=latest.score_away,
                alert_fields=tuple(strategy.config.get("alert_fields", [])),
                metrics=result.metrics,
                reasons=result.reasons,
            )
            session.add(AlertRecord(
                alert_id=identifier,
                owner_id=strategy.owner_id,
                strategy_id=strategy.id,
                match_id=match.id,
                fixture_id=match.provider_match_id,
                strategy_key=strategy.strategy_key,
                strategy_version=strategy.version,
                created_at=alert.created_at,
                minute=alert.minute,
                minute_extra=alert.minute_extra,
                favorite_team_name=alert.favorite_team_name,
                score_favorite=alert.score_favorite,
                score_opponent=alert.score_opponent,
                explanation=_jsonable_alert(alert),
            ))
            created += 1
    return {"evaluated": evaluated, "matched": matched, "created": created, "invalid": invalid}
