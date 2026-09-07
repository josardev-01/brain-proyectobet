from __future__ import annotations

import argparse
import json
from pathlib import Path

from brain_projectbet.database import models  # noqa: F401
from brain_projectbet.database.session import Base, engine, session_scope
from brain_projectbet.database.sync import sync_alerts, sync_backtests, sync_registry, sync_strategies


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincroniza archivos operativos hacia la base de datos")
    parser.add_argument("--registry", type=Path, action="append", default=[])
    args = parser.parse_args()

    registries = args.registry or sorted(Path("data/raw/eligible").glob("*.json"))
    Base.metadata.create_all(engine)
    totals = {"matches": 0, "snapshots": 0, "strategies": 0, "alerts": 0, "backtests": 0}
    with session_scope() as session:
        for registry in registries:
            synced = sync_registry(session, registry)
            totals["matches"] += synced["matches"]
            totals["snapshots"] += synced["snapshots"]
        totals["strategies"] = sync_strategies(session)
        totals["alerts"] = sync_alerts(session)
        totals["backtests"] = sync_backtests(session)
    print(json.dumps({"registries": len(registries), **totals}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
