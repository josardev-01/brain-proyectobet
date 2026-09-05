from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, date, datetime
from pathlib import Path

from brain_projectbet.discovery.eligible import discover_eligible_fixtures
from brain_projectbet.discovery.storage import save_eligible_fixtures
from brain_projectbet.providers.api_football import ApiFootballProbe
from brain_projectbet.strategies.config import DEFAULT_STRATEGY_PATH, load_strategy


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Descubre favoritos claros para monitoreo")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--daily-reserve", type=int, default=15)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strategy", type=Path, default=DEFAULT_STRATEGY_PATH)
    args = parser.parse_args()
    if args.max_pages <= 0:
        parser.error("max-pages debe ser positivo")

    load_dotenv(Path(".env"))
    strategy = load_strategy(args.strategy)
    probe = ApiFootballProbe(os.getenv("API_FOOTBALL_KEY", ""))
    payloads = []
    daily_remaining = None
    total_pages = 1
    for page in range(1, args.max_pages + 1):
        response = probe.prematch_odds_by_date(args.date, page=page)
        payloads.append(response.payload)
        limits = response.rate_limits()
        daily_remaining = limits.daily_remaining
        total_pages = int(response.payload.get("paging", {}).get("total", 1))
        if daily_remaining is not None and daily_remaining <= args.daily_reserve:
            break
        if page >= total_pages:
            break

    discovered_at = datetime.now(UTC)
    result = discover_eligible_fixtures(
        payloads,
        discovered_at=discovered_at,
        policy=strategy.candidate_policy,
    )
    output = args.output or Path("data/raw/eligible") / f"{args.date}.json"
    save_eligible_fixtures(output, result.eligible)
    print(json.dumps({
        "date": args.date,
        "strategy_id": strategy.strategy_id,
        "strategy_version": strategy.version,
        "pages_read": len(payloads),
        "total_pages_reported": total_pages,
        "fixtures_evaluated": result.fixtures_evaluated,
        "eligible_count": len(result.eligible),
        "skipped_incomplete_consensus": result.skipped_incomplete_consensus,
        "daily_remaining": daily_remaining,
        "output": str(output),
        "eligible": [
            {
                "fixture_id": fixture.fixture_id,
                "kickoff_at": fixture.kickoff_at.isoformat(),
                "league": fixture.league_name,
                "favorite_side": fixture.favorite_side,
                "favorite_odds": fixture.median_home_odds if fixture.favorite_side == "home" else fixture.median_away_odds,
                "favorite_probability": round(fixture.favorite_probability, 4),
                "bookmakers": fixture.bookmaker_count,
            }
            for fixture in result.eligible
        ],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
