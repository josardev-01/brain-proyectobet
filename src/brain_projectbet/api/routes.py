from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from brain_projectbet.api.schemas import (
    AlertView,
    DashboardView,
    MatchSummary,
    NotificationEndpointCreate,
    NotificationEndpointView,
    RuleEvaluationRequest,
    RuleEvaluationView,
    SnapshotView,
    StrategyCreate,
    StrategyView,
    TokenView,
    UserLogin,
    UserRegister,
    UserView,
)
from brain_projectbet.database.models import (
    AlertRecord,
    BacktestRecordModel,
    MatchRecord,
    NotificationEndpointRecord,
    SnapshotRecord,
    StrategyRecord,
    UserRecord,
)
from brain_projectbet.database.session import get_db
from brain_projectbet.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from brain_projectbet.core.settings import get_settings
from brain_projectbet.rules.expression import InvalidExpression, evaluate_expression


router = APIRouter(prefix="/api/v1")


@router.post("/auth/register", response_model=TokenView, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, response: Response, session: Session = Depends(get_db)):
    normalized_email = payload.email.strip().lower()
    if session.scalar(select(UserRecord).where(UserRecord.email == normalized_email)) is not None:
        raise HTTPException(status_code=409, detail="el correo ya está registrado")
    user = UserRecord(
        email=normalized_email,
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
        active=True,
        created_at=datetime.now(UTC),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    token, expires_in = create_access_token(user.id)
    response.set_cookie(
        "projectbet_session", token, max_age=expires_in, httponly=True,
        secure=get_settings().environment == "production", samesite="lax",
    )
    return TokenView(access_token=token, expires_in=expires_in, user=user)


@router.post("/auth/login", response_model=TokenView)
def login(payload: UserLogin, response: Response, session: Session = Depends(get_db)):
    user = session.scalar(select(UserRecord).where(UserRecord.email == payload.email.strip().lower()))
    if user is None or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="credenciales inválidas")
    token, expires_in = create_access_token(user.id)
    response.set_cookie(
        "projectbet_session", token, max_age=expires_in, httponly=True,
        secure=get_settings().environment == "production", samesite="lax",
    )
    return TokenView(access_token=token, expires_in=expires_in, user=user)


@router.get("/auth/me", response_model=UserView)
def me(user: UserRecord = Depends(get_current_user)):
    return user


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie("projectbet_session")


@router.get("/notification-endpoints", response_model=list[NotificationEndpointView])
def list_notification_endpoints(
    session: Session = Depends(get_db),
    user: UserRecord = Depends(get_current_user),
):
    return list(session.scalars(select(NotificationEndpointRecord).where(
        NotificationEndpointRecord.owner_id == user.id
    ).order_by(NotificationEndpointRecord.created_at)))


@router.post(
    "/notification-endpoints",
    response_model=NotificationEndpointView,
    status_code=status.HTTP_201_CREATED,
)
def create_notification_endpoint(
    payload: NotificationEndpointCreate,
    session: Session = Depends(get_db),
    user: UserRecord = Depends(get_current_user),
):
    endpoint = NotificationEndpointRecord(
        owner_id=user.id,
        channel=payload.channel,
        destination=payload.destination,
        label=payload.label.strip(),
        enabled=payload.enabled,
        created_at=datetime.now(UTC),
    )
    session.add(endpoint)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="ese destino ya está configurado")
    session.refresh(endpoint)
    return endpoint


@router.patch(
    "/notification-endpoints/{endpoint_id}/activation",
    response_model=NotificationEndpointView,
)
def set_notification_endpoint_activation(
    endpoint_id: int,
    enabled: bool,
    session: Session = Depends(get_db),
    user: UserRecord = Depends(get_current_user),
):
    endpoint = session.get(NotificationEndpointRecord, endpoint_id)
    if endpoint is None or endpoint.owner_id != user.id:
        raise HTTPException(status_code=404, detail="destino no encontrado")
    endpoint.enabled = enabled
    session.commit()
    session.refresh(endpoint)
    return endpoint


@router.delete("/notification-endpoints/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification_endpoint(
    endpoint_id: int,
    session: Session = Depends(get_db),
    user: UserRecord = Depends(get_current_user),
):
    endpoint = session.get(NotificationEndpointRecord, endpoint_id)
    if endpoint is None or endpoint.owner_id != user.id:
        raise HTTPException(status_code=404, detail="destino no encontrado")
    session.delete(endpoint)
    session.commit()


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
def create_strategy(
    payload: StrategyCreate,
    session: Session = Depends(get_db),
    user: UserRecord = Depends(get_current_user),
):
    record = StrategyRecord(**payload.model_dump(), owner_id=user.id, created_at=datetime.now(UTC))
    session.add(record)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="esa versión de estrategia ya existe")
    session.refresh(record)
    return record


@router.patch("/strategies/{strategy_id}/activation", response_model=StrategyView)
def set_strategy_activation(
    strategy_id: int,
    active: bool,
    session: Session = Depends(get_db),
    user: UserRecord = Depends(get_current_user),
):
    record = session.get(StrategyRecord, strategy_id)
    if record is None:
        raise HTTPException(status_code=404, detail="estrategia no encontrada")
    if record.owner_id is not None and record.owner_id != user.id:
        raise HTTPException(status_code=403, detail="no puedes modificar esta estrategia")
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
