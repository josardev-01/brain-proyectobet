from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, date, datetime
from pathlib import Path

from brain_projectbet.discovery.storage import load_eligible_fixtures
from brain_projectbet.orchestration.planner import MatchdayPlan, action_at, build_matchday_plan
from brain_projectbet.strategies.config import DEFAULT_STRATEGY_PATH


def plan_payload(plan: MatchdayPlan) -> dict:
    return {
        "windows": [
            {
                "starts_at": window.starts_at.isoformat(),
                "ends_at": window.ends_at.isoformat(),
                "fixture_ids": list(window.fixture_ids),
            }
            for window in plan.windows
        ],
        "finalize_at": plan.finalize_at.isoformat() if plan.finalize_at else None,
    }


def run_script(script: str, arguments: list[str]) -> tuple[int, dict | None]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = "src"
    completed = subprocess.run(
        [sys.executable, str(Path("scripts") / script), *arguments],
        cwd=Path.cwd(),
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    payload = None
    for line in reversed(completed.stdout.splitlines()):
        try:
            payload = json.loads(line)
            break
        except json.JSONDecodeError:
            continue
    return completed.returncode, payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta una jornada de forma reiniciable")
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("data/raw/eligible") / f"{date.today().isoformat()}.json",
    )
    parser.add_argument("--strategy", type=Path, default=DEFAULT_STRATEGY_PATH)
    parser.add_argument("--interval-seconds", type=int, default=600)
    parser.add_argument("--maximum-matches", type=int, default=3)
    parser.add_argument("--daily-reserve", type=int, default=15)
    parser.add_argument("--once", action="store_true", help="Ejecuta solo la accion que corresponde ahora")
    parser.add_argument("--dry-run", action="store_true", help="Muestra el plan sin consultar al proveedor")
    parser.add_argument(
        "--no-database-sync",
        action="store_true",
        help="No sincroniza los archivos capturados hacia la base de datos",
    )
    args = parser.parse_args()
    if args.interval_seconds <= 0 or args.maximum_matches <= 0:
        parser.error("interval-seconds y maximum-matches deben ser positivos")
    if not args.registry.exists():
        parser.error(f"registro no encontrado: {args.registry}")

    fixtures = load_eligible_fixtures(args.registry)
    plan = build_matchday_plan(fixtures)
    print(json.dumps({"registry": str(args.registry), **plan_payload(plan)}, ensure_ascii=False))
    if args.dry_run or not fixtures:
        return 0

    common = [
        "--registry", str(args.registry),
        "--strategy", str(args.strategy),
        "--daily-reserve", str(args.daily_reserve),
    ]

    while True:
        now = datetime.now(UTC)
        action, next_at = action_at(plan, now)
        if action == "monitor":
            exit_code, payload = run_script("monitor_candidates.py", [
                *common,
                "--cycles", "1",
                "--maximum-matches", str(args.maximum_matches),
            ])
            if exit_code or (payload and payload.get("stopped")):
                return exit_code
            if (
                payload
                and payload.get("daily_remaining") is not None
                and payload["daily_remaining"] <= args.daily_reserve + 1
            ):
                print(json.dumps({
                    "stopped": "daily_reserve_before_next_live_request",
                    "daily_remaining": payload["daily_remaining"],
                }))
                return 75
            if not args.no_database_sync:
                sync_exit, _ = run_script("sync_database.py", ["--registry", str(args.registry)])
                if sync_exit:
                    return sync_exit
            if args.once:
                return 0
            time.sleep(args.interval_seconds)
            continue
        if action == "finalize":
            while True:
                exit_code, payload = run_script("finalize_matches.py", [
                    *common,
                    "--maximum-fixtures", str(args.maximum_matches),
                ])
                if exit_code or (payload and payload.get("stopped")):
                    return exit_code or 75
                if not payload or payload.get("due", 0) == 0:
                    return 0
                finalized = sum(
                    1 for item in payload.get("processed", []) if item.get("finalized") is True
                )
                if finalized == 0:
                    print(json.dumps({
                        "action": "finalization_pending",
                        "reason": "no_finished_fixture_in_batch",
                    }))
                    return 0
                if not args.no_database_sync:
                    sync_exit, _ = run_script("sync_database.py", ["--registry", str(args.registry)])
                    if sync_exit:
                        return sync_exit
        if action == "complete" or args.once:
            print(json.dumps({
                "action": action,
                "now": now.isoformat(),
                "next_at": next_at.isoformat() if next_at else None,
            }))
            return 0

        seconds = max(1, int((next_at - now).total_seconds())) if next_at else 60
        time.sleep(min(seconds, 60))


if __name__ == "__main__":
    raise SystemExit(main())
