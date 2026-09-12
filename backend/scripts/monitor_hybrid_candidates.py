from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

from dotenv import load_dotenv

from brain_projectbet.collection.series import derive_window
from brain_projectbet.collection.storage import (
    append_alert_once,
    append_candidate_once,
    append_snapshot,
    load_snapshots,
)
from brain_projectbet.discovery.storage import load_eligible_fixtures
from brain_projectbet.domain.alerts import AlertEvent, trigger_once_alert_id
from brain_projectbet.domain.candidates import observe_candidate
from brain_projectbet.domain.models import PrematchOdds
from brain_projectbet.monitoring.reconciliation import reconcile_apifootball_live
from brain_projectbet.normalization.apifootball_com import normalize_snapshot
from brain_projectbet.providers.apifootball_com import ApiFootballComProbe
from brain_projectbet.rules.favorite_pressure import evaluate_favorite_pressure
from brain_projectbet.strategies.config import DEFAULT_STRATEGY_PATH, load_strategy


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Monitorea odds de API-Football con estadísticas live de APIFootball"
    )
    parser.add_argument(
        "--registry", type=Path,
        default=Path("data/raw/eligible") / f"{date.today().isoformat()}.json",
    )
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--interval-seconds", type=int, default=120)
    parser.add_argument("--daily-reserve", type=int, default=15)
    parser.add_argument("--strategy", type=Path, default=DEFAULT_STRATEGY_PATH)
    args = parser.parse_args()
    if args.cycles <= 0 or args.interval_seconds <= 0:
        parser.error("cycles e interval-seconds deben ser positivos")
    if not args.registry.exists():
        parser.error(f"registro no encontrado: {args.registry}")

    load_dotenv()
    probe = ApiFootballComProbe(os.getenv("APIFOOTBALL_KEY", ""))
    eligible = load_eligible_fixtures(args.registry)
    strategy = load_strategy(args.strategy)

    for cycle in range(1, args.cycles + 1):
        live = probe.live_matches()
        reconciliation = reconcile_apifootball_live(eligible, live.payload)
        results = []
        for link in reconciliation.links:
            snapshot = normalize_snapshot(
                link.live_fixture,
                captured_at=datetime.now(UTC),
                canonical_provider=link.eligible.provider,
                canonical_match_id=link.eligible.fixture_id,
            )
            snapshot = replace(
                snapshot,
                home_team_id=link.eligible.home_team_id or snapshot.home_team_id,
                away_team_id=link.eligible.away_team_id or snapshot.away_team_id,
            )
            if snapshot.minute is None or snapshot.minute < strategy.candidate_policy.warmup_minute:
                continue
            snapshot_path = Path("data/raw/snapshots") / (
                f"{link.eligible.provider}-{link.eligible.fixture_id}.jsonl"
            )
            append_snapshot(snapshot_path, snapshot)
            odds = PrematchOdds(
                provider="api-football-consensus",
                provider_match_id=link.eligible.fixture_id,
                captured_at=link.eligible.discovered_at,
                home=link.eligible.median_home_odds,
                draw=link.eligible.median_draw_odds,
                away=link.eligible.median_away_odds,
            )
            candidate = observe_candidate(
                snapshot, odds, strategy.objective, policy=strategy.candidate_policy
            )
            decision = None
            candidate_saved = alert_saved = False
            if candidate is not None:
                candidate_saved = append_candidate_once(
                    Path("data/raw/candidates") /
                    f"{link.eligible.provider}-{link.eligible.fixture_id}.jsonl",
                    candidate,
                )
                window = derive_window(
                    load_snapshots(snapshot_path),
                    window_minutes=strategy.pressure_policy.window_minutes,
                )
                decision = evaluate_favorite_pressure(
                    candidate, snapshot, window, policy=strategy.pressure_policy
                )
                if decision.should_alert:
                    favorite = candidate.favorite_side
                    alert = AlertEvent(
                        alert_id=trigger_once_alert_id(
                            candidate, rule_id=decision.rule_id,
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
                        home_team_name=link.eligible.home_team_name,
                        away_team_name=link.eligible.away_team_name,
                        favorite_team_name=(
                            link.eligible.home_team_name if favorite == "home"
                            else link.eligible.away_team_name
                        ),
                        favorite_odds=candidate.favorite_odds,
                        favorite_probability=candidate.favorite_probability,
                        shots_10m=window.deltas.get(f"shots_{favorite}") if window else None,
                        shots_on_target_10m=(
                            window.deltas.get(f"shots_on_target_{favorite}") if window else None
                        ),
                        corners_10m=window.deltas.get(f"corners_{favorite}") if window else None,
                    )
                    alert_saved = append_alert_once(Path("data/raw/alerts.jsonl"), alert)
            results.append({
                "fixture_id": link.eligible.fixture_id,
                "source_match_id": link.live_fixture.get("match_id"),
                "minute": snapshot.minute,
                "status": snapshot.status,
                "candidate_active": candidate.episode_active if candidate else False,
                "candidate_saved": candidate_saved,
                "should_alert": decision.should_alert if decision else False,
                "alert_saved": alert_saved,
                "reasons": decision.reasons if decision else ("candidate_unavailable",),
            })
        print(json.dumps({
            "cycle": cycle,
            "live_received": len(live.payload.get("response", [])),
            "matched": len(reconciliation.links),
            "unmatched": list(reconciliation.unmatched_fixture_ids),
            "ambiguous": list(reconciliation.ambiguous_fixture_ids),
            "results": results,
        }, ensure_ascii=False))
        if cycle < args.cycles:
            time.sleep(args.interval_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
