from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from brain_projectbet.database.session import Base


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MatchRecord(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("provider", "provider_match_id", name="uq_match_provider_id"),
        Index("ix_matches_kickoff", "kickoff_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(40))
    provider_match_id: Mapped[str] = mapped_column(String(80))
    kickoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    league_id: Mapped[str] = mapped_column(String(80), default="")
    league_name: Mapped[str] = mapped_column(String(160), default="")
    country: Mapped[str] = mapped_column(String(100), default="")
    home_team_name: Mapped[str] = mapped_column(String(160), default="")
    away_team_name: Mapped[str] = mapped_column(String(160), default="")
    favorite_side: Mapped[str] = mapped_column(String(8))
    favorite_odds: Mapped[float] = mapped_column(Float)
    favorite_probability: Mapped[float] = mapped_column(Float)
    bookmaker_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="SCHEDULED")
    score_home: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_away: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    snapshots: Mapped[list[SnapshotRecord]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )


class SnapshotRecord(Base):
    __tablename__ = "snapshots"
    __table_args__ = (
        UniqueConstraint("match_id", "captured_at", name="uq_snapshot_match_time"),
        Index("ix_snapshots_match_captured", "match_id", "captured_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    minute_extra: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    score_home: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_away: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shots_home: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shots_away: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shots_on_target_home: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shots_on_target_away: Mapped[int | None] = mapped_column(Integer, nullable=True)
    corners_home: Mapped[int | None] = mapped_column(Integer, nullable=True)
    corners_away: Mapped[int | None] = mapped_column(Integer, nullable=True)
    possession_home: Mapped[float | None] = mapped_column(Float, nullable=True)
    possession_away: Mapped[float | None] = mapped_column(Float, nullable=True)
    xg_home: Mapped[float | None] = mapped_column(Float, nullable=True)
    xg_away: Mapped[float | None] = mapped_column(Float, nullable=True)
    red_cards_home: Mapped[int | None] = mapped_column(Integer, nullable=True)
    red_cards_away: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    match: Mapped[MatchRecord] = relationship(back_populates="snapshots")


class StrategyRecord(Base):
    __tablename__ = "strategies"
    __table_args__ = (UniqueConstraint("strategy_key", "version", name="uq_strategy_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    strategy_key: Mapped[str] = mapped_column(String(100), index=True)
    version: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(180))
    statistical_status: Mapped[str] = mapped_column(String(20), default="HEURÍSTICA")
    objective_type: Mapped[str] = mapped_column(String(60))
    objective_subject: Mapped[str] = mapped_column(String(80))
    horizon_minutes: Mapped[int] = mapped_column(Integer)
    config: Mapped[dict] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AlertRecord(Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_created", "created_at"),)

    alert_id: Mapped[str] = mapped_column(String(220), primary_key=True)
    match_id: Mapped[int | None] = mapped_column(ForeignKey("matches.id"), nullable=True)
    fixture_id: Mapped[str] = mapped_column(String(80), index=True)
    strategy_key: Mapped[str] = mapped_column(String(100))
    strategy_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    minute: Mapped[int] = mapped_column(Integer)
    minute_extra: Mapped[int | None] = mapped_column(Integer, nullable=True)
    favorite_team_name: Mapped[str] = mapped_column(String(160), default="")
    score_favorite: Mapped[int] = mapped_column(Integer)
    score_opponent: Mapped[int] = mapped_column(Integer)
    delivery_status: Mapped[str] = mapped_column(String(20), default="PENDING")
    explanation: Mapped[dict] = mapped_column(JSON)


class BacktestRecordModel(Base):
    __tablename__ = "backtest_results"

    record_id: Mapped[str] = mapped_column(String(260), primary_key=True)
    fixture_id: Mapped[str] = mapped_column(String(80), index=True)
    strategy_key: Mapped[str] = mapped_column(String(100))
    strategy_version: Mapped[int] = mapped_column(Integer)
    rule_status: Mapped[str] = mapped_column(String(20))
    finalized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    alert_triggered: Mapped[bool] = mapped_column(Boolean)
    outcome: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    censored_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON)
