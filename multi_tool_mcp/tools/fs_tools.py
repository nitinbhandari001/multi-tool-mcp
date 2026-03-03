"""Filesystem tools — 5 MCP tools for workspace file operations."""
from multi_tool_mcp.security import require_scope, Scope
from multi_tool_mcp.security.audit import audit_tool
from multi_tool_mcp.tools import get_container


def register(mcp) -> None:

    @mcp.tool(auth=require_scope(Scope.fs_read), tags={"filesystem", "read"})
    @audit_tool("filesystem", "read")
    async def read_file(path: str) -> str:
        """Read a file from the workspace."""
        container = get_container()
        if container is None:
            return "Service unavailable"
        try:
            return await container.fs.read_file(path)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool(auth=require_scope(Scope.fs_write), tags={"filesystem", "write"})
    @audit_tool("filesystem", "write")
    async def write_file(path: str, content: str) -> str:
        """Write content to a file in the workspace."""
        container = get_container()
        if container is None:
            return "Service unavailable"
        try:
            return await container.fs.write_file(path, content)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool(auth=require_scope(Scope.fs_read), tags={"filesystem", "read"})
    @audit_tool("filesystem", "list")
    async def list_directory(path: str = ".") -> str:
        """List files and directories in the workspace."""
        container = get_container()
        if container is None:
            return "Service unavailable"
        try:
            entries = await container.fs.list_directory(path)
            if not entries:
                return f"Empty directory: {path}"
            lines = []
            for e in entries:
                prefix = "[DIR]" if e.is_dir else "[FILE]"
                size_str = f" ({e.size} bytes)" if e.size is not None else ""
                lines.append(f"{prefix} {e.name}{size_str}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool(auth=require_scope(Scope.fs_read), tags={"filesystem", "read"})
    @audit_tool("filesystem", "info")
    async def file_info(path: str) -> str:
        """Get metadata about a file or directory in the workspace."""
        container = get_container()
        if container is None:
            return "Service unavailable"
        try:
            entry = await container.fs.file_info(path)
            kind = "Directory" if entry.is_dir else "File"
            size_str = f"\nSize: {entry.size} bytes" if entry.size is not None else ""
            return (
                f"Name: {entry.name}\nType: {kind}\nPath: {entry.path}"
                f"{size_str}\nModified: {entry.modified}"
            )
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool(auth=require_scope(Scope.fs_admin), tags={"filesystem", "admin"})
    @audit_tool("filesystem", "delete")
    async def delete_file(path: str) -> str:
        """Delete a file from the workspace (admin only)."""
        container = get_container()
        if container is None:
            return "Service unavailable"
        try:
            return await container.fs.delete_file(path)
        except Exception as e:
            return f"Error: {e}"
