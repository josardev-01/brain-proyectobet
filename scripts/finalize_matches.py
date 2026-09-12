from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from brain_projectbet.backtesting.replay import replay_first_alert
from brain_projectbet.backtesting.results import (
    backtest_record_id,
    build_backtest_record,
    summarize_backtests,
)
from brain_projectbet.backtesting.storage import append_backtest_once, load_backtests
from brain_projectbet.collection.storage import append_snapshot, load_snapshots
from brain_projectbet.discovery.storage import load_eligible_fixtures
from brain_projectbet.domain.models import PrematchOdds
from brain_projectbet.normalization.api_football import normalize_snapshot
from brain_projectbet.orchestration.finalization_state import (
    load_finalization_state,
    save_finalization_state,
)
from brain_projectbet.providers.api_football import ApiFootballProbe
from brain_projectbet.providers.http import ProviderHttpError
from brain_projectbet.providers.quota import quota_block_reason
from brain_projectbet.strategies.config import DEFAULT_STRATEGY_PATH, load_strategy


RESULT_STATUSES = {"FT", "AET", "PEN"}


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Finaliza partidos y registra resultados para backtesting")
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("data/raw/eligible") / f"{date.today().isoformat()}.json",
    )
    parser.add_argument("--results", type=Path, default=Path("data/raw/backtesting/results.jsonl"))
    parser.add_argument("--daily-reserve", type=int, default=15)
    parser.add_argument("--minimum-age-minutes", type=int, default=105)
    parser.add_argument("--maximum-fixtures", type=int, default=3)
    parser.add_argument("--retry-cooldown-minutes", type=int, default=720)
    parser.add_argument(
        "--state",
        type=Path,
        default=Path("data/raw/finalization/state.json"),
    )
    parser.add_argument("--strategy", type=Path, default=DEFAULT_STRATEGY_PATH)
    args = parser.parse_args()
    if args.minimum_age_minutes < 0 or args.maximum_fixtures <= 0 or args.retry_cooldown_minutes <= 0:
        parser.error("edades no negativas, máximo positivo y cooldown mayor que cero")
    if not args.registry.exists():
        parser.error(f"registro no encontrado: {args.registry}")

    load_dotenv(Path(".env"))
    probe = ApiFootballProbe(os.getenv("API_FOOTBALL_KEY", ""))
    fixtures = load_eligible_fixtures(args.registry)
    existing_ids = {record.record_id for record in load_backtests(args.results)}
    strategy = load_strategy(args.strategy)
    objective = strategy.objective
    candidate_policy = strategy.candidate_policy
    rule = strategy.pressure_policy
    now = datetime.now(UTC)
    state = load_finalization_state(args.state)
    processed = []
    daily_remaining = None
    minute_remaining = None
    stopped = None

    due = [
        fixture
        for fixture in fixtures
        if fixture.kickoff_at + timedelta(minutes=args.minimum_age_minutes) <= now
        and state.can_check_fixture(fixture.fixture_id, now=now)
        and backtest_record_id(
            provider=fixture.provider,
            fixture_id=fixture.fixture_id,
            objective_id=objective.objective_id,
            objective_version=objective.version,
            rule_id=rule.rule_id,
            rule_version=rule.version,
        ) not in existing_ids
    ][: args.maximum_fixtures]

    if not state.can_spend(on_date=now.date().isoformat(), requested=1, reserve=args.daily_reserve):
        daily_remaining = state.daily_remaining
        stopped = "daily_reserve_cached"

    for registered in due if stopped is None else []:
        if daily_remaining is not None or minute_remaining is not None:
            reason = quota_block_reason(
                fixture_limits,
                requested=2,
                daily_reserve=args.daily_reserve,
            )
            if reason is not None:
                stopped = reason
                break
        try:
            fixture_response = probe.fixture(registered.fixture_id)
        except ProviderHttpError as error:
            stopped = f"provider_http_{error.status_code}"
            break
        fixture_limits = fixture_response.rate_limits()
        daily_remaining = fixture_limits.daily_remaining
        minute_remaining = fixture_limits.minute_remaining
        if daily_remaining is not None:
            state.quota_date = now.date().isoformat()
            state.daily_remaining = daily_remaining
            save_finalization_state(args.state, state)
        response = fixture_response.payload.get("response", [])
        if not response:
            processed.append({"fixture_id": registered.fixture_id, "status": "fixture_missing"})
            continue
        fixture_payload = response[0]
        match_status = str(fixture_payload.get("fixture", {}).get("status", {}).get("short", "UNKNOWN"))
        if match_status not in RESULT_STATUSES:
            state.deferred_until[registered.fixture_id] = now + timedelta(
                minutes=args.retry_cooldown_minutes,
            )
            save_finalization_state(args.state, state)
            processed.append({"fixture_id": registered.fixture_id, "status": match_status, "finalized": False})
            continue
        state.deferred_until.pop(registered.fixture_id, None)
        reason = quota_block_reason(
            fixture_limits,
            requested=1,
            daily_reserve=args.daily_reserve,
        )
        if reason is not None:
            processed.append({"fixture_id": registered.fixture_id, "status": f"waiting_for_{reason}"})
            stopped = reason
            break

        snapshot_path = Path("data/raw/snapshots") / f"api-football-{registered.fixture_id}.jsonl"
        snapshots = load_snapshots(snapshot_path)
        if not snapshots or snapshots[-1].status not in RESULT_STATUSES:
            terminal_snapshot = normalize_snapshot(fixture_payload, [], captured_at=now)
            append_snapshot(snapshot_path, terminal_snapshot)
            snapshots.append(terminal_snapshot)

        fixture_output = Path("data/raw/fixtures") / f"api-football-{registered.fixture_id}-final.json"
        fixture_output.parent.mkdir(parents=True, exist_ok=True)
        fixture_output.write_text(
            json.dumps(fixture_response.payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        try:
            event_response = probe.fixture_events(registered.fixture_id)
        except ProviderHttpError as error:
            processed.append({
                "fixture_id": registered.fixture_id,
                "status": f"provider_http_{error.status_code}",
                "retry_after": error.retry_after,
            })
            stopped = f"provider_http_{error.status_code}"
            break
        fixture_limits = event_response.rate_limits()
        daily_remaining = fixture_limits.daily_remaining
        minute_remaining = fixture_limits.minute_remaining
        if daily_remaining is not None:
            state.quota_date = now.date().isoformat()
            state.daily_remaining = daily_remaining
        save_finalization_state(args.state, state)
        events = event_response.payload.get("response", [])
        event_output = Path("data/raw/events") / f"api-football-{registered.fixture_id}.json"
        event_output.parent.mkdir(parents=True, exist_ok=True)
        event_output.write_text(
            json.dumps(event_response.payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        odds = PrematchOdds(
            provider="api-football-consensus",
            provider_match_id=registered.fixture_id,
            captured_at=registered.discovered_at,
            home=registered.median_home_odds,
            draw=registered.median_draw_odds,
            away=registered.median_away_odds,
        )
        replay = replay_first_alert(
            snapshots,
            odds,
            objective,
            events,
            candidate_policy=candidate_policy,
            pressure_policy=rule,
        )
        record = build_backtest_record(
            registered,
            replay,
            objective_id=objective.objective_id,
            objective_version=objective.version,
            rule_id=rule.rule_id,
            rule_version=rule.version,
            rule_status=rule.status,
            match_status=match_status,
            finalized_at=now,
        )
        saved = append_backtest_once(args.results, record)
        processed.append({
            "fixture_id": registered.fixture_id,
            "status": match_status,
            "finalized": True,
            "result_saved": saved,
            "snapshots_read": replay.snapshots_read,
            "alert_triggered": replay.first_alert is not None,
            "outcome": replay.first_alert.label.outcome if replay.first_alert else None,
        })

    summary = summarize_backtests(load_backtests(args.results))
    print(json.dumps({
        "due": len(due),
        "strategy_id": strategy.strategy_id,
        "strategy_version": strategy.version,
        "processed": processed,
        "daily_remaining": daily_remaining,
        "minute_remaining": minute_remaining,
        "stopped": stopped,
        "summary": asdict(summary),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
