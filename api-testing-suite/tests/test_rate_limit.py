"""
Rate Limiting Tests
=====================

Verifies that the rate limiting middleware enforces request quotas,
returns proper 429 responses, and includes the expected headers.
"""

import pytest
from api.rate_limiter import rate_limiter


class TestRateLimiting:
    """Tests for the rate limiting middleware."""

    def test_rate_limit_headers_present(self, client, auth_headers, sample_payment_data):
        """RL-001: Rate limit headers are present on normal responses."""
        resp = client.post("/v1/payments", json=sample_payment_data, headers=auth_headers)
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers
        assert "X-RateLimit-Reset" in resp.headers

    def test_rate_limit_remaining_decreases(self, client, auth_headers):
        """RL-002: Remaining count decreases with each request."""
        resp1 = client.get("/v1/payments", headers=auth_headers)
        remaining1 = int(resp1.headers["X-RateLimit-Remaining"])

        resp2 = client.get("/v1/payments", headers=auth_headers)
        remaining2 = int(resp2.headers["X-RateLimit-Remaining"])

        assert remaining2 < remaining1

    def test_rate_limit_enforced(self, client, auth_headers):
        """RL-003: Exceeding rate limit returns 429."""
        # Use a low-limit key approach: set rate limiter to very low limit
        rate_limiter.default_limit = 5

        # Use readonly key which has rate_limit=50, but we'll just hit
        # the endpoint rapidly. Instead let's manipulate the limiter directly.
        key = "apikey:demo_key_4eC39HqLyjWDarjtT1zdp7dc"

        # Simulate filling up the rate limit bucket
        for _ in range(100):
            rate_limiter.is_rate_limited(key, limit=100)

        # The next request should be rate-limited
        resp = client.get("/v1/payments", headers=auth_headers)
        assert resp.status_code == 429

        error = resp.get_json()["error"]
        assert error["type"] == "rate_limit_error"
        assert "retry_after" in error

    def test_rate_limit_429_has_retry_after(self, client, auth_headers):
        """RL-004: 429 response includes Retry-After header."""
        key = "apikey:demo_key_4eC39HqLyjWDarjtT1zdp7dc"
        for _ in range(100):
            rate_limiter.is_rate_limited(key, limit=100)

        resp = client.get("/v1/payments", headers=auth_headers)
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers

    def test_rate_limit_different_keys_independent(self, client, auth_headers, admin_headers):
        """RL-005: Different API keys have independent rate limits."""
        # Fill up the standard key's bucket
        key = "apikey:demo_key_4eC39HqLyjWDarjtT1zdp7dc"
        for _ in range(100):
            rate_limiter.is_rate_limited(key, limit=100)

        # Standard key is rate-limited
        resp1 = client.get("/v1/payments", headers=auth_headers)
        assert resp1.status_code == 429

        # Admin key should still work
        resp2 = client.get("/v1/payments", headers=admin_headers)
        assert resp2.status_code == 200

    def test_rate_limit_reset_clears_counters(self):
        """RL-006: Resetting the rate limiter clears all counters."""
        key = "test_key"
        rate_limiter.is_rate_limited(key, limit=100)
        rate_limiter.is_rate_limited(key, limit=100)

        assert rate_limiter.get_usage(key) == 2

        rate_limiter.reset(key)
        assert rate_limiter.get_usage(key) == 0

    def test_rate_limit_global_reset(self):
        """RL-007: Global reset clears all keys."""
        rate_limiter.is_rate_limited("key_a", limit=100)
        rate_limiter.is_rate_limited("key_b", limit=100)

        rate_limiter.reset()

        assert rate_limiter.get_usage("key_a") == 0
        assert rate_limiter.get_usage("key_b") == 0

    def test_health_endpoint_not_rate_limited(self, client):
        """RL-008: Health endpoint is not rate-limited."""
        # Health endpoint has no @rate_limit_middleware decorator
        for _ in range(10):
            resp = client.get("/v1/health")
            assert resp.status_code == 200

    def test_rate_limit_shows_correct_limit_value(self, client, auth_headers):
        """RL-009: X-RateLimit-Limit reflects the key's configured limit."""
        resp = client.get("/v1/payments", headers=auth_headers)
        # Standard key has rate_limit=100
        assert resp.headers["X-RateLimit-Limit"] == "100"
