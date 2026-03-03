import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx
from multi_tool_mcp.services.api_proxy import APIProxyService
from multi_tool_mcp.middleware.rate_limiter import TokenBucketLimiter
from multi_tool_mcp.exceptions import SSRFError, RateLimitExceeded

ALLOWED = {"api.github.com", "jsonplaceholder.typicode.com", "httpbin.org"}


def make_proxy(client=None, rate=100, burst=100):
    if client is None:
        client = AsyncMock(spec=httpx.AsyncClient)
    limiter = TokenBucketLimiter(rate=rate, burst=burst)
    return APIProxyService(client, ALLOWED, limiter)


def make_response(status=200, body='{"ok": true}', url="https://api.github.com/"):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status
    resp.headers = {"content-type": "application/json"}
    resp.text = body
    resp.url = url
    return resp


async def test_allowed_domain_succeeds():
    """Requests to allowed domains succeed."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=make_response(200))
    proxy = make_proxy(client)
    result = await proxy.get("https://api.github.com/repos/test/test")
    assert result.status_code == 200


async def test_blocked_domain_raises_ssrf():
    """Requests to blocked domains raise SSRFError."""
    proxy = make_proxy()
    with pytest.raises(SSRFError):
        await proxy.get("https://internal.corp.com/secrets")


async def test_non_http_scheme_raises_ssrf():
    """Non-http/https schemes raise SSRFError."""
    proxy = make_proxy()
    with pytest.raises(SSRFError):
        await proxy.get("file:///etc/passwd")


async def test_rate_limit_blocks_after_burst():
    """Rate limiter blocks after burst is exhausted."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=make_response(200))
    proxy = make_proxy(client, rate=0.001, burst=2)

    await proxy.get("https://api.github.com/1")
    await proxy.get("https://api.github.com/2")
    with pytest.raises(RateLimitExceeded):
        await proxy.get("https://api.github.com/3")


async def test_list_allowed_returns_sorted():
    """list_allowed() returns sorted domain list."""
    proxy = make_proxy()
    domains = proxy.list_allowed()
    assert domains == sorted(domains)
    assert "api.github.com" in domains


async def test_post_request():
    """request() works with POST method."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.request = AsyncMock(return_value=make_response(201, '{"created": true}'))
    proxy = make_proxy(client)
    result = await proxy.request("POST", "https://httpbin.org/post", body='{"test": 1}')
    assert result.status_code == 201
