"""Security module - RBAC, JWT auth, audit logging."""
from .roles import Role, Scope, ROLE_SCOPES, has_scope
from .auth import require_scope, require_any_auth, generate_token, decode_token
from .audit import AuditLogger, audit_tool

__all__ = [
    "Role", "Scope", "ROLE_SCOPES", "has_scope",
    "require_scope", "require_any_auth",
    "generate_token", "decode_token",
    "AuditLogger", "audit_tool",
]
