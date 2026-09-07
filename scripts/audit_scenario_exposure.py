from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from brain_projectbet.backtesting.exposure import audit_favorite_losing_exposure
from brain_projectbet.discovery.storage import load_eligible_fixtures


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita si el favorito llegó a perder desde el minuto objetivo")
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    reports = []
    missing = []
    for registered in load_eligible_fixtures(args.registry):
        fixture_path = Path("data/raw/fixtures") / f"api-football-{registered.fixture_id}-final.json"
        events_path = Path("data/raw/events") / f"api-football-{registered.fixture_id}.json"
        if not fixture_path.exists() or not events_path.exists():
            missing.append(registered.fixture_id)
            continue
        fixture_payload = json.loads(fixture_path.read_text(encoding="utf-8"))["response"][0]
        events = json.loads(events_path.read_text(encoding="utf-8")).get("response", [])
        teams = fixture_payload["teams"]
        goals = fixture_payload["goals"]
        home_id = str(teams["home"]["id"])
        away_id = str(teams["away"]["id"])
        favorite_id = home_id if registered.favorite_side == "home" else away_id
        report = audit_favorite_losing_exposure(
            fixture_id=registered.fixture_id,
            home_team_id=home_id,
            away_team_id=away_id,
            favorite_team_id=favorite_id,
            final_home_score=int(goals["home"]),
            final_away_score=int(goals["away"]),
            events=events,
        )
        item = asdict(report)
        item["match"] = f"{teams['home']['name']} vs {teams['away']['name']}"
        reports.append(item)

    payload = {
        "fixtures": len(reports),
        "score_reconciled": sum(item["score_reconciled"] for item in reports),
        "scenario_active": sum(item["scenario_ever_active"] is True for item in reports),
        "scenario_inactive": sum(item["scenario_ever_active"] is False for item in reports),
        "scenario_unknown": sum(item["scenario_ever_active"] is None for item in reports),
        "missing": missing,
        "reports": reports,
    }
    output = args.output or Path("data/raw/quality") / f"scenario-{args.registry.stem}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
