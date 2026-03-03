import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from multi_tool_mcp.services import ServiceContainer
from multi_tool_mcp.security.audit import AuditLogger
from multi_tool_mcp.middleware.rate_limiter import TokenBucketLimiter

JWT_SECRET = "test-secret-for-development-only-32chars"


@pytest.fixture
def jwt_secret():
    return JWT_SECRET


@pytest.fixture
def admin_token(jwt_secret):
    from multi_tool_mcp.security.auth import generate_token
    return generate_token(jwt_secret, "admin-user", "admin")


@pytest.fixture
def viewer_token(jwt_secret):
    from multi_tool_mcp.security.auth import generate_token
    return generate_token(jwt_secret, "viewer-user", "viewer")


@pytest.fixture
def mock_db_pool():
    pool = MagicMock()
    pool.acquire = MagicMock()
    return pool


@pytest.fixture
def mock_httpx_client():
    import httpx
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace with test files."""
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "test.txt").write_text("Hello test")
    return tmp_path


@pytest.fixture
async def audit_logger(tmp_path):
    return AuditLogger(str(tmp_path / "audit_logs"))


@pytest.fixture
def mock_container(audit_logger, temp_workspace):
    """Create a mock ServiceContainer for testing tools."""
    from multi_tool_mcp.services.filesystem import FilesystemService
    from multi_tool_mcp.config import Settings

    settings = Settings(workspace_root=str(temp_workspace))
    fs = FilesystemService(str(temp_workspace), 10485760, {".txt", ".md", ".csv", ".json"})

    container = MagicMock(spec=ServiceContainer)
    container.audit = audit_logger
    container.fs = fs
    container.settings = settings
    container.db = None
    container.api = MagicMock()
    container.api.list_allowed.return_value = ["api.github.com"]
    container.api.get = AsyncMock()
    container.ai = MagicMock()

    return container
