from __future__ import annotations

import json
from typing import Any, Callable, Mapping
from urllib.request import Request, urlopen

from brain_projectbet.domain.alerts import AlertEvent


PostJson = Callable[[str, Mapping[str, Any], float], Mapping[str, Any]]


def format_telegram_alert(alert: AlertEvent) -> str:
    if alert.strategy_name:
        return _format_user_strategy_alert(alert)
    minute = f"{alert.minute}+{alert.minute_extra}" if alert.minute_extra else str(alert.minute)
    match_name = (
        f"{alert.home_team_name} vs {alert.away_team_name}"
        if alert.home_team_name and alert.away_team_name
        else f"Partido {alert.fixture_id}"
    )
    favorite_name = alert.favorite_team_name or f"Equipo {alert.favorite_team_id}"
    probability = (
        f"{alert.favorite_probability:.1%}" if alert.favorite_probability is not None else "N/D"
    )
    odds = f"{alert.favorite_odds:.2f}" if alert.favorite_odds is not None else "N/D"
    return "\n".join([
        "⚽ FAVORITO BAJO PRESIÓN",
        "",
        match_name,
        f"Minuto: {minute}'",
        f"Marcador del favorito: {alert.score_favorite}-{alert.score_opponent}",
        "",
        f"Favorito: {favorite_name}",
        f"Cuota pre-partido: {odds}",
        f"Probabilidad normalizada: {probability}",
        "",
        "Últimos 10 minutos:",
        f"Tiros: {alert.shots_10m if alert.shots_10m is not None else 'N/D'}",
        f"A puerta: {alert.shots_on_target_10m if alert.shots_on_target_10m is not None else 'N/D'}",
        f"Corners: {alert.corners_10m if alert.corners_10m is not None else 'N/D'}",
        "",
        f"Regla: {alert.rule_id} v{alert.rule_version} ({alert.rule_status})",
    ])


def _display(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _pair_line(label: str, metrics: Mapping[str, object], metric: str) -> str | None:
    values = [
        ("local", metrics.get(f"{metric}_home")),
        ("visitante", metrics.get(f"{metric}_away")),
    ]
    available = [f"{side} {_display(value)}" for side, value in values if value is not None]
    return f"{label}: {' · '.join(available)}" if available else None


def _format_user_strategy_alert(alert: AlertEvent) -> str:
    minute = f"{alert.minute}+{alert.minute_extra}" if alert.minute_extra else str(alert.minute)
    metrics = alert.metrics
    selected = set(alert.alert_fields)
    lines = [
        "⚽ ESTRATEGIA ACTIVADA",
        "",
        alert.strategy_name,
        (
            f"{alert.home_team_name} vs {alert.away_team_name}"
            if alert.home_team_name and alert.away_team_name
            else f"Partido {alert.fixture_id}"
        ),
        f"Minuto: {minute}'",
    ]
    if "score" in selected and alert.score_home is not None and alert.score_away is not None:
        lines.append(f"Marcador: {_display(alert.score_home)}-{_display(alert.score_away)}")
    if "prematch_odds" in selected:
        odds = [
            f"Local {_display(metrics['home_odds'])}" if metrics.get("home_odds") is not None else None,
            f"Empate {_display(metrics['draw_odds'])}" if metrics.get("draw_odds") is not None else None,
            f"Visitante {_display(metrics['away_odds'])}" if metrics.get("away_odds") is not None else None,
        ]
        available_odds = [value for value in odds if value is not None]
        if available_odds:
            lines.extend(["", "Cuotas pre-partido:", " · ".join(available_odds)])
    stat_fields = (
        ("shots", "Tiros", "shots"),
        ("shots_on_target", "Tiros a puerta", "shots_on_target"),
        ("attacks", "Ataques", "attacks"),
        ("dangerous_attacks", "Ataques peligrosos", "dangerous_attacks"),
        ("corners", "Corners", "corners"),
        ("possession", "Posesión", "possession"),
    )
    visible_stats = []
    for field_name, label, metric in stat_fields:
        if field_name in selected:
            line = _pair_line(label, metrics, metric)
            if line is not None:
                visible_stats.append(line)
    if "cards" in selected:
        for label, metric in (("Amarillas", "yellow_cards"), ("Rojas", "red_cards")):
            line = _pair_line(label, metrics, metric)
            if line is not None:
                visible_stats.append(line)
    if visible_stats:
        lines.extend(["", "Estadísticas al activarse:", *visible_stats])
    if "conditions" in selected and alert.reasons:
        lines.extend(["", "Condiciones evaluadas:", *[f"• {reason}" for reason in alert.reasons[:8]]])
    lines.extend(["", f"Estrategia: {alert.rule_id} v{alert.rule_version} ({alert.rule_status})"])
    return "\n".join(lines)


def _post_json(url: str, payload: Mapping[str, Any], timeout: float) -> Mapping[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class TelegramNotifier:
    channel = "telegram"

    def __init__(
        self,
        token: str,
        chat_id: str,
        *,
        timeout: float = 10,
        post_json: PostJson = _post_json,
    ) -> None:
        if not token or not chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID son obligatorios")
        self._url = f"https://api.telegram.org/bot{token}/sendMessage"
        self._chat_id = chat_id
        self._timeout = timeout
        self._post_json = post_json

    def send(self, alert: AlertEvent) -> None:
        try:
            response = self._post_json(
                self._url,
                {"chat_id": self._chat_id, "text": format_telegram_alert(alert)},
                self._timeout,
            )
        except Exception:
            raise RuntimeError("falló la conexión con Telegram; la alerta sigue pendiente") from None
        if response.get("ok") is not True:
            raise RuntimeError("Telegram rechazó la entrega de la alerta")
