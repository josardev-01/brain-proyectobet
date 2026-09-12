from __future__ import annotations

import json
from time import perf_counter
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class ProviderHttpError(RuntimeError):
    def __init__(self, status_code: int, retry_after: int | None = None) -> None:
        super().__init__(f"el proveedor respondió HTTP {status_code}")
        self.status_code = status_code
        self.retry_after = retry_after


def get_json(
    base_url: str,
    *,
    query: Mapping[str, str] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout_seconds: float = 20,
    array_root_key: str | None = None,
) -> tuple[Mapping[str, Any], float, Mapping[str, str]]:
    url = base_url
    if query:
        url = f"{base_url}?{urlencode(query)}"
    request = Request(url, headers=dict(headers or {}), method="GET")
    started_at = perf_counter()
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
            response_headers = {
                name: value
                for name, value in response.headers.items()
                if "ratelimit" in name.lower()
            }
    except HTTPError as error:
        retry_value = error.headers.get("Retry-After") if error.headers else None
        try:
            retry_after = int(retry_value) if retry_value is not None else None
        except ValueError:
            retry_after = None
        raise ProviderHttpError(error.code, retry_after) from None
    elapsed_ms = (perf_counter() - started_at) * 1000
    if isinstance(payload, list) and array_root_key is not None:
        payload = {array_root_key: payload}
    if not isinstance(payload, dict):
        raise ValueError("el proveedor devolvió un JSON raíz no reconocido")
    return payload, elapsed_ms, response_headers
