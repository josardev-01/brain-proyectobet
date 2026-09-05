import unittest

from brain_projectbet.providers.base import ProbeResponse


class ProbeResponseTests(unittest.TestCase):
    def test_distinguishes_daily_and_minute_limits(self) -> None:
        response = ProbeResponse(
            provider="test",
            operation="live",
            elapsed_ms=10,
            payload={},
            response_headers={
                "x-ratelimit-requests-limit": "100",
                "x-ratelimit-requests-remaining": "94",
                "X-RateLimit-Limit": "10",
                "X-RateLimit-Remaining": "7",
            },
        )
        limits = response.rate_limits()
        self.assertEqual(limits.daily_limit, 100)
        self.assertEqual(limits.daily_remaining, 94)
        self.assertEqual(limits.minute_limit, 10)
        self.assertEqual(limits.minute_remaining, 7)

    def test_missing_rate_limit_is_unknown(self) -> None:
        response = ProbeResponse("test", "live", 10, {}, {})
        limits = response.rate_limits()
        self.assertIsNone(limits.daily_remaining)
        self.assertIsNone(limits.minute_remaining)


if __name__ == "__main__":
    unittest.main()
