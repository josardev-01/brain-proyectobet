from __future__ import annotations

import argparse
import json
import os
import time
from datetime import UTC, date, datetime
from pathlib import Path

from brain_projectbet.discovery.eligible import (
    discover_eligible_fixtures,
    enrich_eligible_fixtures,
    upcoming_fixture_ids,
)
from brain_projectbet.discovery.storage import save_eligible_fixtures
from brain_projectbet.providers.api_football import ApiFootballProbe
from brain_projectbet.providers.http import ProviderHttpError
from brain_projectbet.strategies.config import DEFAULT_STRATEGY_PATH, load_strategy


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def fixture_ids(payloads: list[dict]) -> set[str]:
    return {
        str(entry.get("fixture", {}).get("id", ""))
        for payload in payloads
        for entry in payload.get("response", [])
        if entry.get("fixture", {}).get("id") is not None
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Descubre favoritos claros para monitoreo")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--daily-reserve", type=int, default=15)
    parser.add_argument(
        "--maximum-fixture-queries",
        type=int,
        default=50,
        help="Amplía cobertura consultando próximos partidos fuera de las primeras páginas",
    )
    parser.add_argument(
        "--request-interval-seconds",
        type=float,
        default=7.0,
        help="Pausa entre consultas para respetar el límite por minuto",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strategy", type=Path, default=DEFAULT_STRATEGY_PATH)
    args = parser.parse_args()
    if args.max_pages <= 0 or args.maximum_fixture_queries < 0 or args.request_interval_seconds < 0:
        parser.error("los límites deben ser positivos y el intervalo no negativo")

    load_dotenv(Path(".env"))
    strategy = load_strategy(args.strategy)
    probe = ApiFootballProbe(os.getenv("API_FOOTBALL_KEY", ""))
    last_request_at: float | None = None

    def request(call):
        nonlocal last_request_at
        if last_request_at is not None:
            wait = args.request_interval_seconds - (time.monotonic() - last_request_at)
            if wait > 0:
                time.sleep(wait)
        try:
            response = call()
        except ProviderHttpError as error:
            if error.status_code != 429:
                raise
            time.sleep(min(max(error.retry_after or 60, 1), 60))
            response = call()
        last_request_at = time.monotonic()
        return response

    payloads = []
    daily_remaining = None
    total_pages = 1
    stopped_reason = None
    for page in range(1, args.max_pages + 1):
        response = request(lambda page=page: probe.prematch_odds_by_date(args.date, page=page))
        limits = response.rate_limits()
        if limits.daily_remaining is not None:
            daily_remaining = limits.daily_remaining
        if response.payload.get("errors"):
            stopped_reason = "provider_rejected_page"
            break
        paging = response.payload.get("paging", {})
        reported_page = int(paging.get("current", page))
        if reported_page != page:
            stopped_reason = "provider_page_mismatch"
            break
        payloads.append(response.payload)
        reported_pages = int(paging.get("total", 1))
        total_pages = max(total_pages, reported_pages)
        if daily_remaining is not None and daily_remaining <= args.daily_reserve:
            stopped_reason = "daily_reserve_reached"
            break
        if page >= total_pages:
            stopped_reason = "all_pages_read"
            break
    if stopped_reason is None and len(payloads) == args.max_pages and args.max_pages < total_pages:
        stopped_reason = "max_pages_reached"
    pages_read = len(payloads)

    fixture_catalog = None
    identities_enriched = False
    fixture_queries = 0
    rejected_fixture_queries = 0
    if payloads and (daily_remaining is None or daily_remaining > args.daily_reserve):
        fixture_catalog = request(lambda: probe.fixtures_by_date(args.date))
        catalog_limits = fixture_catalog.rate_limits()
        if catalog_limits.daily_remaining is not None:
            daily_remaining = catalog_limits.daily_remaining
        covered = fixture_ids(payloads)
        upcoming = upcoming_fixture_ids(fixture_catalog.payload, covered)
        for fixture_id in upcoming[:args.maximum_fixture_queries]:
            if daily_remaining is not None and daily_remaining <= args.daily_reserve:
                break
            response = request(lambda fixture_id=fixture_id: probe.prematch_odds(fixture_id))
            fixture_queries += 1
            limits = response.rate_limits()
            if limits.daily_remaining is not None:
                daily_remaining = limits.daily_remaining
            if response.payload.get("errors"):
                rejected_fixture_queries += 1
                continue
            payloads.append(dict(response.payload))

    discovered_at = datetime.now(UTC)
    result = discover_eligible_fixtures(
        payloads,
        discovered_at=discovered_at,
        policy=strategy.candidate_policy,
    )
    eligible = result.eligible
    if eligible and fixture_catalog is not None:
        eligible = enrich_eligible_fixtures(eligible, fixture_catalog.payload)
        identities_enriched = True
    output = args.output or Path("data/raw/eligible") / f"{args.date}.json"
    save_eligible_fixtures(output, eligible)
    print(json.dumps({
        "date": args.date,
        "strategy_id": strategy.strategy_id,
        "strategy_version": strategy.version,
        "pages_read": pages_read,
        "total_pages_reported": total_pages,
        "stopped_reason": stopped_reason,
        "fixture_queries": fixture_queries,
        "rejected_fixture_queries": rejected_fixture_queries,
        "fixtures_evaluated": result.fixtures_evaluated,
        "eligible_count": len(eligible),
        "team_identities_enriched": identities_enriched,
        "skipped_incomplete_consensus": result.skipped_incomplete_consensus,
        "daily_remaining": daily_remaining,
        "output": str(output),
        "eligible": [
            {
                "fixture_id": fixture.fixture_id,
                "kickoff_at": fixture.kickoff_at.isoformat(),
                "league": fixture.league_name,
                "home": fixture.home_team_name,
                "away": fixture.away_team_name,
                "favorite_side": fixture.favorite_side,
                "favorite_odds": fixture.median_home_odds if fixture.favorite_side == "home" else fixture.median_away_odds,
                "favorite_probability": round(fixture.favorite_probability, 4),
                "bookmakers": fixture.bookmaker_count,
            }
            for fixture in eligible
        ],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
