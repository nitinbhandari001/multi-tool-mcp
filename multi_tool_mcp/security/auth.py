"""JWT auth helpers and FastMCP auth callables for multi-tool-mcp."""
import time
from typing import Callable

import jwt
from fastmcp import Context
from fastmcp.server.dependencies import get_access_token

from ..exceptions import AuthorizationError
from .roles import Role, Scope, ROLE_SCOPES, has_scope


def require_scope(scope: Scope) -> Callable:
    """Return an auth callable for use in @mcp.tool(auth=...).

    FastMCP 3.0 auth callables receive (ctx: Context) and raise to deny access.
    Returns None on success.
    """
    async def auth_check(ctx: Context) -> None:
        token = get_access_token()  # None in STDIO mode
        if token is None:
            return  # STDIO mode — skip auth
        role = token.claims.get("role", "")
        if not has_scope(role, scope):
            raise AuthorizationError(
                f"Role '{role}' lacks scope '{scope}'"
            )
    return auth_check


def require_any_auth() -> Callable:
    """Return an auth callable that just checks a token exists."""
    async def auth_check(ctx: Context) -> None:
        token = get_access_token()
        if token is None:
            return  # STDIO mode — skip auth
        # Token present = authenticated
    return auth_check


def generate_token(
    secret: str,
    client_id: str,
    role: str,
    expires_hours: int = 24,
) -> str:
    """Generate HS256 JWT with role and scopes claims."""
    role_enum = Role(role) if role in [r.value for r in Role] else None
    scopes = (
        [s.value for s in ROLE_SCOPES.get(role_enum, set())]
        if role_enum
        else []
    )
    now = int(time.time())
    payload = {
        "sub": client_id,
        "client_id": client_id,
        "role": role,
        "scopes": scopes,
        "iat": now,
        "exp": now + expires_hours * 3600,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(secret: str, token: str) -> dict:
    """Decode and validate JWT. Returns payload dict."""
    return jwt.decode(token, secret, algorithms=["HS256"])
