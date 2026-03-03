from __future__ import annotations
from dataclasses import dataclass
import asyncpg
import httpx
import structlog
from .database import DatabaseService
from .api_proxy import APIProxyService
from .filesystem import FilesystemService
from .ai import AIService
from ..security.audit import AuditLogger
from ..config import Settings
from ..middleware.rate_limiter import TokenBucketLimiter

log = structlog.get_logger(__name__)


@dataclass
class ServiceContainer:
    db: DatabaseService | None  # None if pg connection failed
    api: APIProxyService
    fs: FilesystemService
    ai: AIService
    audit: AuditLogger
    settings: Settings
    _pool: asyncpg.Pool | None
    _http: httpx.AsyncClient

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
        await self._http.aclose()


async def create_services(settings: Settings) -> ServiceContainer:
    """Create all services from settings."""
    # DB pool (graceful fallback if pg unavailable)
    pool = await DatabaseService.create_pool(
        settings.database_url,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
    )
    if pool is None:
        log.warning("db_connection_failed", url=settings.database_url)
        db_service = None
    else:
        allowed_tables = set(settings.allowed_tables.split(","))
        blocked_kw = set(settings.blocked_sql_keywords.split(","))
        db_service = DatabaseService(pool, allowed_tables, blocked_kw)

    # HTTP client
    http_client = httpx.AsyncClient(timeout=settings.api_timeout)

    # Rate limiter (api_rate_limit per second burst)
    limiter = TokenBucketLimiter(rate=settings.api_rate_limit / 60.0, burst=settings.api_rate_limit)

    # API proxy
    allowed_domains = set(settings.allowed_api_domains.split(","))
    api_service = APIProxyService(http_client, allowed_domains, limiter)

    # Filesystem
    allowed_exts = set(settings.allowed_extensions.split(","))
    fs_service = FilesystemService(settings.workspace_root, settings.max_file_size, allowed_exts)

    # AI
    ai_service = AIService.from_settings(settings)

    # Audit logger
    audit = AuditLogger(settings.audit_log_dir)

    return ServiceContainer(
        db=db_service,
        api=api_service,
        fs=fs_service,
        ai=ai_service,
        audit=audit,
        settings=settings,
        _pool=pool,
        _http=http_client,
    )
