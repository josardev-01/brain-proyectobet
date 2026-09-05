from __future__ import annotations

import json
from time import perf_counter
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def get_json(
    base_url: str,
    *,
    query: Mapping[str, str] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout_seconds: float = 20,
) -> tuple[Mapping[str, Any], float]:
    url = base_url
    if query:
        url = f"{base_url}?{urlencode(query)}"
    request = Request(url, headers=dict(headers or {}), method="GET")
    started_at = perf_counter()
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    elapsed_ms = (perf_counter() - started_at) * 1000
    if not isinstance(payload, dict):
        raise ValueError("el proveedor devolvió un JSON raíz no reconocido")
    return payload, elapsed_ms
