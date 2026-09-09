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
    environment = os.getenv("APP_ENV", "development").strip().lower()
    if environment not in {"development", "test", "production"}:
        raise RuntimeError("APP_ENV debe ser development, test o production")
    jwt_secret = os.getenv("JWT_SECRET", "projectbet-local-development-only")
    access_token_minutes = int(os.getenv("ACCESS_TOKEN_MINUTES", "720"))
    if not 5 <= access_token_minutes <= 10080:
        raise RuntimeError("ACCESS_TOKEN_MINUTES debe estar entre 5 y 10080")
    origins = tuple(
        item.strip()
        for item in os.getenv("API_CORS_ORIGINS", "http://localhost:3000").split(",")
        if item.strip()
    )
    if environment == "production":
        if (
            len(jwt_secret) < 32
            or jwt_secret == "projectbet-local-development-only"
            or jwt_secret.startswith("replace-with-")
        ):
            raise RuntimeError("JWT_SECRET debe ser aleatorio y tener al menos 32 caracteres")
        if not origins or any(origin == "*" or not origin.startswith("https://") for origin in origins):
            raise RuntimeError("API_CORS_ORIGINS debe contener solo orígenes HTTPS explícitos")
    return Settings(
        environment=environment,
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/projectbet.db"),
        cors_origins=origins,
        jwt_secret=jwt_secret,
        access_token_minutes=access_token_minutes,
    )
