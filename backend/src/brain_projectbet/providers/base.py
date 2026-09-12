from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True, slots=True)
class RateLimitStatus:
    daily_limit: int | None = None
    daily_remaining: int | None = None
    minute_limit: int | None = None
    minute_remaining: int | None = None


@dataclass(frozen=True, slots=True)
class ProbeResponse:
    provider: str
    operation: str
    elapsed_ms: float
    payload: Mapping[str, Any]
    response_headers: Mapping[str, str]

    def rate_limits(self) -> RateLimitStatus:
        headers = {name.lower(): value for name, value in self.response_headers.items()}

        def integer(name: str) -> int | None:
            value = headers.get(name)
            try:
                return int(value) if value is not None else None
            except ValueError:
                return None

        return RateLimitStatus(
            daily_limit=integer("x-ratelimit-requests-limit"),
            daily_remaining=integer("x-ratelimit-requests-remaining"),
            minute_limit=integer("x-ratelimit-limit"),
            minute_remaining=integer("x-ratelimit-remaining"),
        )


class FootballDataProbe(Protocol):
    name: str

    def live_matches(self) -> ProbeResponse:
        """Obtiene partidos en juego con los includes disponibles."""

    def prematch_odds(self, fixture_id: str) -> ProbeResponse:
        """Obtiene odds 1X2 anteriores al partido, si el plan las permite."""
