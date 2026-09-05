from __future__ import annotations

import argparse
import json
import os
import time
from datetime import UTC, date, datetime
from pathlib import Path

from brain_projectbet.collection.series import derive_window
from brain_projectbet.collection.storage import (
    append_alert_once,
    append_candidate_once,
    append_snapshot,
    load_snapshots,
)
from brain_projectbet.discovery.storage import load_eligible_fixtures
from brain_projectbet.domain.alerts import AlertEvent, trigger_once_alert_id
from brain_projectbet.domain.candidates import CandidatePolicy, observe_candidate
from brain_projectbet.domain.models import PrematchOdds
from brain_projectbet.domain.objectives import FAVORITE_GOAL_WITHIN_10M_V1
from brain_projectbet.monitoring.selection import needs_statistics_sample, select_live_eligible
from brain_projectbet.normalization.api_football import normalize_snapshot
from brain_projectbet.providers.api_football import ApiFootballProbe
from brain_projectbet.rules.favorite_pressure import evaluate_favorite_pressure


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitorea automáticamente favoritos elegibles")
    parser.add_argument("--registry", type=Path, default=Path("data/raw/eligible") / f"{date.today().isoformat()}.json")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--interval-seconds", type=int, default=120)
    parser.add_argument("--maximum-matches", type=int, default=3)
    parser.add_argument("--daily-reserve", type=int, default=15)
    args = parser.parse_args()
    if args.cycles <= 0 or args.interval_seconds <= 0 or args.maximum_matches <= 0:
        parser.error("cycles, interval-seconds y maximum-matches deben ser positivos")
    if not args.registry.exists():
        parser.error(f"registro no encontrado: {args.registry}")

    load_dotenv(Path(".env"))
    probe = ApiFootballProbe(os.getenv("API_FOOTBALL_KEY", ""))
    eligible = load_eligible_fixtures(args.registry)
    policy = CandidatePolicy()

    for cycle in range(1, args.cycles + 1):
        live = probe.live_matches()
        selected = select_live_eligible(
            live.payload,
            eligible,
            warmup_minute=policy.warmup_minute,
            maximum_matches=args.maximum_matches,
        )
        selected_for_statistics = []
        for registered, fixture_payload in selected:
            snapshot_path = Path("data/raw/snapshots") / f"api-football-{registered.fixture_id}.jsonl"
            if needs_statistics_sample(
                registered,
                fixture_payload,
                has_snapshots=bool(load_snapshots(snapshot_path)),
                minimum_minute=policy.minimum_minute,
            ):
                selected_for_statistics.append((registered, fixture_payload))
        daily_remaining = live.rate_limits().daily_remaining
        required_for_stats = len(selected_for_statistics)
        if daily_remaining is not None and daily_remaining - required_for_stats < args.daily_reserve:
            print(json.dumps({
                "cycle": cycle,
                "stopped": "daily_reserve",
                "daily_remaining": daily_remaining,
                "required_for_stats": required_for_stats,
            }))
            break

        cycle_results = []
        for registered, fixture_payload in selected_for_statistics:
            statistics = probe.fixture_statistics(registered.fixture_id)
            snapshot = normalize_snapshot(
                fixture_payload,
                statistics.payload.get("response", []),
                captured_at=datetime.now(UTC),
            )
            snapshot_path = Path("data/raw/snapshots") / f"api-football-{registered.fixture_id}.jsonl"
            append_snapshot(snapshot_path, snapshot)
            odds = PrematchOdds(
                provider="api-football-consensus",
                provider_match_id=registered.fixture_id,
                captured_at=registered.discovered_at,
                home=registered.median_home_odds,
                draw=registered.median_draw_odds,
                away=registered.median_away_odds,
            )
            candidate = observe_candidate(
                snapshot,
                odds,
                FAVORITE_GOAL_WITHIN_10M_V1,
                policy=policy,
            )
            candidate_saved = False
            decision = None
            alert_saved = False
            if candidate is not None:
                candidate_path = Path("data/raw/candidates") / f"api-football-{registered.fixture_id}.jsonl"
                candidate_saved = append_candidate_once(candidate_path, candidate)
                window = derive_window(load_snapshots(snapshot_path), window_minutes=10)
                decision = evaluate_favorite_pressure(candidate, snapshot, window)
                if decision.should_alert:
                    favorite_suffix = "home" if candidate.favorite_side == "home" else "away"
                    team_names = (snapshot.raw_metadata or {}).get("team_names", {})
                    home_name = str(team_names.get("home", {}).get("name", ""))
                    away_name = str(team_names.get("away", {}).get("name", ""))
                    alert = AlertEvent(
                        alert_id=trigger_once_alert_id(
                            candidate,
                            rule_id=decision.rule_id,
                            rule_version=decision.rule_version,
                        ),
                        candidate_id=candidate.candidate_id,
                        fixture_id=candidate.fixture_id,
                        favorite_team_id=candidate.favorite_team_id,
                        rule_id=decision.rule_id,
                        rule_version=decision.rule_version,
                        created_at=datetime.now(UTC),
                        minute=candidate.minute,
                        minute_extra=candidate.minute_extra,
                        score_favorite=candidate.score_favorite,
                        score_opponent=candidate.score_opponent,
                        objective_id=candidate.objective_id,
                        objective_version=candidate.objective_version,
                        rule_status=decision.status,
                        home_team_name=home_name,
                        away_team_name=away_name,
                        favorite_team_name=home_name if favorite_suffix == "home" else away_name,
                        favorite_odds=candidate.favorite_odds,
                        favorite_probability=candidate.favorite_probability,
                        shots_10m=window.deltas.get(f"shots_{favorite_suffix}") if window else None,
                        shots_on_target_10m=(
                            window.deltas.get(f"shots_on_target_{favorite_suffix}") if window else None
                        ),
                        corners_10m=window.deltas.get(f"corners_{favorite_suffix}") if window else None,
                    )
                    alert_saved = append_alert_once(Path("data/raw/alerts.jsonl"), alert)
            cycle_results.append({
                "fixture_id": registered.fixture_id,
                "minute": snapshot.minute,
                "extra": snapshot.minute_extra,
                "status": snapshot.status,
                "candidate_active": candidate.episode_active if candidate else False,
                "candidate_saved": candidate_saved,
                "should_alert": decision.should_alert if decision else False,
                "alert_saved": alert_saved,
                "reasons": decision.reasons if decision else ("candidate_unavailable",),
            })
            stats_remaining = statistics.rate_limits().daily_remaining
            if stats_remaining is not None:
                daily_remaining = stats_remaining

        print(json.dumps({
            "cycle": cycle,
            "eligible_registered": len(eligible),
            "live_selected": len(selected),
            "statistics_selected": len(selected_for_statistics),
            "daily_remaining": daily_remaining,
            "results": cycle_results,
        }, ensure_ascii=False))
        if daily_remaining is not None and daily_remaining <= args.daily_reserve:
            break
        if cycle < args.cycles:
            time.sleep(args.interval_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
