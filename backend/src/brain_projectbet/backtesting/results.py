from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from brain_projectbet.backtesting.replay import ReplayResult
from brain_projectbet.discovery.eligible import EligibleFixture


@dataclass(frozen=True, slots=True)
class BacktestRecord:
    record_id: str
    fixture_id: str
    league_id: str
    league_name: str
    favorite_side: str
    favorite_odds: float
    favorite_probability: float
    objective_id: str
    objective_version: int
    rule_id: str
    rule_version: int
    rule_status: str
    match_status: str
    finalized_at: datetime
    snapshots_read: int
    active_candidate_observations: int
    alert_triggered: bool
    trigger_minute: int | None
    trigger_minute_extra: int | None
    outcome: bool | None
    censored_reason: str | None


@dataclass(frozen=True, slots=True)
class BacktestSummary:
    records: int
    fixtures_with_history: int
    fixtures_with_active_candidate: int
    alerts: int
    resolved_alerts: int
    positive_alerts: int
    negative_alerts: int
    censored_or_unresolved_alerts: int
    precision: float | None
    recall: None = None
    f1: None = None
    lift: None = None
    status: str = "EXPERIMENTAL"


def backtest_record_id(
    *,
    provider: str,
    fixture_id: str,
    objective_id: str,
    objective_version: int,
    rule_id: str,
    rule_version: int,
) -> str:
    return (
        f"{provider}:{fixture_id}:{objective_id}:v{objective_version}:"
        f"{rule_id}:v{rule_version}"
    )


def build_backtest_record(
    fixture: EligibleFixture,
    replay: ReplayResult,
    *,
    objective_id: str,
    objective_version: int,
    rule_id: str,
    rule_version: int,
    rule_status: str,
    match_status: str,
    finalized_at: datetime,
) -> BacktestRecord:
    alert = replay.first_alert
    favorite_odds = (
        fixture.median_home_odds
        if fixture.favorite_side == "home"
        else fixture.median_away_odds
    )
    return BacktestRecord(
        record_id=backtest_record_id(
            provider=fixture.provider,
            fixture_id=fixture.fixture_id,
            objective_id=objective_id,
            objective_version=objective_version,
            rule_id=rule_id,
            rule_version=rule_version,
        ),
        fixture_id=fixture.fixture_id,
        league_id=fixture.league_id,
        league_name=fixture.league_name,
        favorite_side=fixture.favorite_side,
        favorite_odds=favorite_odds,
        favorite_probability=fixture.favorite_probability,
        objective_id=objective_id,
        objective_version=objective_version,
        rule_id=rule_id,
        rule_version=rule_version,
        rule_status=rule_status,
        match_status=match_status,
        finalized_at=finalized_at,
        snapshots_read=replay.snapshots_read,
        active_candidate_observations=replay.active_candidate_observations,
        alert_triggered=alert is not None,
        trigger_minute=alert.trigger_minute if alert else None,
        trigger_minute_extra=alert.trigger_minute_extra if alert else None,
        outcome=alert.label.outcome if alert else None,
        censored_reason=alert.label.censored_reason if alert else None,
    )


def summarize_backtests(records: list[BacktestRecord]) -> BacktestSummary:
    alerts = [record for record in records if record.alert_triggered]
    resolved = [record for record in alerts if record.outcome is not None]
    positives = sum(record.outcome is True for record in resolved)
    negatives = sum(record.outcome is False for record in resolved)
    return BacktestSummary(
        records=len(records),
        fixtures_with_history=sum(record.snapshots_read >= 2 for record in records),
        fixtures_with_active_candidate=sum(
            record.active_candidate_observations > 0 for record in records
        ),
        alerts=len(alerts),
        resolved_alerts=len(resolved),
        positive_alerts=positives,
        negative_alerts=negatives,
        censored_or_unresolved_alerts=len(alerts) - len(resolved),
        precision=positives / len(resolved) if resolved else None,
    )
