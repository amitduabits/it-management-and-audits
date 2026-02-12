"""
Rate Limiting Middleware
=========================

Simple in-memory rate limiting using a sliding window counter algorithm.
Tracks request counts per API key with configurable limits and windows.
"""

import time
import threading
from functools import wraps
from flask import request, jsonify, g


class RateLimiter:
    """
    Thread-safe in-memory rate limiter.

    Uses a sliding window approach: each key gets a list of timestamps.
    Expired timestamps are pruned on every check.
    """

    def __init__(self, default_limit=60, window_seconds=60):
        self._lock = threading.Lock()
        self._requests = {}  # key -> list of timestamps
        self.default_limit = default_limit
        self.window_seconds = window_seconds

    def _prune(self, key, now):
        """Remove timestamps older than the window."""
        cutoff = now - self.window_seconds
        self._requests[key] = [
            ts for ts in self._requests.get(key, []) if ts > cutoff
        ]

    def is_rate_limited(self, key, limit=None):
        """
        Check if a key has exceeded its rate limit.

        Returns:
            (is_limited, remaining, reset_at)
        """
        limit = limit or self.default_limit
        now = time.time()

        with self._lock:
            self._prune(key, now)

            timestamps = self._requests.get(key, [])
            current_count = len(timestamps)

            if current_count >= limit:
                # Rate limited
                oldest = timestamps[0] if timestamps else now
                reset_at = oldest + self.window_seconds
                return True, 0, reset_at

            # Record this request
            if key not in self._requests:
                self._requests[key] = []
            self._requests[key].append(now)

            remaining = limit - current_count - 1
            reset_at = now + self.window_seconds
            return False, remaining, reset_at

    def get_usage(self, key):
        """Return current usage stats for a key without recording a request."""
        now = time.time()
        with self._lock:
            self._prune(key, now)
            count = len(self._requests.get(key, []))
        return count

    def reset(self, key=None):
        """Reset rate limit counters. If key is None, reset all."""
        with self._lock:
            if key:
                self._requests.pop(key, None)
            else:
                self._requests.clear()


# ---------------------------------------------------------------------------
# Global rate limiter instance
# ---------------------------------------------------------------------------
rate_limiter = RateLimiter(default_limit=60, window_seconds=60)


def rate_limit_middleware(f):
    """
    Flask decorator that enforces rate limiting on an endpoint.

    The limit is determined by the authenticated API key's rate_limit
    setting, falling back to the default (60 req/min).

    Rate limit headers are added to every response:
        X-RateLimit-Limit
        X-RateLimit-Remaining
        X-RateLimit-Reset
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Determine the rate limit key (API key or IP)
        api_key = getattr(g, "api_key", None)
        key_data = getattr(g, "key_data", None)

        if api_key:
            limiter_key = f"apikey:{api_key}"
            limit = key_data.get("rate_limit", 60) if key_data else 60
        else:
            limiter_key = f"ip:{request.remote_addr}"
            limit = rate_limiter.default_limit

        is_limited, remaining, reset_at = rate_limiter.is_rate_limited(
            limiter_key, limit=limit
        )

        if is_limited:
            response = jsonify({
                "error": {
                    "type": "rate_limit_error",
                    "message": (
                        f"Rate limit exceeded. You have made too many "
                        f"requests. Limit: {limit} requests per "
                        f"{rate_limiter.window_seconds} seconds. "
                        f"Please retry after the reset time."
                    ),
                    "status": 429,
                    "retry_after": max(1, int(reset_at - time.time())),
                }
            })
            response.status_code = 429
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(reset_at))
            response.headers["Retry-After"] = str(
                max(1, int(reset_at - time.time()))
            )
            return response

        # Call the actual view function
        response = f(*args, **kwargs)

        # If the view returned a tuple (body, status) or similar, normalise
        if isinstance(response, tuple):
            from flask import make_response
            response = make_response(*response)

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_at))

        return response

    return decorated
