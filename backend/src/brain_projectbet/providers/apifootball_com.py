from __future__ import annotations

from brain_projectbet.providers.base import ProbeResponse
from brain_projectbet.providers.http import get_json


class ApiFootballComProbe:
    """Cliente para apifootball.com; no confundir con API-Sports API-Football."""

    name = "apifootball-com"
    base_url = "https://apiv3.apifootball.com/"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("APIFOOTBALL_KEY no está configurada")
        self._api_key = api_key

    def _get(self, operation: str, **query: str) -> ProbeResponse:
        payload, elapsed_ms, headers = get_json(
            self.base_url,
            query={"APIkey": self._api_key, **query},
            array_root_key="response",
        )
        return ProbeResponse(self.name, operation, elapsed_ms, payload, headers)

    def live_matches(self) -> ProbeResponse:
        return self._get("live_matches", action="get_events", match_live="1")

    def fixture(self, fixture_id: str) -> ProbeResponse:
        return self._get("fixture", action="get_events", match_id=fixture_id)

    def fixture_statistics(self, fixture_id: str) -> ProbeResponse:
        return self._get(
            "fixture_statistics", action="get_statistics", match_id=fixture_id
        )

    def fixture_events(self, fixture_id: str) -> ProbeResponse:
        return self._get("fixture_events", action="get_events", match_id=fixture_id)

    def prematch_odds(self, fixture_id: str) -> ProbeResponse:
        return self._get("prematch_odds", action="get_odds", match_id=fixture_id)
