from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DeliveryReceipt:
    delivery_id: str
    alert_id: str
    channel: str
    sent_at: datetime


def delivery_id(alert_id: str, channel: str, destination: str) -> str:
    destination_hash = hashlib.sha256(destination.encode("utf-8")).hexdigest()[:16]
    return f"{alert_id}:{channel}:{destination_hash}"


def delivered_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        json.loads(line)["delivery_id"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def append_receipt_once(path: Path, receipt: DeliveryReceipt) -> bool:
    if receipt.delivery_id in delivered_ids(path):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(receipt)
    payload["sent_at"] = receipt.sent_at.isoformat()
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False))
        stream.write("\n")
    return True
