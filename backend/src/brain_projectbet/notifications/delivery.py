from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from brain_projectbet.database.models import (
    AlertRecord,
    NotificationDeliveryRecord,
    NotificationEndpointRecord,
)
from brain_projectbet.domain.alerts import AlertEvent
from brain_projectbet.notifications.base import AlertNotifier
from brain_projectbet.notifications.telegram import TelegramNotifier


NotifierFactory = Callable[[str, str], AlertNotifier]


def _telegram_factory(token: str, destination: str) -> AlertNotifier:
    return TelegramNotifier(token, destination)


def alert_event_from_record(record: AlertRecord) -> AlertEvent:
    allowed = {field.name for field in fields(AlertEvent)}
    payload = {key: value for key, value in record.explanation.items() if key in allowed}
    created_at = payload.get("created_at")
    if isinstance(created_at, str):
        payload["created_at"] = datetime.fromisoformat(created_at)
    return AlertEvent(**payload)


def _refresh_alert_delivery_status(
    session: Session,
    alert: AlertRecord,
    endpoints: list[NotificationEndpointRecord],
) -> None:
    """Keep the alert summary consistent with its per-endpoint receipts."""
    if not endpoints:
        alert.delivery_status = "NO_ENDPOINT"
        session.commit()
        return

    endpoint_ids = [endpoint.id for endpoint in endpoints]
    statuses = list(session.scalars(select(NotificationDeliveryRecord.status).where(
        NotificationDeliveryRecord.alert_id == alert.alert_id,
        NotificationDeliveryRecord.endpoint_id.in_(endpoint_ids),
    )))
    if len(statuses) == len(endpoint_ids) and all(status == "SENT" for status in statuses):
        alert.delivery_status = "SENT"
    elif any(status == "FAILED" for status in statuses):
        alert.delivery_status = "FAILED"
    else:
        alert.delivery_status = "PENDING"
    session.commit()


def deliver_pending_alerts(
    session: Session,
    *,
    telegram_token: str,
    maximum: int = 20,
    notifier_factory: NotifierFactory = _telegram_factory,
) -> dict[str, int]:
    if maximum <= 0:
        raise ValueError("maximum debe ser positivo")
    endpoints = list(session.scalars(select(NotificationEndpointRecord).where(
        NotificationEndpointRecord.enabled.is_(True),
        NotificationEndpointRecord.channel == "telegram",
    )))
    alerts = list(session.scalars(select(AlertRecord).order_by(AlertRecord.created_at)))
    sent = failed = skipped = attempted = 0
    for alert in alerts:
        eligible_endpoints = (
            [endpoint for endpoint in endpoints if endpoint.owner_id == alert.owner_id]
            if alert.owner_id is not None
            else endpoints
        )
        for endpoint in eligible_endpoints:
            delivery = session.scalar(select(NotificationDeliveryRecord).where(
                NotificationDeliveryRecord.alert_id == alert.alert_id,
                NotificationDeliveryRecord.endpoint_id == endpoint.id,
            ))
            if delivery is not None and delivery.status == "SENT":
                skipped += 1
                continue
            if attempted >= maximum:
                _refresh_alert_delivery_status(session, alert, eligible_endpoints)
                return {"attempted": attempted, "sent": sent, "failed": failed, "skipped": skipped}
            now = datetime.now(UTC)
            if delivery is None:
                delivery = NotificationDeliveryRecord(
                    alert_id=alert.alert_id,
                    endpoint_id=endpoint.id,
                    status="PENDING",
                    attempts=0,
                    updated_at=now,
                )
                session.add(delivery)
            delivery.attempts += 1
            delivery.updated_at = now
            attempted += 1
            try:
                notifier_factory(telegram_token, endpoint.destination).send(
                    alert_event_from_record(alert)
                )
            except Exception as error:
                delivery.status = "FAILED"
                delivery.last_error = str(error)[:240]
                failed += 1
            else:
                delivery.status = "SENT"
                delivery.last_error = None
                delivery.sent_at = now
                sent += 1
            session.commit()
        _refresh_alert_delivery_status(session, alert, eligible_endpoints)
    return {"attempted": attempted, "sent": sent, "failed": failed, "skipped": skipped}
