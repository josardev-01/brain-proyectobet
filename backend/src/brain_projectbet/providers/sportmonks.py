from __future__ import annotations

from brain_projectbet.providers.base import ProbeResponse
from brain_projectbet.providers.http import get_json


class SportMonksProbe:
    name = "sportmonks"
    base_url = "https://api.sportmonks.com/v3/football"

    def __init__(self, api_token: str) -> None:
        if not api_token:
            raise ValueError("SPORTMONKS_TOKEN no está configurada")
        self._token = api_token

    def live_matches(self) -> ProbeResponse:
        payload, elapsed_ms, headers = get_json(
            f"{self.base_url}/livescores/inplay",
            query={
                "api_token": self._token,
                "include": "participants;scores;statistics;events",
            },
        )
        return ProbeResponse(self.name, "live_matches", elapsed_ms, payload, headers)

    def prematch_odds(self, fixture_id: str) -> ProbeResponse:
        payload, elapsed_ms, headers = get_json(
            f"{self.base_url}/odds/pre-match/fixtures/{fixture_id}",
            query={"api_token": self._token},
        )
        return ProbeResponse(self.name, "prematch_odds", elapsed_ms, payload, headers)
