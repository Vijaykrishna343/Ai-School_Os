"""
Rate Limiter Service for AI School OS.

Provides environment-driven rate limiting with:
1. Sliding window / token bucket algorithm.
2. In-memory thread-safe store for test / single-node deployments.
3. Optional Redis backend support if REDIS_URL is configured.
4. FastAPI dependency integration for route throttling.
"""

import math
import time
from threading import Lock
from typing import Dict, List, Tuple

from fastapi import Request
from app.common.exceptions.api_exception import APIException
from app.common.exceptions.error_codes import ErrorCode
from app.core.config import settings


class InMemoryRateLimiter:
    """
    Thread-safe sliding window rate limiter for in-memory / test environments.
    """

    def __init__(self):
        self._lock = Lock()
        self._attempts: Dict[str, List[float]] = {}

    def is_limited(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = self._attempts.get(key, [])
            # Evict timestamps older than window
            timestamps = [t for t in timestamps if t > cutoff]
            self._attempts[key] = timestamps

            if len(timestamps) >= limit:
                # Calculate retry after
                oldest = timestamps[0]
                retry_after = math.ceil(oldest + window_seconds - now)
                return True, max(1, retry_after)

            return False, 0

    def record_attempt(self, key: str) -> None:
        now = time.time()
        with self._lock:
            if key not in self._attempts:
                self._attempts[key] = []
            self._attempts[key].append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._attempts.clear()


class RateLimiterService:
    """
    Unified Rate Limiter Service supporting in-memory and optional Redis backends.
    """

    def __init__(self):
        self.memory_limiter = InMemoryRateLimiter()

    def _get_redis_client(self):
        if not settings.REDIS_URL:
            return None
        try:
            import redis
            return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception:
            return None

    def check_rate_limit(
        self,
        identifier: str,
        limit: int | None = None,
        window_seconds: int | None = None,
    ) -> Tuple[bool, int]:
        effective_limit = limit or settings.LOGIN_RATE_LIMIT
        effective_window = window_seconds or settings.LOGIN_RATE_WINDOW_SECONDS
        key = f"rate_limit:{identifier}"

        redis_client = self._get_redis_client()
        if redis_client:
            try:
                now = time.time()
                cutoff = now - effective_window
                pipe = redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, cutoff)
                pipe.zcard(key)
                pipe.zrange(key, 0, 0, withscores=True)
                results = pipe.execute()

                cardinality = results[1]
                if cardinality >= effective_limit:
                    oldest_score = results[2][0][1] if results[2] else now
                    retry_after = math.ceil(oldest_score + effective_window - now)
                    return True, max(1, retry_after)
                return False, 0
            except Exception:
                # Graceful fallback to in-memory on Redis error
                pass

        return self.memory_limiter.is_limited(key, effective_limit, effective_window)

    def record_failure(
        self,
        identifier: str,
        window_seconds: int | None = None,
    ) -> None:
        effective_window = window_seconds or settings.LOGIN_RATE_WINDOW_SECONDS
        key = f"rate_limit:{identifier}"

        redis_client = self._get_redis_client()
        if redis_client:
            try:
                now = time.time()
                pipe = redis_client.pipeline()
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, effective_window)
                pipe.execute()
                return
            except Exception:
                pass

        self.memory_limiter.record_attempt(key)

    def reset_attempts(self, identifier: str) -> None:
        key = f"rate_limit:{identifier}"
        redis_client = self._get_redis_client()
        if redis_client:
            try:
                redis_client.delete(key)
            except Exception:
                pass

        self.memory_limiter.reset(key)

    def clear_all(self) -> None:
        self.memory_limiter.clear()


rate_limiter = RateLimiterService()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers or remote connection."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def enforce_login_rate_limit(request: Request) -> None:
    """
    FastAPI dependency that enforces rate limiting on login attempts by client IP.
    """
    client_ip = get_client_ip(request)
    is_limited, retry_after = rate_limiter.check_rate_limit(client_ip)

    if is_limited:
        raise APIException(
            status_code=429,
            code=ErrorCode.TOO_MANY_REQUESTS if hasattr(ErrorCode, "TOO_MANY_REQUESTS") else "TOO_MANY_REQUESTS",
            message="Too many failed login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
