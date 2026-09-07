from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from brain_projectbet.collection.series import derive_window
from brain_projectbet.domain.models import MatchSnapshot
from brain_projectbet.rules.expression import ExpressionResult, InvalidExpression, evaluate_expression
from brain_projectbet.rules.metrics import build_rule_metrics


@dataclass(frozen=True, slots=True)
class StrategyRuntimeResult:
    matched: bool
    reasons: tuple[str, ...]
    missing_metrics: tuple[str, ...]
    metrics: dict[str, Any]


def evaluate_strategy_config(
    config: dict[str, Any],
    snapshots: Iterable[MatchSnapshot],
    *,
    favorite_side: str,
) -> StrategyRuntimeResult:
    ordered = sorted(
        snapshots,
        key=lambda snapshot: (snapshot.captured_at, snapshot.minute or -1),
    )
    if not ordered:
        raise InvalidExpression("el partido no tiene snapshots")
    conditions = config.get("conditions")
    if not conditions:
        raise InvalidExpression("la estrategia no contiene condiciones declarativas")
    expression = conditions if isinstance(conditions, dict) else {
        "logical": "AND", "conditions": conditions,
    }
    window_minutes = int(
        config.get("feature_window_minutes")
        or config.get("rule", {}).get("parameters", {}).get("window_minutes")
        or 10
    )
    window = derive_window(ordered, window_minutes=window_minutes)
    metrics = build_rule_metrics(ordered[-1], window, favorite_side=favorite_side)
    result: ExpressionResult = evaluate_expression(expression, metrics)
    return StrategyRuntimeResult(
        matched=result.matched,
        reasons=result.reasons,
        missing_metrics=result.missing_metrics,
        metrics=metrics,
    )
