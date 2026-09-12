from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from brain_projectbet.rules.expression import InvalidExpression, validate_expression
from brain_projectbet.rules.catalog import STRATEGY_CATALOG


class MatchSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    provider_match_id: str
    kickoff_at: datetime
    league_name: str
    country: str
    home_team_name: str
    away_team_name: str
    favorite_side: str
    favorite_odds: float
    favorite_probability: float
    home_odds: float | None
    draw_odds: float | None
    away_odds: float | None
    home_probability: float | None
    draw_probability: float | None
    away_probability: float | None
    status: str
    score_home: int | None
    score_away: int | None


class SnapshotView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    captured_at: datetime
    minute: int | None
    minute_extra: int | None
    status: str
    score_home: int | None
    score_away: int | None
    shots_home: int | None
    shots_away: int | None
    shots_on_target_home: int | None
    shots_on_target_away: int | None
    shots_off_target_home: int | None
    shots_off_target_away: int | None
    attacks_home: int | None
    attacks_away: int | None
    dangerous_attacks_home: int | None
    dangerous_attacks_away: int | None
    corners_home: int | None
    corners_away: int | None
    possession_home: float | None
    possession_away: float | None
    yellow_cards_home: int | None
    yellow_cards_away: int | None
    red_cards_home: int | None
    red_cards_away: int | None


class StrategyView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int | None
    strategy_key: str
    version: int
    name: str
    statistical_status: str
    objective_type: str
    objective_subject: str
    horizon_minutes: int
    config: dict[str, Any]
    active: bool
    created_at: datetime


class StrategyCreate(BaseModel):
    strategy_key: str = Field(min_length=3, max_length=100, pattern=r"^[a-z0-9_]+$")
    version: int = Field(ge=1)
    name: str = Field(min_length=3, max_length=180)
    statistical_status: Literal["HEURÍSTICA", "EXPERIMENTAL", "VALIDADA"] = "HEURÍSTICA"
    objective_type: str = Field(min_length=2, max_length=60)
    objective_subject: str = Field(min_length=2, max_length=80)
    horizon_minutes: int = Field(ge=1, le=120)
    config: dict[str, Any]
    active: bool = False

    @model_validator(mode="after")
    def identity_matches_config(self):
        configured_id = self.config.get("strategy_id")
        configured_version = self.config.get("version")
        if configured_id != self.strategy_key or configured_version != self.version:
            raise ValueError("strategy_id y version del config deben coincidir con la identidad")
        conditions = self.config.get("conditions")
        if not conditions:
            raise ValueError("la estrategia debe contener al menos una condición")
        expression = conditions if isinstance(conditions, dict) else {
            "logical": "AND", "conditions": conditions
        }
        try:
            validate_expression(expression)
        except InvalidExpression as error:
            raise ValueError(str(error)) from error
        window = self.config.get("feature_window_minutes", 10)
        if window not in STRATEGY_CATALOG["windows"]:
            raise ValueError("feature_window_minutes no está permitido")
        allowed_metrics = {item["value"] for item in STRATEGY_CATALOG["metrics"]}
        for item in STRATEGY_CATALOG["metrics"]:
            if item.get("supports_window"):
                allowed_metrics.add(f"{item['value']}_last_{window}")

        def metric_names(node: dict[str, Any]):
            if "logical" in node:
                for child in node.get("conditions", []):
                    yield from metric_names(child)
            elif isinstance(node.get("metric"), str):
                yield node["metric"]

        unknown = sorted(set(metric_names(expression)) - allowed_metrics)
        if unknown:
            raise ValueError(f"métricas no permitidas: {', '.join(unknown)}")
        objectives = {item["value"] for item in STRATEGY_CATALOG["objectives"]}
        subjects = {item["value"] for item in STRATEGY_CATALOG["subjects"]}
        if self.objective_type not in objectives or self.objective_subject not in subjects:
            raise ValueError("objetivo no permitido")
        if self.statistical_status != "HEURÍSTICA":
            raise ValueError("una estrategia creada por usuario debe comenzar como HEURÍSTICA")
        scope = self.config.get("scope", {})
        if not isinstance(scope, dict):
            raise ValueError("scope debe ser un objeto")
        for key in ("leagues_included", "leagues_excluded", "countries_included"):
            values = scope.get(key, [])
            if not isinstance(values, list) or len(values) > 100:
                raise ValueError(f"{key} debe ser una lista de hasta 100 elementos")
            if any(not isinstance(item, str) or not item.strip() or len(item) > 160 for item in values):
                raise ValueError(f"{key} contiene un valor inválido")
        allowed_fields = {item["value"] for item in STRATEGY_CATALOG["alert_fields"]}
        alert_fields = self.config.get("alert_fields", [])
        if not isinstance(alert_fields, list) or not set(alert_fields).issubset(allowed_fields):
            raise ValueError("alert_fields contiene un campo no permitido")
        return self


class AlertView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: str
    owner_id: int | None
    fixture_id: str
    strategy_key: str
    strategy_version: int
    created_at: datetime
    minute: int
    minute_extra: int | None
    favorite_team_name: str
    score_favorite: int
    score_opponent: int
    delivery_status: str
    explanation: dict[str, Any]


class DashboardView(BaseModel):
    matches: int
    live_matches: int
    strategies: int
    active_strategies: int
    alerts: int
    snapshots: int
    backtest_records: int
    resolved_alerts: int
    precision: float | None
    statistical_status: str = "EXPERIMENTAL"


class RuleEvaluationRequest(BaseModel):
    expression: dict[str, Any]
    metrics: dict[str, Any]


class RuleEvaluationView(BaseModel):
    matched: bool
    reasons: list[str]
    missing_metrics: list[str]


class UserRegister(BaseModel):
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    display_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=10, max_length=128)


class UserLogin(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    active: bool
    role: str
    approval_status: str
    reviewed_at: datetime | None
    reviewed_by_id: int | None
    created_at: datetime


class RegistrationView(BaseModel):
    status: Literal["PENDING"] = "PENDING"
    message: str
    user: UserView


class TokenView(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserView


class UserApprovalUpdate(BaseModel):
    approval_status: Literal["APPROVED", "REJECTED"]


class NotificationEndpointCreate(BaseModel):
    channel: Literal["telegram"] = "telegram"
    destination: str = Field(min_length=2, max_length=180, pattern=r"^-?\d+$")
    label: str = Field(default="", max_length=120)
    enabled: bool = True


class NotificationEndpointView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel: str
    destination: str
    label: str
    enabled: bool
    created_at: datetime


class StrategyRuntimeView(BaseModel):
    strategy_id: int
    strategy_key: str
    strategy_version: int
    statistical_status: str
    matched: bool | None
    reasons: list[str] = Field(default_factory=list)
    missing_metrics: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
