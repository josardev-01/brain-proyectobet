from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "ProjectBet API"
    environment: str = "development"
    database_url: str = "sqlite:///./data/projectbet.db"
    cors_origins: tuple[str, ...] = ("http://localhost:3000",)
    jwt_secret: str = "projectbet-local-development-only"
    access_token_minutes: int = 720


@lru_cache
def get_settings() -> Settings:
    environment = os.getenv("APP_ENV", "development")
    jwt_secret = os.getenv("JWT_SECRET", "projectbet-local-development-only")
    if environment == "production" and jwt_secret == "projectbet-local-development-only":
        raise RuntimeError("JWT_SECRET debe configurarse en producción")
    origins = tuple(
        item.strip()
        for item in os.getenv("API_CORS_ORIGINS", "http://localhost:3000").split(",")
        if item.strip()
    )
    return Settings(
        environment=environment,
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/projectbet.db"),
        cors_origins=origins,
        jwt_secret=jwt_secret,
        access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "720")),
    )
