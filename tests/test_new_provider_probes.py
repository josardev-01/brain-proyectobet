import unittest
from unittest.mock import patch

from brain_projectbet.providers.apifootball_com import ApiFootballComProbe
from brain_projectbet.providers.goal_api import GoalApiProbe


class GoalApiProbeTests(unittest.TestCase):
    @patch("brain_projectbet.providers.goal_api.get_json")
    def test_live_uses_bearer_auth_and_maps_daily_quota(self, get_json) -> None:
        get_json.return_value = (
            {"success": True, "data": []},
            12.5,
            {
                "X-RateLimit-Type": "DAILY",
                "X-RateLimit-Limit": "1000",
                "X-RateLimit-Remaining": "998",
            },
        )

        result = GoalApiProbe("secret").live_matches()

        args, kwargs = get_json.call_args
        self.assertEqual(args[0], "https://api.goal-api.com/v1/fixtures/live")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer secret")
        self.assertEqual(kwargs["headers"]["User-Agent"], "ProjectBet/0.1")
        self.assertEqual(result.rate_limits().daily_limit, 1000)
        self.assertEqual(result.rate_limits().daily_remaining, 998)
        self.assertIsNone(result.rate_limits().minute_limit)

    def test_rejects_missing_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "GOAL_API_KEY"):
            GoalApiProbe("")


class ApiFootballComProbeTests(unittest.TestCase):
    @patch("brain_projectbet.providers.apifootball_com.get_json")
    def test_live_uses_server_side_key_and_array_wrapper(self, get_json) -> None:
        get_json.return_value = ({"response": []}, 8.0, {})

        result = ApiFootballComProbe("secret").live_matches()

        args, kwargs = get_json.call_args
        self.assertEqual(args[0], "https://apiv3.apifootball.com/")
        self.assertEqual(kwargs["query"]["action"], "get_events")
        self.assertEqual(kwargs["query"]["match_live"], "1")
        self.assertEqual(kwargs["query"]["APIkey"], "secret")
        self.assertEqual(kwargs["array_root_key"], "response")
        self.assertEqual(result.provider, "apifootball-com")

    def test_rejects_missing_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "APIFOOTBALL_KEY"):
            ApiFootballComProbe("")


if __name__ == "__main__":
    unittest.main()
