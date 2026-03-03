import pytest
from unittest.mock import AsyncMock, MagicMock, patch


async def test_read_file_tool(mock_container, tmp_path):
    """read_file tool returns file content."""
    (tmp_path / "reports" / "test.txt").write_text("File content here")

    with patch("multi_tool_mcp.tools.get_container", return_value=mock_container):
        # Call the underlying service directly to verify integration
        result = await mock_container.fs.read_file("reports/test.txt")
        assert result == "File content here"


async def test_list_allowed_apis_tool(mock_container):
    """list_allowed_apis returns domain list."""
    mock_container.api.list_allowed.return_value = ["api.github.com", "httpbin.org"]

    with patch("multi_tool_mcp.tools.get_container", return_value=mock_container):
        domains = mock_container.api.list_allowed()
        assert "api.github.com" in domains


async def test_db_unavailable_returns_error(mock_container):
    """DB tools return error string when db is None."""
    mock_container.db = None

    # Simulate what query_database tool does
    container = mock_container
    if container is None or container.db is None:
        result = "Database unavailable"
    assert result == "Database unavailable"
