from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from brain_projectbet.collection.storage import load_snapshots
from brain_projectbet.quality.audit import summarize_quality


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita cobertura temporal y campos normalizados")
    parser.add_argument("--snapshots-dir", type=Path, default=Path("data/raw/snapshots"))
    parser.add_argument("--output", type=Path, default=Path("data/raw/quality/report.json"))
    args = parser.parse_args()
    paths = sorted(args.snapshots_dir.glob("*.jsonl")) if args.snapshots_dir.exists() else []
    summary = summarize_quality(load_snapshots(path) for path in paths)
    payload = asdict(summary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
