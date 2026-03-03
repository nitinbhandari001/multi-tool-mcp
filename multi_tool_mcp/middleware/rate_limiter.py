import asyncio
import time
from ..exceptions import RateLimitExceeded


class TokenBucketLimiter:
    def __init__(self, rate: float, burst: int):
        # rate = tokens per second, burst = max bucket capacity
        self._rate = rate
        self._burst = burst
        self._buckets: dict[str, tuple[float, float]] = {}  # key -> (tokens, last_refill_time)
        self._lock = asyncio.Lock()

    async def acquire(self, key: str) -> bool:
        """Try to acquire a token. Returns True if allowed, False if denied."""
        async with self._lock:
            now = time.monotonic()
            tokens, last = self._buckets.get(key, (float(self._burst), now))
            # Refill: add tokens based on elapsed time
            elapsed = now - last
            tokens = min(float(self._burst), tokens + elapsed * self._rate)
            if tokens >= 1.0:
                self._buckets[key] = (tokens - 1.0, now)
                return True
            else:
                self._buckets[key] = (tokens, now)
                return False

    async def acquire_or_raise(self, key: str) -> None:
        """Acquire token or raise RateLimitExceeded."""
        if not await self.acquire(key):
            raise RateLimitExceeded(f"Rate limit exceeded for '{key}'")

    def get_stats(self) -> dict:
        return {"bucket_count": len(self._buckets), "keys": list(self._buckets.keys())}
