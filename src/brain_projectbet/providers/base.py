from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True, slots=True)
class ProbeResponse:
    provider: str
    operation: str
    elapsed_ms: float
    payload: Mapping[str, Any]
    response_headers: Mapping[str, str]

    def remaining_requests(self) -> int | None:
        for name, value in self.response_headers.items():
            if name.lower() in {"x-ratelimit-requests-remaining", "x-ratelimit-remaining"}:
                try:
                    return int(value)
                except ValueError:
                    return None
        return None


class FootballDataProbe(Protocol):
    name: str

    def live_matches(self) -> ProbeResponse:
        """Obtiene partidos en juego con los includes disponibles."""

    def prematch_odds(self, fixture_id: str) -> ProbeResponse:
        """Obtiene odds 1X2 anteriores al partido, si el plan las permite."""
