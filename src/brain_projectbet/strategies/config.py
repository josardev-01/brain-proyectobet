from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from brain_projectbet.domain.candidates import CandidatePolicy
from brain_projectbet.domain.objectives import ObjectiveDefinition, TargetEvent
from brain_projectbet.rules.favorite_pressure import FavoritePressurePolicy


DEFAULT_STRATEGY_PATH = Path("config/strategies/favorite_losing_pressure_v2.json")
STATUSES = {"HEURÍSTICA", "EXPERIMENTAL", "VALIDADA"}


@dataclass(frozen=True, slots=True)
class StrategyDefinition:
    strategy_id: str
    version: int
    status: str
    objective: ObjectiveDefinition
    candidate_policy: CandidatePolicy
    rule_type: str
    pressure_policy: FavoritePressurePolicy


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} debe ser un objeto")
    return value


def load_strategy(path: Path = DEFAULT_STRATEGY_PATH) -> StrategyDefinition:
    try:
        raw = _mapping(json.loads(path.read_text(encoding="utf-8")), "strategy")
        strategy_id = str(raw["strategy_id"])
        version = int(raw["version"])
        status = str(raw["status"])
        objective_raw = _mapping(raw["objective"], "objective")
        target_raw = _mapping(objective_raw["target"], "objective.target")
        candidate_raw = _mapping(raw["candidate_policy"], "candidate_policy")
        rule_raw = _mapping(raw["rule"], "rule")
        parameters = dict(_mapping(rule_raw.get("parameters", {}), "rule.parameters"))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError(f"configuración de estrategia inválida: {error}") from error

    if not strategy_id.strip() or version <= 0 or status not in STATUSES:
        raise ValueError("identidad, versión o estado de estrategia inválidos")
    rule_type = str(rule_raw.get("type", ""))
    if rule_type != "favorite_pressure":
        raise ValueError(f"tipo de regla no soportado: {rule_type}")

    try:
        target = TargetEvent(
            event_type=str(target_raw["event_type"]),
            horizon_minutes=int(target_raw["horizon_minutes"]),
            subject=str(target_raw.get("subject", "match")),
            attributes=dict(_mapping(target_raw.get("attributes", {}), "target.attributes")),
        )
        objective = ObjectiveDefinition(
            objective_id=str(objective_raw["objective_id"]),
            version=int(objective_raw["version"]),
            target=target,
            preconditions=dict(
                _mapping(objective_raw.get("preconditions", {}), "objective.preconditions")
            ),
            status=str(objective_raw.get("status", status)),
        )
        candidate_policy = CandidatePolicy(**dict(candidate_raw))
        pressure_policy = FavoritePressurePolicy(
            rule_id=str(rule_raw["rule_id"]),
            version=version,
            status=status,
            **parameters,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"configuración de estrategia inválida: {error}") from error
    if target.event_type != "goal" or target.subject != "prematch_favorite":
        raise ValueError("favorite_pressure actualmente requiere un gol del favorito pre-partido")
    return StrategyDefinition(
        strategy_id=strategy_id,
        version=version,
        status=status,
        objective=objective,
        candidate_policy=candidate_policy,
        rule_type=rule_type,
        pressure_policy=pressure_policy,
    )
