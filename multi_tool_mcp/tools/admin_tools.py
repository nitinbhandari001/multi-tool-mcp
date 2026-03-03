"""Admin tools — 4 MCP tools for server administration."""
from multi_tool_mcp.security import require_scope, Scope
from multi_tool_mcp.security.audit import audit_tool
from multi_tool_mcp.tools import get_container


def register(mcp) -> None:

    @mcp.tool(auth=require_scope(Scope.admin), tags={"admin"})
    @audit_tool("admin", "view_audit")
    async def view_audit_log(
        limit: int = 50, resource: str | None = None, status: str | None = None
    ) -> str:
        """View the audit log (admin only)."""
        container = get_container()
        if container is None:
            return "Service unavailable"
        try:
            entries = await container.audit.query(limit=limit, resource=resource, status=status)
            if not entries:
                return "No audit entries found"
            lines = []
            for e in entries:
                result = "OK" if e.success else "FAIL"
                lines.append(
                    f"[{e.timestamp}] {result} {e.user}({e.role}) "
                    f"{e.tool} {e.resource}/{e.operation} {e.duration_ms:.1f}ms"
                )
                if e.detail:
                    lines.append(f"  Detail: {e.detail}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool(auth=require_scope(Scope.admin), tags={"admin"})
    @audit_tool("admin", "server_status")
    async def server_status() -> str:
        """Get server status and service health (admin only)."""
        container = get_container()
        if container is None:
            return "Server initializing"
        db_status = "connected" if container.db is not None else "unavailable"
        ai_status = "configured" if container.ai._providers else "no providers configured"
        rate_stats = container.api._limiter.get_stats()
        return (
            f"Server Status\n"
            f"=============\n"
            f"Database: {db_status}\n"
            f"AI Service: {ai_status}\n"
            f"API Rate Limiter: {rate_stats['bucket_count']} active buckets\n"
            f"Audit Entries: {len(container.audit._entries)}\n"
            f"Workspace: {container.settings.workspace_root}"
        )

    @mcp.tool(auth=require_scope(Scope.admin), tags={"admin"})
    @audit_tool("admin", "generate_summary")
    async def generate_summary(resource: str) -> str:
        """Generate an AI summary of recent activity for a resource (admin only)."""
        container = get_container()
        if container is None:
            return "Service unavailable"
        try:
            entries = await container.audit.query(limit=20, resource=resource)
            if not entries:
                return f"No recent activity for resource: {resource}"
            summary_input = "\n".join(
                f"{e.timestamp}: {e.tool} by {e.user} - {'success' if e.success else 'failure'}"
                for e in entries
            )
            result = await container.ai.call_llm(
                system="You are an enterprise security analyst. Summarize the following audit log entries concisely.",
                user=f"Resource: {resource}\n\nActivity:\n{summary_input}",
            )
            return result or "AI service unavailable for summary generation"
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool(tags={"admin"})
    async def whoami() -> str:
        """Return the current user's identity and permissions (no auth required)."""
        try:
            from fastmcp.server.dependencies import get_access_token
            token = get_access_token()
            if token is None:
                return "Running in STDIO mode - no authentication"
            from multi_tool_mcp.security.roles import ROLE_SCOPES, Role
            role_str = token.claims.get("role", "unknown")
            try:
                role_enum = Role(role_str)
                scopes = sorted(s.value for s in ROLE_SCOPES.get(role_enum, set()))
            except ValueError:
                scopes = token.claims.get("scopes", [])
            return (
                f"Client ID: {token.client_id}\n"
                f"Role: {role_str}\n"
                f"Scopes: {', '.join(scopes)}"
            )
        except Exception as e:
            return f"Error: {e}"
