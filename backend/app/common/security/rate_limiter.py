"""
Rate Limiter Service for AI School OS.

Provides environment-driven rate limiting with:
1. Atomic Lua script sliding window algorithm executing on Redis server in a single round-trip.
2. Thread-safe in-memory store for development/testing when Redis is not configured.
3. Production-grade Redis backend support with connection pooling.
4. Strict production fail-closed enforcement (no silent in-memory fallback in production).
5. FastAPI dependency integration with atomic check-and-reserve slot acquisition.
"""

import logging
import math
import time
import uuid
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Request
from app.common.exceptions.api_exception import APIException
from app.common.exceptions.error_codes import ErrorCode
from app.core.config import settings

logger = logging.getLogger(__name__)

# Atomic sliding window script in Lua:
# 1. Prunes timestamps older than now - window
# 2. Counts active attempts
# 3. If count >= limit, computes retry_after and returns [1, retry_after, count]
# 4. If count < limit and reserve == 1, atomically adds (member, now) and sets TTL, returning [0, 0, count + 1]
SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
local reserve = tonumber(ARGV[5])
local cutoff = now - window

redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
local count = redis.call('ZCARD', key)

if count >= limit then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 1
    if oldest and #oldest >= 2 then
        local oldest_time = tonumber(oldest[2])
        retry_after = math.ceil(oldest_time + window - now)
        if retry_after < 1 then
            retry_after = 1
        end
    end
    return {1, retry_after, count}
end

if reserve == 1 then
    redis.call('ZADD', key, now, member)
    redis.call('EXPIRE', key, math.ceil(window))
    return {0, 0, count + 1}
else
    return {0, 0, count}
end
"""


class InMemoryRateLimiter:
    """
    Thread-safe atomic sliding window rate limiter for in-memory / test environments.
    """

    def __init__(self):
        self._lock = Lock()
        self._attempts: Dict[str, List[float]] = {}

    def is_limited(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        reserve: bool = False,
    ) -> Tuple[bool, int]:
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = self._attempts.get(key, [])
            # Evict timestamps older than window
            timestamps = [t for t in timestamps if t > cutoff]
            if timestamps:
                self._attempts[key] = timestamps
            else:
                self._attempts.pop(key, None)

            if len(timestamps) >= limit:
                # Calculate retry after
                oldest = timestamps[0]
                retry_after = math.ceil(oldest + window_seconds - now)
                return True, max(1, retry_after)

            if reserve:
                if key not in self._attempts:
                    self._attempts[key] = []
                self._attempts[key].append(now)

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
    Unified Rate Limiter Service supporting in-memory and production-grade distributed Redis backends.
    """

    def __init__(self, redis_client: Optional[Any] = None, redis_url: Optional[str] = None):
        self.memory_limiter = InMemoryRateLimiter()
        self._redis_client = redis_client
        self._redis_pool = None
        self._pool_lock = Lock()
        self._custom_redis_url = redis_url

    def is_production(self) -> bool:
        return settings.ENVIRONMENT.lower() in ("production", "prod")

    def _get_redis_client(self) -> Optional[Any]:
        if self._redis_client is not None:
            return self._redis_client

        redis_url = self._custom_redis_url or settings.REDIS_URL
        if not redis_url:
            if self.is_production():
                raise ValueError("REDIS_URL must be configured in production environment for distributed rate limiting.")
            return None

        with self._pool_lock:
            if self._redis_client is None:
                try:
                    import redis
                    self._redis_pool = redis.ConnectionPool.from_url(
                        redis_url,
                        decode_responses=True,
                        max_connections=50,
                        socket_timeout=2.0,
                        socket_connect_timeout=2.0,
                    )
                    self._redis_client = redis.Redis(connection_pool=self._redis_pool)
                except Exception as exc:
                    logger.error("Failed to initialize Redis rate limiter client: %s", exc)
                    if self.is_production():
                        raise
                    return None
            return self._redis_client

    def ping(self) -> bool:
        """Check Redis connectivity."""
        try:
            client = self._get_redis_client()
            if client is not None:
                return bool(client.ping())
        except Exception:
            return False
        return False

    def acquire(
        self,
        identifier: str,
        limit: int | None = None,
        window_seconds: int | None = None,
    ) -> Tuple[bool, int]:
        """
        Atomically check and reserve a rate limit slot in a single round-trip operation.
        Returns (is_limited, retry_after). If is_limited is False, a slot was reserved.
        """
        return self._execute_sliding_window(
            identifier=identifier,
            limit=limit,
            window_seconds=window_seconds,
            reserve=True,
        )

    def check_rate_limit(
        self,
        identifier: str,
        limit: int | None = None,
        window_seconds: int | None = None,
        reserve: bool = False,
    ) -> Tuple[bool, int]:
        """
        Check rate limit status. By default reserve=False (read-only inspection).
        If reserve=True, atomically reserves a slot if allowed.
        """
        return self._execute_sliding_window(
            identifier=identifier,
            limit=limit,
            window_seconds=window_seconds,
            reserve=reserve,
        )

    def _execute_sliding_window(
        self,
        identifier: str,
        limit: int | None = None,
        window_seconds: int | None = None,
        reserve: bool = False,
    ) -> Tuple[bool, int]:
        effective_limit = limit or settings.LOGIN_RATE_LIMIT
        effective_window = window_seconds or settings.LOGIN_RATE_WINDOW_SECONDS
        key = f"rate_limit:{identifier}" if not (identifier.startswith("rate_limit:") or identifier.startswith("pwd_reset:")) else identifier

        try:
            redis_client = self._get_redis_client()
        except Exception as exc:
            if self.is_production():
                logger.error("Redis client unavailable in production sliding window check: %s", exc)
                return True, effective_window
            redis_client = None

        if redis_client is not None:
            try:
                now = time.time()
                member = f"{now}:{uuid.uuid4().hex}"
                reserve_val = 1 if reserve else 0
                res = redis_client.eval(
                    SLIDING_WINDOW_LUA,
                    1,
                    key,
                    str(now),
                    str(effective_window),
                    str(effective_limit),
                    member,
                    str(reserve_val),
                )
                is_limited = bool(res[0] == 1)
                retry_after = int(res[1])
                return is_limited, retry_after
            except Exception as exc:
                logger.error("Redis error during sliding window check: %s", exc)
                if self.is_production():
                    # Fail-closed in production: reject requests when rate-limiter is unreachable
                    return True, effective_window
                # In development / testing, fallback to in-memory store
                pass

        if self.is_production():
            # Production must never silently use in-memory rate limiting
            logger.error("Production rate limiter accessed without Redis backend; failing closed.")
            return True, effective_window

        return self.memory_limiter.is_limited(key, effective_limit, effective_window, reserve=reserve)

    def record_failure(
        self,
        identifier: str,
        window_seconds: int | None = None,
    ) -> None:
        """
        Record a failure attempt explicitly.
        """
        effective_window = window_seconds or settings.LOGIN_RATE_WINDOW_SECONDS
        key = f"rate_limit:{identifier}" if not (identifier.startswith("rate_limit:") or identifier.startswith("pwd_reset:")) else identifier

        try:
            redis_client = self._get_redis_client()
        except Exception as exc:
            if self.is_production():
                logger.error("Redis client unavailable in production record_failure: %s", exc)
                return
            redis_client = None

        if redis_client is not None:
            try:
                now = time.time()
                unique_member = f"{now}:{uuid.uuid4().hex}"
                pipe = redis_client.pipeline(transaction=True)
                pipe.zadd(key, {unique_member: now})
                pipe.expire(key, effective_window)
                pipe.execute()
                return
            except Exception as exc:
                logger.error("Redis error during record_failure: %s", exc)
                if self.is_production():
                    return
                pass

        if not self.is_production():
            self.memory_limiter.record_attempt(key)

    def reset_attempts(self, identifier: str) -> None:
        key = f"rate_limit:{identifier}" if not (identifier.startswith("rate_limit:") or identifier.startswith("pwd_reset:")) else identifier
        try:
            redis_client = self._get_redis_client()
            if redis_client is not None:
                redis_client.delete(key)
        except Exception as exc:
            logger.warning("Redis error during reset_attempts: %s", exc)

        self.memory_limiter.reset(key)

    def clear_all(self) -> None:
        """Clear all rate limit state (in-memory and test Redis keys)."""
        self.memory_limiter.clear()
        try:
            redis_client = self._get_redis_client()
            if redis_client is not None:
                keys = redis_client.keys("rate_limit:*") + redis_client.keys("pwd_reset:*")
                if keys:
                    redis_client.delete(*keys)
        except Exception:
            pass

    def close(self) -> None:
        """Cleanly close Redis connection pool."""
        with self._pool_lock:
            if self._redis_pool is not None:
                try:
                    self._redis_pool.disconnect()
                except Exception:
                    pass
                self._redis_pool = None
            self._redis_client = None


rate_limiter = RateLimiterService()


def get_client_ip(request: Request) -> str:
    """Extract client IP safely without trusting spoofed X-Forwarded-For headers by default."""
    if getattr(settings, "TRUST_PROXY", False):
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def enforce_login_rate_limit(request: Request) -> None:
    """
    FastAPI dependency that enforces rate limiting on login attempts by client IP.
    Atomically acquires a rate limit reservation slot before authentication proceeds.
    """
    client_ip = get_client_ip(request)
    is_limited, retry_after = rate_limiter.acquire(client_ip)

    if is_limited:
        raise APIException(
            status_code=429,
            code=ErrorCode.TOO_MANY_REQUESTS,
            message="Too many failed login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def enforce_password_reset_rate_limit(request: Request) -> None:
    """
    FastAPI dependency that enforces rate limiting on password reset / recovery requests by client IP.
    Atomically acquires a password reset reservation slot before password reset handling proceeds.
    """
    client_ip = get_client_ip(request)
    limit = settings.PASSWORD_RESET_RATE_LIMIT
    window = settings.PASSWORD_RESET_RATE_WINDOW_SECONDS
    key = f"pwd_reset:{client_ip}"
    is_limited, retry_after = rate_limiter.acquire(key, limit=limit, window_seconds=window)

    if is_limited:
        raise APIException(
            status_code=429,
            code=ErrorCode.TOO_MANY_REQUESTS,
            message="Too many password reset requests. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


