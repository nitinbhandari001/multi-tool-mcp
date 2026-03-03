import pytest
from unittest.mock import AsyncMock, MagicMock
from multi_tool_mcp.services.database import DatabaseService
from multi_tool_mcp.exceptions import DatabaseError, SQLValidationError

ALLOWED_TABLES = {"demo_users", "demo_orders", "demo_products"}
BLOCKED_KW = {"DROP", "TRUNCATE", "ALTER", "GRANT", "REVOKE"}


def make_db(pool=None):
    if pool is None:
        pool = MagicMock()
    return DatabaseService(pool, ALLOWED_TABLES, BLOCKED_KW)


class FakeRecord:
    """Mimics asyncpg Record: supports .keys() and .values() and indexing."""
    def __init__(self, data: dict):
        self._data = data

    def keys(self):
        return list(self._data.keys())

    def values(self):
        return list(self._data.values())

    def __getitem__(self, key):
        return self._data[key]


async def test_query_returns_results():
    """Query returns QueryResult with correct columns and rows."""
    pool = MagicMock()
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[
        FakeRecord({"id": 1, "name": "Alice"}),
        FakeRecord({"id": 2, "name": "Bob"}),
    ])
    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    db = make_db(pool)
    result = await db.query("SELECT id, name FROM demo_users")

    assert result.columns == ["id", "name"]
    assert result.row_count == 2
    assert result.rows[0] == [1, "Alice"]


async def test_query_auto_limit():
    """Query auto-appends LIMIT if not present."""
    pool = MagicMock()
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    db = make_db(pool)
    await db.query("SELECT * FROM demo_users", limit=5)

    call_args = conn.fetch.call_args[0][0]
    assert "LIMIT 5" in call_args.upper()


async def test_blocked_keywords_rejected():
    """Queries with blocked SQL keywords are rejected."""
    db = make_db()
    # Use a SELECT that embeds a blocked keyword to hit _validate_query (not the SELECT-check)
    with pytest.raises(SQLValidationError):
        await db.query("SELECT * FROM demo_users; DROP TABLE demo_users")


async def test_only_select_allowed_in_query():
    """Only SELECT/WITH queries allowed via query()."""
    db = make_db()
    with pytest.raises(SQLValidationError):
        await db.query("INSERT INTO demo_users VALUES (1, 'x', 'x@x.com', 'user', now())")


async def test_execute_returns_count():
    """execute() returns affected row count."""
    pool = MagicMock()
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value="UPDATE 3")
    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    db = make_db(pool)
    count = await db.execute("UPDATE demo_users SET role = $1 WHERE id = $2", ["admin", 1])
    assert count == 3


async def test_invalid_table_name_rejected():
    """describe_table rejects table names with special characters."""
    db = make_db()
    with pytest.raises(SQLValidationError):
        await db.describe_table("demo_users; DROP TABLE demo_users")


async def test_create_pool_returns_none_on_failure():
    """create_pool returns None (not raises) on connection failure."""
    result = await DatabaseService.create_pool(
        "postgresql://invalid:invalid@localhost:1/nonexistent",
        min_size=1, max_size=2
    )
    assert result is None


async def test_execute_rejects_select():
    """execute() rejects SELECT queries."""
    db = make_db()
    with pytest.raises(SQLValidationError):
        await db.execute("SELECT * FROM demo_users")
