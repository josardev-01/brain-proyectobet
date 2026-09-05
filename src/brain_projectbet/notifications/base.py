from __future__ import annotations

from typing import Protocol

from brain_projectbet.domain.alerts import AlertEvent


class AlertNotifier(Protocol):
    channel: str

    def send(self, alert: AlertEvent) -> None:
        """Entrega una alerta o lanza una excepción para permitir reintento."""
