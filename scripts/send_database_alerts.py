from __future__ import annotations

import argparse
import json
import os

from dotenv import load_dotenv

from brain_projectbet.database.session import session_scope
from brain_projectbet.notifications.delivery import deliver_pending_alerts


def main() -> int:
    parser = argparse.ArgumentParser(description="Entrega alertas de base de datos a destinos Telegram")
    parser.add_argument("--maximum", type=int, default=20)
    args = parser.parse_args()
    if args.maximum <= 0:
        parser.error("maximum debe ser positivo")
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print(json.dumps({"stopped": "telegram_token_missing"}))
        return 2
    with session_scope() as session:
        result = deliver_pending_alerts(session, telegram_token=token, maximum=args.maximum)
    print(json.dumps(result))
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
