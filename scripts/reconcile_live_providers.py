from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, date, datetime
from pathlib import Path

from brain_projectbet.collection.storage import append_snapshot
from brain_projectbet.discovery.storage import load_eligible_fixtures
from brain_projectbet.monitoring.reconciliation import reconcile_apifootball_live
from brain_projectbet.normalization.apifootball_com import normalize_snapshot
from brain_projectbet.providers.apifootball_com import ApiFootballComProbe


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cruza candidatos API-Football con el feed live de APIFootball"
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("data/raw/eligible") / f"{date.today().isoformat()}.json",
    )
    parser.add_argument(
        "--write-snapshots",
        action="store_true",
        help="Guarda snapshots enlazados; sin esta opción solo informa coincidencias",
    )
    args = parser.parse_args()
    if not args.registry.exists():
        parser.error(f"registro no encontrado: {args.registry}")

    load_dotenv(Path(".env"))
    live = ApiFootballComProbe(os.getenv("APIFOOTBALL_KEY", "")).live_matches()
    result = reconcile_apifootball_live(
        load_eligible_fixtures(args.registry), live.payload
    )
    captured_at = datetime.now(UTC)
    written = []
    if args.write_snapshots:
        for link in result.links:
            snapshot = normalize_snapshot(
                link.live_fixture,
                captured_at=captured_at,
                canonical_provider=link.eligible.provider,
                canonical_match_id=link.eligible.fixture_id,
            )
            path = Path("data/raw/snapshots") / (
                f"{link.eligible.provider}-{link.eligible.fixture_id}.jsonl"
            )
            append_snapshot(path, snapshot)
            written.append(str(path))

    print(json.dumps({
        "provider": "apifootball-com",
        "live_received": len(live.payload.get("response", [])),
        "matched": len(result.links),
        "unmatched": list(result.unmatched_fixture_ids),
        "ambiguous": list(result.ambiguous_fixture_ids),
        "links": [{
            "api_football_fixture_id": link.eligible.fixture_id,
            "apifootball_match_id": str(link.live_fixture.get("match_id", "")),
            "home": link.live_fixture.get("match_hometeam_name"),
            "away": link.live_fixture.get("match_awayteam_name"),
            "confidence": round(link.confidence, 4),
        } for link in result.links],
        "snapshots_written": written,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
