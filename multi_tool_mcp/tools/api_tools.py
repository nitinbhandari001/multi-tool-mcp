"""API proxy tools — 3 MCP tools for outbound HTTP requests."""
from multi_tool_mcp.security import require_scope, Scope
from multi_tool_mcp.security.audit import audit_tool
from multi_tool_mcp.tools import get_container


def register(mcp) -> None:

    @mcp.tool(auth=require_scope(Scope.api_read), tags={"api", "read"})
    @audit_tool("api", "get")
    async def api_get(url: str, headers: dict | None = None) -> str:
        """Make a GET request to an allowed API endpoint."""
        container = get_container()
        if container is None:
            return "Service unavailable"
        try:
            resp = await container.api.get(url, headers)
            return f"HTTP {resp.status_code}\n\n{resp.body}"
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool(auth=require_scope(Scope.api_write), tags={"api", "write"})
    @audit_tool("api", "request")
    async def api_request(
        method: str, url: str, headers: dict | None = None, body: str | None = None
    ) -> str:
        """Make an HTTP request (GET/POST/PUT/PATCH/DELETE) to an allowed API endpoint."""
        container = get_container()
        if container is None:
            return "Service unavailable"
        try:
            resp = await container.api.request(method, url, headers, body)
            return f"HTTP {resp.status_code}\n\n{resp.body}"
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool(auth=require_scope(Scope.api_read), tags={"api", "read"})
    @audit_tool("api", "list_allowed")
    async def list_allowed_apis() -> str:
        """List the API domains that this server is allowed to access."""
        container = get_container()
        if container is None:
            return "Service unavailable"
        domains = container.api.list_allowed()
        return "Allowed API domains:\n" + "\n".join(f"  - {d}" for d in domains)
