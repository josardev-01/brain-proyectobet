import unittest

from brain_projectbet.rules.expression import InvalidExpression, evaluate_expression, validate_expression


class RuleExpressionTests(unittest.TestCase):
    def test_evaluates_nested_and_or_expression(self) -> None:
        expression = {
            "logical": "AND",
            "conditions": [
                {"metric": "favorite_is_losing", "operator": "=", "value": True},
                {"logical": "OR", "conditions": [
                    {"metric": "sot_last_10", "operator": ">=", "value": 2},
                    {"metric": "corners_last_10", "operator": ">=", "value": 3},
                ]},
            ],
        }
        result = evaluate_expression(expression, {
            "favorite_is_losing": True, "sot_last_10": 1, "corners_last_10": 4,
        })
        self.assertTrue(result.matched)
        self.assertEqual(result.missing_metrics, ())

    def test_missing_metric_fails_closed_and_is_explained(self) -> None:
        result = evaluate_expression(
            {"metric": "xg_last_10", "operator": ">", "value": .5}, {}
        )
        self.assertFalse(result.matched)
        self.assertEqual(result.missing_metrics, ("xg_last_10",))

    def test_between_is_inclusive(self) -> None:
        expression = {"metric": "minute", "operator": "BETWEEN", "value": [45, 90]}
        self.assertTrue(evaluate_expression(expression, {"minute": 45}).matched)
        self.assertTrue(evaluate_expression(expression, {"minute": 90}).matched)

    def test_not_requires_one_child(self) -> None:
        with self.assertRaises(InvalidExpression):
            validate_expression({"logical": "NOT", "conditions": [
                {"metric": "red_card", "operator": "=", "value": True},
                {"metric": "minute", "operator": ">", "value": 45},
            ]})

    def test_rejects_unknown_operator(self) -> None:
        with self.assertRaises(InvalidExpression):
            validate_expression({"metric": "shots", "operator": "CONTAINS", "value": 2})


if __name__ == "__main__":
    unittest.main()
