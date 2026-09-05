from __future__ import annotations

import argparse
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

from brain_projectbet.collection.series import derive_window
from brain_projectbet.collection.storage import append_snapshot, load_snapshots
from brain_projectbet.normalization.api_football import extract_match_winner_odds, normalize_snapshot
from brain_projectbet.providers.api_football import ApiFootballProbe


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require_payload_item(payload: dict, operation: str) -> dict:
    response = payload.get("response", [])
    if not response:
        raise RuntimeError(f"{operation} no devolvió datos: {payload.get('errors')}")
    return response[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Recolecta snapshots controlados de un fixture")
    parser.add_argument("--fixture-id", required=True)
    parser.add_argument("--bookmaker", default="Bet365")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--minimum-remaining", type=int, default=10)
    args = parser.parse_args()
    if args.cycles <= 0 or args.interval_seconds <= 0:
        parser.error("cycles e interval-seconds deben ser positivos")

    load_dotenv(Path(".env"))
    probe = ApiFootballProbe(os.getenv("API_FOOTBALL_KEY", ""))
    odds_response = probe.prematch_odds(args.fixture_id)
    odds = extract_match_winner_odds(
        odds_response.payload,
        fixture_id=args.fixture_id,
        bookmaker_name=args.bookmaker,
        captured_at=datetime.now(UTC),
    )
    favorite_side = odds.favorite_side()
    probabilities = odds.normalized_probabilities()
    output = Path("data/raw/snapshots") / f"api-football-{args.fixture_id}.jsonl"

    for cycle in range(1, args.cycles + 1):
        fixture_response = probe.fixture(args.fixture_id)
        statistics_response = probe.fixture_statistics(args.fixture_id)
        fixture = require_payload_item(dict(fixture_response.payload), "fixture")
        snapshot = normalize_snapshot(
            fixture,
            statistics_response.payload.get("response", []),
            captured_at=datetime.now(UTC),
        )
        append_snapshot(output, snapshot)
        favorite_score = snapshot.score_home if favorite_side == "home" else snapshot.score_away
        opponent_score = snapshot.score_away if favorite_side == "home" else snapshot.score_home
        precondition_met = (
            favorite_score is not None
            and opponent_score is not None
            and favorite_score < opponent_score
        )
        snapshots = load_snapshots(output)
        windows = {
            str(minutes): derive_window(snapshots, window_minutes=minutes)
            for minutes in (3, 5, 10, 15)
        }
        remaining_values = [
            value for value in (
                fixture_response.remaining_requests(),
                statistics_response.remaining_requests(),
            ) if value is not None
        ]
        remaining = min(remaining_values) if remaining_values else None
        print(json.dumps({
            "cycle": cycle,
            "fixture_id": args.fixture_id,
            "minute": snapshot.minute,
            "status": snapshot.status,
            "score": [snapshot.score_home, snapshot.score_away],
            "favorite_side": favorite_side,
            "favorite_probability": round(probabilities[0 if favorite_side == 'home' else 2], 4),
            "precondition_met": precondition_met,
            "windows_ready": [key for key, value in windows.items() if value is not None],
            "remaining_requests": remaining,
            "output": str(output),
        }, ensure_ascii=False))
        if remaining is not None and remaining <= args.minimum_remaining:
            print("Recolección detenida para preservar la cuota de solicitudes.")
            break
        if snapshot.status in {"FT", "AET", "PEN", "PST", "CANC", "ABD", "AWD", "WO"}:
            print("Recolección detenida porque el partido ya no está activo.")
            break
        if cycle < args.cycles:
            time.sleep(args.interval_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
