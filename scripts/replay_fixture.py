from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from brain_projectbet.backtesting.replay import replay_first_alert
from brain_projectbet.collection.storage import load_snapshots
from brain_projectbet.discovery.storage import load_eligible_fixtures
from brain_projectbet.domain.models import PrematchOdds
from brain_projectbet.domain.objectives import FAVORITE_GOAL_WITHIN_10M_V1


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce un fixture sin usar información futura en la regla")
    parser.add_argument("--fixture-id", required=True)
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("data/raw/eligible") / f"{date.today().isoformat()}.json",
    )
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--snapshots", type=Path)
    args = parser.parse_args()

    registered = next(
        (item for item in load_eligible_fixtures(args.registry) if item.fixture_id == args.fixture_id),
        None,
    )
    if registered is None:
        parser.error(f"fixture {args.fixture_id} no encontrado en {args.registry}")
    snapshot_path = args.snapshots or Path("data/raw/snapshots") / f"api-football-{args.fixture_id}.jsonl"
    snapshots = load_snapshots(snapshot_path)
    event_payload = json.loads(args.events.read_text(encoding="utf-8"))
    events = event_payload.get("response", event_payload) if isinstance(event_payload, dict) else event_payload
    odds = PrematchOdds(
        provider="api-football-consensus",
        provider_match_id=registered.fixture_id,
        captured_at=registered.discovered_at,
        home=registered.median_home_odds,
        draw=registered.median_draw_odds,
        away=registered.median_away_odds,
    )
    result = replay_first_alert(snapshots, odds, FAVORITE_GOAL_WITHIN_10M_V1, events)
    print(json.dumps(asdict(result), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
