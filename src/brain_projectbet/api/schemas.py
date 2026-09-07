from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from brain_projectbet.rules.expression import InvalidExpression, validate_expression


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
    corners_home: int | None
    corners_away: int | None
    possession_home: float | None
    possession_away: float | None


class StrategyView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
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
        if conditions:
            expression = conditions if isinstance(conditions, dict) else {
                "logical": "AND", "conditions": conditions
            }
            try:
                validate_expression(expression)
            except InvalidExpression as error:
                raise ValueError(str(error)) from error
        return self


class AlertView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: str
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
    email: str
    password: str


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    active: bool
    created_at: datetime


class TokenView(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserView


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
