import httpx
from urllib.parse import urlparse
from ..exceptions import SSRFError, RateLimitExceeded
from ..models import APIResponse
from ..middleware.rate_limiter import TokenBucketLimiter


class APIProxyService:
    def __init__(
        self,
        client: httpx.AsyncClient,
        allowed_domains: set[str],
        limiter: TokenBucketLimiter,
    ):
        self._client = client
        self._allowed_domains = allowed_domains
        self._limiter = limiter

    def _validate_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise SSRFError(f"Scheme '{parsed.scheme}' not allowed. Use http/https.")
        hostname = parsed.hostname or ""
        if hostname not in self._allowed_domains:
            raise SSRFError(f"Domain '{hostname}' not in allowlist")
        return url

    async def get(self, url: str, headers: dict | None = None) -> APIResponse:
        validated = self._validate_url(url)
        hostname = urlparse(validated).hostname or url
        await self._limiter.acquire_or_raise(hostname)
        try:
            resp = await self._client.get(validated, headers=headers or {})
            return APIResponse(
                status_code=resp.status_code,
                headers=dict(resp.headers),
                body=resp.text,
                url=str(resp.url),
            )
        except httpx.RequestError as e:
            raise SSRFError(str(e)) from e

    async def request(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        body: str | None = None,
    ) -> APIResponse:
        validated = self._validate_url(url)
        hostname = urlparse(validated).hostname or url
        await self._limiter.acquire_or_raise(hostname)
        try:
            resp = await self._client.request(
                method.upper(),
                validated,
                headers=headers or {},
                content=body,
            )
            return APIResponse(
                status_code=resp.status_code,
                headers=dict(resp.headers),
                body=resp.text,
                url=str(resp.url),
            )
        except httpx.RequestError as e:
            raise SSRFError(str(e)) from e

    def list_allowed(self) -> list[str]:
        return sorted(self._allowed_domains)
