from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "ProjectBet API"
    environment: str = "development"
    database_url: str = "sqlite:///./data/projectbet.db"
    cors_origins: tuple[str, ...] = ("http://localhost:3000",)


@lru_cache
def get_settings() -> Settings:
    origins = tuple(
        item.strip()
        for item in os.getenv("API_CORS_ORIGINS", "http://localhost:3000").split(",")
        if item.strip()
    )
    return Settings(
        environment=os.getenv("APP_ENV", "development"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/projectbet.db"),
        cors_origins=origins,
    )
