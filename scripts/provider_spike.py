from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from brain_projectbet.providers.api_football import ApiFootballProbe
from brain_projectbet.providers.sportmonks import SportMonksProbe


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def build_probe(provider: str):
    if provider == "api-football":
        return ApiFootballProbe(os.getenv("API_FOOTBALL_KEY", ""))
    return SportMonksProbe(os.getenv("SPORTMONKS_TOKEN", ""))


def main() -> int:
    parser = argparse.ArgumentParser(description="Captura respuestas crudas para comparar proveedores")
    parser.add_argument("provider", choices=("api-football", "sportmonks"))
    parser.add_argument("operation", choices=("live", "statistics", "odds"))
    parser.add_argument("--fixture-id")
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/provider-spike"))
    args = parser.parse_args()

    load_dotenv(Path(".env"))
    probe = build_probe(args.provider)
    if args.operation == "live":
        result = probe.live_matches()
    elif args.operation == "statistics":
        if args.provider != "api-football":
            parser.error("SportMonks incluye statistics en la operación live del spike")
        if not args.fixture_id:
            parser.error("--fixture-id es obligatorio para statistics")
        result = probe.fixture_statistics(args.fixture_id)
    else:
        if not args.fixture_id:
            parser.error("--fixture-id es obligatorio para odds")
        result = probe.prematch_odds(args.fixture_id)

    captured_at = datetime.now(UTC)
    output_dir = args.output_dir / result.provider
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{captured_at:%Y%m%dT%H%M%SZ}-{result.operation}.json"
    output_path.write_text(json.dumps(result.payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "provider": result.provider,
        "operation": result.operation,
        "elapsed_ms": round(result.elapsed_ms, 2),
        "output": str(output_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
