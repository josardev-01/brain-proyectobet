import os
import unittest
from unittest.mock import patch

from brain_projectbet.core.settings import get_settings


class SecuritySettingsTests(unittest.TestCase):
    def tearDown(self) -> None:
        get_settings.cache_clear()

    def test_rejects_placeholder_secret_in_production(self) -> None:
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "JWT_SECRET": "replace-with-a-long-random-secret-value",
            "API_CORS_ORIGINS": "https://projectbet.example.com",
        }, clear=False):
            get_settings.cache_clear()
            with self.assertRaisesRegex(RuntimeError, "JWT_SECRET"):
                get_settings()

    def test_rejects_non_https_production_origin(self) -> None:
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "JWT_SECRET": "a-strong-random-secret-that-is-long-enough-2026",
            "API_CORS_ORIGINS": "http://projectbet.example.com",
        }, clear=False):
            get_settings.cache_clear()
            with self.assertRaisesRegex(RuntimeError, "HTTPS"):
                get_settings()

    def test_accepts_explicit_https_production_configuration(self) -> None:
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "JWT_SECRET": "a-strong-random-secret-that-is-long-enough-2026",
            "API_CORS_ORIGINS": "https://projectbet.example.com",
        }, clear=False):
            get_settings.cache_clear()
            settings = get_settings()
            self.assertEqual(settings.environment, "production")


if __name__ == "__main__":
    unittest.main()
