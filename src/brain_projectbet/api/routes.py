from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from brain_projectbet.api.schemas import (
    AlertView,
    DashboardView,
    MatchSummary,
    RuleEvaluationRequest,
    RuleEvaluationView,
    SnapshotView,
    StrategyCreate,
    StrategyView,
)
from brain_projectbet.database.models import (
    AlertRecord,
    BacktestRecordModel,
    MatchRecord,
    SnapshotRecord,
    StrategyRecord,
)
from brain_projectbet.database.session import get_db
from brain_projectbet.rules.expression import InvalidExpression, evaluate_expression


router = APIRouter(prefix="/api/v1")


@router.get("/dashboard", response_model=DashboardView)
def dashboard(session: Session = Depends(get_db)) -> DashboardView:
    matches = session.scalar(select(func.count()).select_from(MatchRecord)) or 0
    live = session.scalar(select(func.count()).select_from(MatchRecord).where(
        MatchRecord.status.in_(("1H", "HT", "2H", "ET", "BT", "P"))
    )) or 0
    strategies = session.scalar(select(func.count()).select_from(StrategyRecord)) or 0
    active_strategies = session.scalar(select(func.count()).select_from(StrategyRecord).where(
        StrategyRecord.active.is_(True)
    )) or 0
    alerts = session.scalar(select(func.count()).select_from(AlertRecord)) or 0
    snapshots = session.scalar(select(func.count()).select_from(SnapshotRecord)) or 0
    backtests = session.scalar(select(func.count()).select_from(BacktestRecordModel)) or 0
    resolved = session.scalar(select(func.count()).select_from(BacktestRecordModel).where(
        BacktestRecordModel.alert_triggered.is_(True), BacktestRecordModel.outcome.is_not(None)
    )) or 0
    positives = session.scalar(select(func.count()).select_from(BacktestRecordModel).where(
        BacktestRecordModel.alert_triggered.is_(True), BacktestRecordModel.outcome.is_(True)
    )) or 0
    return DashboardView(
        matches=matches,
        live_matches=live,
        strategies=strategies,
        active_strategies=active_strategies,
        alerts=alerts,
        snapshots=snapshots,
        backtest_records=backtests,
        resolved_alerts=resolved,
        precision=positives / resolved if resolved else None,
    )


@router.get("/matches", response_model=list[MatchSummary])
def list_matches(
    match_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db),
):
    query = select(MatchRecord).order_by(MatchRecord.kickoff_at.desc()).limit(limit)
    if match_status:
        query = query.where(MatchRecord.status == match_status)
    return list(session.scalars(query))


@router.get("/matches/{provider}/{fixture_id}", response_model=MatchSummary)
def get_match(provider: str, fixture_id: str, session: Session = Depends(get_db)):
    match = session.scalar(select(MatchRecord).where(
        MatchRecord.provider == provider,
        MatchRecord.provider_match_id == fixture_id,
    ))
    if match is None:
        raise HTTPException(status_code=404, detail="partido no encontrado")
    return match


@router.get("/matches/{provider}/{fixture_id}/snapshots", response_model=list[SnapshotView])
def list_match_snapshots(provider: str, fixture_id: str, session: Session = Depends(get_db)):
    match = session.scalar(select(MatchRecord).where(
        MatchRecord.provider == provider,
        MatchRecord.provider_match_id == fixture_id,
    ))
    if match is None:
        raise HTTPException(status_code=404, detail="partido no encontrado")
    return list(session.scalars(select(SnapshotRecord).where(
        SnapshotRecord.match_id == match.id
    ).order_by(SnapshotRecord.captured_at)))


@router.get("/strategies", response_model=list[StrategyView])
def list_strategies(session: Session = Depends(get_db)):
    return list(session.scalars(select(StrategyRecord).order_by(
        StrategyRecord.strategy_key, StrategyRecord.version.desc()
    )))


@router.post("/strategies", response_model=StrategyView, status_code=status.HTTP_201_CREATED)
def create_strategy(payload: StrategyCreate, session: Session = Depends(get_db)):
    record = StrategyRecord(**payload.model_dump(), created_at=datetime.now(UTC))
    session.add(record)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="esa versión de estrategia ya existe")
    session.refresh(record)
    return record


@router.patch("/strategies/{strategy_id}/activation", response_model=StrategyView)
def set_strategy_activation(strategy_id: int, active: bool, session: Session = Depends(get_db)):
    record = session.get(StrategyRecord, strategy_id)
    if record is None:
        raise HTTPException(status_code=404, detail="estrategia no encontrada")
    record.active = active
    session.commit()
    session.refresh(record)
    return record


@router.get("/alerts", response_model=list[AlertView])
def list_alerts(
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db),
):
    return list(session.scalars(select(AlertRecord).order_by(
        AlertRecord.created_at.desc()
    ).limit(limit)))


@router.post("/rules/evaluate", response_model=RuleEvaluationView)
def evaluate_rule(payload: RuleEvaluationRequest):
    try:
        result = evaluate_expression(payload.expression, payload.metrics)
    except InvalidExpression as error:
        raise HTTPException(status_code=422, detail=str(error))
    return RuleEvaluationView(
        matched=result.matched,
        reasons=list(result.reasons),
        missing_metrics=list(result.missing_metrics),
    )
