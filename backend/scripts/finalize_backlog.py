from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path


def past_registries(today: datetime, days: int) -> list[Path]:
    cutoff = today.date() - timedelta(days=days)
    paths = [
        *Path("data/raw/eligible").glob("*.json"),
        *Path("data/raw/coverage").glob("*.json"),
    ]
    return sorted(
        (path for path in paths if cutoff <= _registry_date(path) < today.date()),
        key=lambda path: (_registry_date(path), str(path)),
    )


def _registry_date(path: Path):
    try:
        return datetime.strptime(path.stem, "%Y-%m-%d").date()
    except ValueError:
        return datetime.min.date()


def main() -> int:
    parser = argparse.ArgumentParser(description="Reintenta cierre de jornadas anteriores con reserva de cuota")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--maximum-fixtures", type=int, default=3)
    parser.add_argument("--daily-reserve", type=int, default=15)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.days <= 0 or args.maximum_fixtures <= 0 or args.daily_reserve < 0:
        parser.error("días y máximo positivos; reserva no negativa")
    registries = past_registries(datetime.now(UTC), args.days)
    if args.dry_run:
        print(json.dumps({"registries": [str(path) for path in registries]}))
        return 0
    for registry in registries:
        result = subprocess.run(
            [sys.executable, "backend/scripts/finalize_matches.py", "--registry", str(registry),
             "--maximum-fixtures", str(args.maximum_fixtures),
             "--daily-reserve", str(args.daily_reserve)],
            check=False, capture_output=True, text=True,
        )
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        if result.returncode:
            return result.returncode
        try:
            payload = json.loads(result.stdout.splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            print(result.stdout, file=sys.stderr, end="")
            return 1
        print(json.dumps({"registry": str(registry), "due": payload["due"],
                          "processed": payload["processed"], "stopped": payload["stopped"]}, ensure_ascii=False))
        if any(item.get("finalized") for item in payload["processed"]):
            sync = subprocess.run(
                [sys.executable, "backend/scripts/sync_database.py", "--registry", str(registry)],
                check=False,
            )
            if sync.returncode:
                return sync.returncode
        if payload["stopped"]:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
