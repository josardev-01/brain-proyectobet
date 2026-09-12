from __future__ import annotations

import argparse
from datetime import UTC, datetime
from getpass import getpass

from sqlalchemy import select

from brain_projectbet.core.security import hash_password
from brain_projectbet.database.models import NotificationEndpointRecord, UserRecord
from brain_projectbet.database.session import session_scope


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crea o promueve el administrador inicial")
    parser.add_argument("--email", required=True)
    parser.add_argument("--display-name", default="Administrador")
    parser.add_argument("--telegram-chat-id")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    password = getpass("Contraseña del administrador: ")
    confirmation = getpass("Repite la contraseña: ")
    if password != confirmation:
        raise SystemExit("las contraseñas no coinciden")
    if len(password) < 10:
        raise SystemExit("la contraseña debe tener al menos 10 caracteres")

    email = args.email.strip().lower()
    now = datetime.now(UTC)
    with session_scope() as session:
        user = session.scalar(select(UserRecord).where(UserRecord.email == email))
        if user is None:
            user = UserRecord(
                email=email,
                display_name=args.display_name.strip(),
                password_hash=hash_password(password),
                active=True,
                role="ADMIN",
                approval_status="APPROVED",
                reviewed_at=now,
                created_at=now,
            )
            session.add(user)
            action = "creado"
        else:
            user.display_name = args.display_name.strip()
            user.password_hash = hash_password(password)
            user.active = True
            user.role = "ADMIN"
            user.approval_status = "APPROVED"
            user.reviewed_at = now
            action = "actualizado"
        session.flush()
        if args.telegram_chat_id:
            endpoint = session.scalar(select(NotificationEndpointRecord).where(
                NotificationEndpointRecord.owner_id == user.id,
                NotificationEndpointRecord.channel == "telegram",
                NotificationEndpointRecord.destination == args.telegram_chat_id,
            ))
            if endpoint is None:
                session.add(NotificationEndpointRecord(
                    owner_id=user.id,
                    channel="telegram",
                    destination=args.telegram_chat_id,
                    label="Telegram principal",
                    enabled=True,
                    created_at=now,
                ))
            else:
                endpoint.enabled = True
    print(f"administrador {action}: {email}")


if __name__ == "__main__":
    main()
