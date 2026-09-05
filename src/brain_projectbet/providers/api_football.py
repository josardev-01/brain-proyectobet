from __future__ import annotations

from brain_projectbet.providers.base import ProbeResponse
from brain_projectbet.providers.http import get_json


class ApiFootballProbe:
    name = "api-football"
    base_url = "https://v3.football.api-sports.io"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("API_FOOTBALL_KEY no está configurada")
        self._headers = {"x-apisports-key": api_key}

    def live_matches(self) -> ProbeResponse:
        payload, elapsed_ms, headers = get_json(
            f"{self.base_url}/fixtures",
            query={"live": "all"},
            headers=self._headers,
        )
        return ProbeResponse(self.name, "live_matches", elapsed_ms, payload, headers)

    def fixture(self, fixture_id: str) -> ProbeResponse:
        payload, elapsed_ms, headers = get_json(
            f"{self.base_url}/fixtures",
            query={"id": fixture_id},
            headers=self._headers,
        )
        return ProbeResponse(self.name, "fixture", elapsed_ms, payload, headers)

    def fixture_statistics(self, fixture_id: str) -> ProbeResponse:
        payload, elapsed_ms, headers = get_json(
            f"{self.base_url}/fixtures/statistics",
            query={"fixture": fixture_id},
            headers=self._headers,
        )
        return ProbeResponse(self.name, "fixture_statistics", elapsed_ms, payload, headers)

    def fixture_events(self, fixture_id: str) -> ProbeResponse:
        payload, elapsed_ms, headers = get_json(
            f"{self.base_url}/fixtures/events",
            query={"fixture": fixture_id},
            headers=self._headers,
        )
        return ProbeResponse(self.name, "fixture_events", elapsed_ms, payload, headers)

    def prematch_odds(self, fixture_id: str) -> ProbeResponse:
        payload, elapsed_ms, headers = get_json(
            f"{self.base_url}/odds",
            query={"fixture": fixture_id},
            headers=self._headers,
        )
        return ProbeResponse(self.name, "prematch_odds", elapsed_ms, payload, headers)

    def prematch_odds_by_date(self, date: str, *, page: int = 1) -> ProbeResponse:
        payload, elapsed_ms, headers = get_json(
            f"{self.base_url}/odds",
            query={"date": date, "page": str(page)},
            headers=self._headers,
        )
        return ProbeResponse(self.name, "prematch_odds_by_date", elapsed_ms, payload, headers)
