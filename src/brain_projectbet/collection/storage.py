from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from brain_projectbet.domain.models import MatchSnapshot
from brain_projectbet.domain.candidates import CandidateObservation
from brain_projectbet.domain.alerts import AlertEvent


def _json_default(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"tipo no serializable: {type(value).__name__}")


def append_snapshot(path: Path, snapshot: MatchSnapshot) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(asdict(snapshot), ensure_ascii=False, default=_json_default))
        stream.write("\n")


def load_snapshots(path: Path) -> list[MatchSnapshot]:
    if not path.exists():
        return []
    snapshots = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        data["captured_at"] = datetime.fromisoformat(data["captured_at"])
        snapshots.append(MatchSnapshot(**data))
    return snapshots


def append_candidate_once(path: Path, candidate: CandidateObservation) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("candidate_id") == candidate.candidate_id:
                return False
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(asdict(candidate), ensure_ascii=False, default=_json_default))
        stream.write("\n")
    return True


def append_alert_once(path: Path, alert: AlertEvent) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("alert_id") == alert.alert_id:
                return False
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(asdict(alert), ensure_ascii=False, default=_json_default))
        stream.write("\n")
    return True


def load_alerts(path: Path) -> list[AlertEvent]:
    if not path.exists():
        return []
    alerts = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        item["created_at"] = datetime.fromisoformat(item["created_at"])
        alerts.append(AlertEvent(**item))
    return alerts
