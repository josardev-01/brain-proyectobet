import unittest

from brain_projectbet.providers.base import RateLimitStatus
from brain_projectbet.providers.http import ProviderHttpError
from brain_projectbet.providers.quota import quota_block_reason


class QuotaTests(unittest.TestCase):
    def test_blocks_before_crossing_daily_reserve(self) -> None:
        limits = RateLimitStatus(daily_remaining=16, minute_remaining=8)
        self.assertEqual(
            quota_block_reason(limits, requested=2, daily_reserve=15),
            "daily_reserve",
        )

    def test_blocks_when_minute_has_no_capacity(self) -> None:
        limits = RateLimitStatus(daily_remaining=90, minute_remaining=0)
        self.assertEqual(
            quota_block_reason(limits, requested=1, daily_reserve=15),
            "minute_reserve",
        )

    def test_allows_exact_reserve_boundary(self) -> None:
        limits = RateLimitStatus(daily_remaining=16, minute_remaining=1)
        self.assertIsNone(quota_block_reason(limits, requested=1, daily_reserve=15))

    def test_unknown_headers_do_not_invent_a_limit(self) -> None:
        self.assertIsNone(
            quota_block_reason(RateLimitStatus(), requested=2, daily_reserve=15)
        )

    def test_http_error_is_sanitized(self) -> None:
        error = ProviderHttpError(429, retry_after=30)
        self.assertEqual(error.status_code, 429)
        self.assertEqual(error.retry_after, 30)
        self.assertNotIn("key", str(error))


if __name__ == "__main__":
    unittest.main()
