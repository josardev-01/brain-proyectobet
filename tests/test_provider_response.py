import unittest

from brain_projectbet.providers.base import ProbeResponse


class ProbeResponseTests(unittest.TestCase):
    def test_reads_remaining_requests_case_insensitively(self) -> None:
        response = ProbeResponse(
            provider="test",
            operation="live",
            elapsed_ms=10,
            payload={},
            response_headers={"X-RateLimit-Requests-Remaining": "42"},
        )
        self.assertEqual(response.remaining_requests(), 42)

    def test_missing_rate_limit_is_unknown(self) -> None:
        response = ProbeResponse("test", "live", 10, {}, {})
        self.assertIsNone(response.remaining_requests())


if __name__ == "__main__":
    unittest.main()
