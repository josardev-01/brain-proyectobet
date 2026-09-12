from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


COMPARISON_OPERATORS = {">", ">=", "<", "<=", "=", "!=", "BETWEEN"}
LOGICAL_OPERATORS = {"AND", "OR", "NOT"}


class InvalidExpression(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExpressionResult:
    matched: bool
    reasons: tuple[str, ...]
    missing_metrics: tuple[str, ...] = ()


def validate_expression(expression: Mapping[str, Any], *, max_depth: int = 8, max_nodes: int = 100) -> None:
    nodes = 0

    def visit(node: Mapping[str, Any], depth: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes:
            raise InvalidExpression(f"la expresión supera {max_nodes} nodos")
        if depth > max_depth:
            raise InvalidExpression(f"la expresión supera {max_depth} niveles")
        if not isinstance(node, Mapping):
            raise InvalidExpression("cada condición debe ser un objeto")

        logical = node.get("logical")
        if logical is not None:
            logical = str(logical).upper()
            if logical not in LOGICAL_OPERATORS:
                raise InvalidExpression(f"operador lógico no soportado: {logical}")
            children = node.get("conditions")
            if not isinstance(children, list) or not children:
                raise InvalidExpression("un grupo lógico requiere condiciones")
            if logical == "NOT" and len(children) != 1:
                raise InvalidExpression("NOT requiere exactamente una condición")
            for child in children:
                visit(child, depth + 1)
            return

        metric = node.get("metric")
        operator = str(node.get("operator", "")).upper()
        if not isinstance(metric, str) or not metric.strip():
            raise InvalidExpression("la condición requiere metric")
        if operator not in COMPARISON_OPERATORS:
            raise InvalidExpression(f"operador no soportado: {operator}")
        if "value" not in node:
            raise InvalidExpression("la condición requiere value")
        if operator == "BETWEEN":
            value = node["value"]
            if not isinstance(value, list) or len(value) != 2:
                raise InvalidExpression("BETWEEN requiere [mínimo, máximo]")

    visit(expression, 1)


def evaluate_expression(expression: Mapping[str, Any], metrics: Mapping[str, Any]) -> ExpressionResult:
    validate_expression(expression)

    def evaluate(node: Mapping[str, Any]) -> ExpressionResult:
        logical = node.get("logical")
        if logical is not None:
            logical = str(logical).upper()
            results = [evaluate(child) for child in node["conditions"]]
            missing = tuple(dict.fromkeys(metric for result in results for metric in result.missing_metrics))
            if logical == "AND":
                matched = all(result.matched for result in results)
            elif logical == "OR":
                matched = any(result.matched for result in results)
            else:
                matched = not results[0].matched
            reasons = tuple(reason for result in results for reason in result.reasons)
            return ExpressionResult(matched, reasons, missing)

        metric = str(node["metric"])
        operator = str(node["operator"]).upper()
        expected = node["value"]
        actual = metrics.get(metric)
        if metric not in metrics or actual is None:
            return ExpressionResult(False, (f"{metric}: dato no disponible",), (metric,))
        try:
            matched = _compare(actual, operator, expected)
        except (TypeError, ValueError) as error:
            raise InvalidExpression(f"comparación inválida para {metric}: {error}") from error
        return ExpressionResult(matched, (f"{metric} {operator} {expected}: {actual}",))

    return evaluate(expression)


def _compare(actual: Any, operator: str, expected: Any) -> bool:
    if operator == "=":
        return actual == expected
    if operator == "!=":
        return actual != expected
    if operator == ">":
        return actual > expected
    if operator == ">=":
        return actual >= expected
    if operator == "<":
        return actual < expected
    if operator == "<=":
        return actual <= expected
    if operator == "BETWEEN":
        return expected[0] <= actual <= expected[1]
    raise InvalidExpression(f"operador no soportado: {operator}")
