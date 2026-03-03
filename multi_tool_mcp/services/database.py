import asyncio
import asyncpg
from typing import Any
from ..exceptions import DatabaseError, SQLValidationError
from ..models import QueryResult, TableInfo, ColumnInfo


class DatabaseService:
    def __init__(
        self,
        pool: asyncpg.Pool,
        allowed_tables: set[str],
        blocked_keywords: set[str],
    ):
        self._pool = pool
        self._allowed_tables = allowed_tables
        self._blocked_keywords = blocked_keywords

    def _validate_query(self, sql: str, is_admin: bool = False) -> None:
        """Raise SQLValidationError if query contains blocked keywords (for non-admin)."""
        if is_admin:
            return
        upper = sql.upper()
        for kw in self._blocked_keywords:
            if kw.upper() in upper:
                raise SQLValidationError(f"Blocked keyword in query: {kw}")

    async def query(self, sql: str, params: list | None = None, limit: int = 100) -> QueryResult:
        """Execute SELECT/WITH query. Auto-appends LIMIT if missing."""
        stripped = sql.strip().upper()
        if not (stripped.startswith("SELECT") or stripped.startswith("WITH")):
            raise SQLValidationError("Only SELECT/WITH queries allowed")
        self._validate_query(sql)
        # Auto-append LIMIT
        if "LIMIT" not in stripped:
            sql = f"{sql.rstrip(';')} LIMIT {limit}"
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(sql, *(params or []))
                if not rows:
                    return QueryResult(columns=[], rows=[], row_count=0)
                columns = list(rows[0].keys())
                data = [list(r.values()) for r in rows]
                return QueryResult(columns=columns, rows=data, row_count=len(data))
        except asyncpg.PostgresError as e:
            raise DatabaseError(str(e)) from e

    async def execute(self, sql: str, params: list | None = None) -> int:
        """Execute INSERT/UPDATE/DELETE. Returns affected row count."""
        stripped = sql.strip().upper()
        allowed_ops = ("INSERT", "UPDATE", "DELETE")
        if not any(stripped.startswith(op) for op in allowed_ops):
            raise SQLValidationError("Only INSERT/UPDATE/DELETE allowed via execute()")
        self._validate_query(sql)
        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute(sql, *(params or []))
                # result is like "INSERT 0 3" or "UPDATE 2"
                parts = result.split()
                return int(parts[-1]) if parts else 0
        except asyncpg.PostgresError as e:
            raise DatabaseError(str(e)) from e

    async def list_tables(self) -> list[str]:
        """List tables in the public schema."""
        sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(sql)
                return [r["table_name"] for r in rows]
        except asyncpg.PostgresError as e:
            raise DatabaseError(str(e)) from e

    async def describe_table(self, table: str) -> TableInfo:
        """Return column info for a table."""
        # Validate table name (alphanumeric + underscore only)
        if not table.replace("_", "").isalnum():
            raise SQLValidationError(f"Invalid table name: {table}")
        sql = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(sql, table)
                columns = [
                    ColumnInfo(
                        name=r["column_name"],
                        data_type=r["data_type"],
                        nullable=r["is_nullable"] == "YES",
                        default=r["column_default"],
                    )
                    for r in rows
                ]
                return TableInfo(name=table, schema_name="public", columns=columns)
        except asyncpg.PostgresError as e:
            raise DatabaseError(str(e)) from e

    @staticmethod
    async def create_pool(url: str, min_size: int = 2, max_size: int = 10) -> asyncpg.Pool | None:
        """Create asyncpg pool. Returns None on connection failure (graceful fallback)."""
        try:
            return await asyncpg.create_pool(url, min_size=min_size, max_size=max_size)
        except Exception:
            return None
