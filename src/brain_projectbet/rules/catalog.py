from __future__ import annotations


STRATEGY_CATALOG = {
    "objectives": [
        {"value": "goal", "label": "Gol"},
        {"value": "corner", "label": "Corner"},
        {"value": "card", "label": "Tarjeta"},
    ],
    "subjects": [
        {"value": "prematch_favorite", "label": "Favorito pre-partido"},
        {"value": "home", "label": "Equipo local"},
        {"value": "away", "label": "Equipo visitante"},
        {"value": "either", "label": "Cualquiera"},
    ],
    "operators": [">=", ">", "=", "<=", "<", "!=", "BETWEEN"],
    "windows": [5, 10, 15],
    "metrics": [
        {"value": "minute", "label": "Minuto", "group": "Partido", "type": "number"},
        {"value": "favorite_is_losing", "label": "Favorito va perdiendo", "group": "Partido", "type": "boolean"},
        {"value": "score_difference", "label": "Diferencia de goles del favorito", "group": "Partido", "type": "number"},
        {"value": "favorite_odds", "label": "Cuota pre-partido del favorito", "group": "Pre-partido", "type": "number"},
        {"value": "favorite_probability", "label": "Probabilidad normalizada del favorito", "group": "Pre-partido", "type": "number"},
        {"value": "favorite_shots_on_target_last_{window}", "label": "Tiros a puerta del favorito", "group": "Ventana reciente", "type": "number"},
        {"value": "favorite_shots_last_{window}", "label": "Tiros del favorito", "group": "Ventana reciente", "type": "number"},
        {"value": "favorite_shots_off_target_last_{window}", "label": "Tiros fuera del favorito", "group": "Ventana reciente", "type": "number"},
        {"value": "favorite_attacks_last_{window}", "label": "Ataques del favorito", "group": "Ventana reciente", "type": "number"},
        {"value": "favorite_dangerous_attacks_last_{window}", "label": "Ataques peligrosos del favorito", "group": "Ventana reciente", "type": "number"},
        {"value": "favorite_corners_last_{window}", "label": "Corners del favorito", "group": "Ventana reciente", "type": "number"},
        {"value": "favorite_possession", "label": "Posesión actual del favorito", "group": "Acumulado", "type": "number"},
        {"value": "favorite_yellow_cards", "label": "Amarillas del favorito", "group": "Acumulado", "type": "number"},
        {"value": "favorite_red_cards", "label": "Rojas del favorito", "group": "Acumulado", "type": "number"},
        {"value": "opponent_shots_on_target_last_{window}", "label": "Tiros a puerta del rival", "group": "Ventana reciente", "type": "number"},
        {"value": "opponent_dangerous_attacks_last_{window}", "label": "Ataques peligrosos del rival", "group": "Ventana reciente", "type": "number"},
        {"value": "opponent_corners_last_{window}", "label": "Corners del rival", "group": "Ventana reciente", "type": "number"},
    ],
    "alert_fields": [
        {"value": "score", "label": "Marcador"},
        {"value": "prematch_odds", "label": "Cuota pre-partido"},
        {"value": "shots", "label": "Tiros"},
        {"value": "shots_on_target", "label": "Tiros a puerta"},
        {"value": "attacks", "label": "Ataques"},
        {"value": "dangerous_attacks", "label": "Ataques peligrosos"},
        {"value": "corners", "label": "Corners"},
        {"value": "possession", "label": "Posesión"},
        {"value": "cards", "label": "Tarjetas"},
    ],
}
