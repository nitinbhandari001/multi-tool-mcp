"""RBAC roles and scopes for multi-tool-mcp."""
from enum import StrEnum
from typing import FrozenSet


class Role(StrEnum):
    viewer = "viewer"
    analyst = "analyst"
    developer = "developer"
    admin = "admin"


class Scope(StrEnum):
    db_read = "db:read"
    db_write = "db:write"
    db_admin = "db:admin"
    api_read = "api:read"
    api_write = "api:write"
    fs_read = "fs:read"
    fs_write = "fs:write"
    fs_admin = "fs:admin"
    admin = "admin"


_VIEWER_SCOPES: FrozenSet[Scope] = frozenset({
    Scope.db_read,
    Scope.api_read,
    Scope.fs_read,
})

_ANALYST_SCOPES: FrozenSet[Scope] = _VIEWER_SCOPES | frozenset({
    Scope.db_write,
    Scope.api_write,
})

_DEVELOPER_SCOPES: FrozenSet[Scope] = _ANALYST_SCOPES | frozenset({
    Scope.fs_write,
    Scope.fs_admin,
    Scope.db_admin,
})

_ADMIN_SCOPES: FrozenSet[Scope] = frozenset(Scope)

ROLE_SCOPES: dict[Role, FrozenSet[Scope]] = {
    Role.viewer: _VIEWER_SCOPES,
    Role.analyst: _ANALYST_SCOPES,
    Role.developer: _DEVELOPER_SCOPES,
    Role.admin: _ADMIN_SCOPES,
}


def has_scope(role: "str | Role", scope: Scope) -> bool:
    """Return True if role has the given scope. Unknown roles return False."""
    try:
        role_enum = Role(role)
    except ValueError:
        return False
    return scope in ROLE_SCOPES.get(role_enum, frozenset())
