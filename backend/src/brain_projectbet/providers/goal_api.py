from __future__ import annotations

from typing import Mapping

from brain_projectbet.providers.base import ProbeResponse
from brain_projectbet.providers.http import get_json


class GoalApiProbe:
    name = "goal-api"
    base_url = "https://api.goal-api.com/v1"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("GOAL_API_KEY no está configurada")
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "ProjectBet/0.1",
        }

    @staticmethod
    def _daily_headers(headers: Mapping[str, str]) -> Mapping[str, str]:
        normalized = {name.lower(): value for name, value in headers.items()}
        if normalized.get("x-ratelimit-type", "").upper() != "DAILY":
            return headers
        result = {
            name: value
            for name, value in headers.items()
            if name.lower() not in {"x-ratelimit-limit", "x-ratelimit-remaining"}
        }
        result["x-ratelimit-requests-limit"] = normalized.get("x-ratelimit-limit", "")
        result["x-ratelimit-requests-remaining"] = normalized.get(
            "x-ratelimit-remaining", ""
        )
        return result

    def _get(self, path: str, operation: str) -> ProbeResponse:
        payload, elapsed_ms, headers = get_json(
            f"{self.base_url}{path}", headers=self._headers
        )
        return ProbeResponse(
            self.name,
            operation,
            elapsed_ms,
            payload,
            self._daily_headers(headers),
        )

    def live_matches(self) -> ProbeResponse:
        return self._get("/fixtures/live", "live_matches")

    def fixture(self, fixture_id: str) -> ProbeResponse:
        return self._get(f"/fixtures/{fixture_id}", "fixture")

    def fixture_statistics(self, fixture_id: str) -> ProbeResponse:
        return self._get(
            f"/fixtures/{fixture_id}/statistics", "fixture_statistics"
        )

    def fixture_events(self, fixture_id: str) -> ProbeResponse:
        return self._get(f"/fixtures/{fixture_id}/events", "fixture_events")

    def prematch_odds(self, fixture_id: str) -> ProbeResponse:
        return self._get(f"/fixtures/{fixture_id}/odds", "prematch_odds")
