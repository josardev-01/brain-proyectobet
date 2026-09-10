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
    context: dict[str, Any] | None = None,
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
    metrics.update(context or {})
    scope = config.get("scope", {})
    league = str(metrics.get("league_name", ""))
    country = str(metrics.get("country", ""))
    included = {str(item).casefold() for item in scope.get("leagues_included", [])}
    excluded = {str(item).casefold() for item in scope.get("leagues_excluded", [])}
    countries = {str(item).casefold() for item in scope.get("countries_included", [])}
    scope_reasons = []
    if included and league.casefold() not in included:
        scope_reasons.append("league_not_included")
    if league.casefold() in excluded:
        scope_reasons.append("league_excluded")
    if countries and country.casefold() not in countries:
        scope_reasons.append("country_not_included")
    if scope_reasons:
        return StrategyRuntimeResult(
            matched=False,
            reasons=tuple(scope_reasons),
            missing_metrics=(),
            metrics=metrics,
        )
    result: ExpressionResult = evaluate_expression(expression, metrics)
    return StrategyRuntimeResult(
        matched=result.matched,
        reasons=result.reasons,
        missing_metrics=result.missing_metrics,
        metrics=metrics,
    )
