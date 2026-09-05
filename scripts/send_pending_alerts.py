from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from brain_projectbet.collection.storage import load_alerts
from brain_projectbet.notifications.storage import (
    DeliveryReceipt,
    append_receipt_once,
    delivered_ids,
    delivery_id,
)
from brain_projectbet.notifications.telegram import TelegramNotifier, format_telegram_alert


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Envía a Telegram alertas todavía no entregadas")
    parser.add_argument("--alerts", type=Path, default=Path("data/raw/alerts.jsonl"))
    parser.add_argument("--receipts", type=Path, default=Path("data/raw/notifications/receipts.jsonl"))
    parser.add_argument("--maximum", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.maximum <= 0:
        parser.error("maximum debe ser positivo")

    load_dotenv(Path(".env"))
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    destination = chat_id or "dry-run"
    sent_ids = delivered_ids(args.receipts)
    pending = [
        alert
        for alert in load_alerts(args.alerts)
        if delivery_id(alert.alert_id, "telegram", destination) not in sent_ids
    ][: args.maximum]
    if args.dry_run:
        print(json.dumps({
            "pending": len(pending),
            "messages": [format_telegram_alert(alert) for alert in pending],
            "sent": 0,
        }, ensure_ascii=False))
        return 0
    if not pending:
        print(json.dumps({"pending": 0, "sent": 0}, ensure_ascii=False))
        return 0
    notifier = TelegramNotifier(token, chat_id)
    sent = 0
    for alert in pending:
        notifier.send(alert)
        receipt = DeliveryReceipt(
            delivery_id=delivery_id(alert.alert_id, notifier.channel, chat_id),
            alert_id=alert.alert_id,
            channel=notifier.channel,
            sent_at=datetime.now(UTC),
        )
        if append_receipt_once(args.receipts, receipt):
            sent += 1
    print(json.dumps({"pending": len(pending), "sent": sent}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
