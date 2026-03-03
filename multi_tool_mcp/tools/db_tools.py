"""Database tools — 6 MCP tools for DB read/write operations."""
from multi_tool_mcp.security import require_scope, Scope
from multi_tool_mcp.security.audit import audit_tool
from multi_tool_mcp.tools import get_container


def register(mcp) -> None:

    @mcp.tool(auth=require_scope(Scope.db_read), tags={"database", "read"})
    @audit_tool("database", "query")
    async def query_database(sql: str, params: list | None = None, limit: int = 100) -> str:
        """Execute a SELECT query against the database."""
        container = get_container()
        if container is None or container.db is None:
            return "Database unavailable"
        try:
            result = await container.db.query(sql, params, limit)
            if result.row_count == 0:
                return "No results"
            header = " | ".join(result.columns)
            sep = "-" * len(header)
            rows = [" | ".join(str(v) for v in row) for row in result.rows]
            return f"{header}\n{sep}\n" + "\n".join(rows) + f"\n\n({result.row_count} rows)"
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool(auth=require_scope(Scope.db_read), tags={"database", "read"})
    @audit_tool("database", "list_tables")
    async def list_tables() -> str:
        """List all tables in the database."""
        container = get_container()
        if container is None or container.db is None:
            return "Database unavailable"
        try:
            tables = await container.db.list_tables()
            return "\n".join(tables) if tables else "No tables found"
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool(auth=require_scope(Scope.db_read), tags={"database", "read"})
    @audit_tool("database", "describe")
    async def describe_table(table: str) -> str:
        """Describe the columns of a database table."""
        container = get_container()
        if container is None or container.db is None:
            return "Database unavailable"
        try:
            info = await container.db.describe_table(table)
            lines = [f"Table: {info.name} (schema: {info.schema_name})", ""]
            for col in info.columns:
                null_str = "NULL" if col.nullable else "NOT NULL"
                default_str = f" DEFAULT {col.default}" if col.default else ""
                lines.append(f"  {col.name}: {col.data_type} {null_str}{default_str}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool(auth=require_scope(Scope.db_write), tags={"database", "write"})
    @audit_tool("database", "insert")
    async def insert_record(table: str, data: dict) -> str:
        """Insert a record into a database table."""
        container = get_container()
        if container is None or container.db is None:
            return "Database unavailable"
        if not table.replace("_", "").isalnum():
            return f"Error: Invalid table name: {table}"
        try:
            cols = list(data.keys())
            vals = list(data.values())
            placeholders = ", ".join(f"${i+1}" for i in range(len(cols)))
            col_names = ", ".join(cols)
            sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
            count = await container.db.execute(sql, vals)
            return f"Inserted {count} record(s) into {table}"
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool(auth=require_scope(Scope.db_write), tags={"database", "write"})
    @audit_tool("database", "update")
    async def update_record(table: str, data: dict, where_col: str, where_val: str) -> str:
        """Update records in a database table."""
        container = get_container()
        if container is None or container.db is None:
            return "Database unavailable"
        if not table.replace("_", "").isalnum():
            return f"Error: Invalid table name: {table}"
        try:
            cols = list(data.keys())
            vals = list(data.values())
            set_clause = ", ".join(f"{c} = ${i+1}" for i, c in enumerate(cols))
            where_idx = len(cols) + 1
            sql = f"UPDATE {table} SET {set_clause} WHERE {where_col} = ${where_idx}"
            count = await container.db.execute(sql, vals + [where_val])
            return f"Updated {count} record(s) in {table}"
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool(auth=require_scope(Scope.db_write), tags={"database", "write"})
    @audit_tool("database", "delete")
    async def delete_record(table: str, where_col: str, where_val: str) -> str:
        """Delete records from a database table."""
        container = get_container()
        if container is None or container.db is None:
            return "Database unavailable"
        if not table.replace("_", "").isalnum():
            return f"Error: Invalid table name: {table}"
        try:
            sql = f"DELETE FROM {table} WHERE {where_col} = $1"
            count = await container.db.execute(sql, [where_val])
            return f"Deleted {count} record(s) from {table}"
        except Exception as e:
            return f"Error: {e}"
