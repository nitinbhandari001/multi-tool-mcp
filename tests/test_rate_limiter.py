import pytest
from multi_tool_mcp.middleware.rate_limiter import TokenBucketLimiter
from multi_tool_mcp.exceptions import RateLimitExceeded


async def test_acquire_up_to_burst():
    """Can acquire tokens up to burst capacity."""
    limiter = TokenBucketLimiter(rate=10.0, burst=5)
    # Should allow burst=5 tokens
    for _ in range(5):
        assert await limiter.acquire("test-key") is True


async def test_deny_after_exhausted():
    """Denies when bucket is empty."""
    limiter = TokenBucketLimiter(rate=0.001, burst=2)  # Very slow refill
    await limiter.acquire("key")
    await limiter.acquire("key")
    # Bucket empty — next should fail
    result = await limiter.acquire("key")
    assert result is False


async def test_acquire_or_raise_raises():
    """acquire_or_raise raises RateLimitExceeded when denied."""
    limiter = TokenBucketLimiter(rate=0.001, burst=1)
    await limiter.acquire_or_raise("key")  # Uses up the 1 token
    with pytest.raises(RateLimitExceeded):
        await limiter.acquire_or_raise("key")
