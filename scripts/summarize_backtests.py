from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from brain_projectbet.backtesting.results import summarize_backtests
from brain_projectbet.backtesting.storage import load_backtests


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume resultados de backtesting disponibles")
    parser.add_argument("--results", type=Path, default=Path("data/raw/backtesting/results.jsonl"))
    args = parser.parse_args()
    print(json.dumps(asdict(summarize_backtests(load_backtests(args.results))), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
