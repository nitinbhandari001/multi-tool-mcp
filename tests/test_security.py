import pytest
from multi_tool_mcp.security.roles import Role, Scope, ROLE_SCOPES, has_scope
from multi_tool_mcp.security.auth import generate_token, decode_token


def test_viewer_scopes():
    """Viewer has db:read, api:read, fs:read only."""
    assert has_scope("viewer", Scope.db_read)
    assert has_scope("viewer", Scope.api_read)
    assert has_scope("viewer", Scope.fs_read)
    assert not has_scope("viewer", Scope.db_write)
    assert not has_scope("viewer", Scope.admin)


def test_admin_has_all_scopes():
    """Admin has all 9 scopes."""
    for scope in Scope:
        assert has_scope("admin", scope), f"Admin missing scope: {scope}"


def test_viewer_cannot_write():
    """Viewer cannot perform write operations."""
    assert not has_scope("viewer", Scope.db_write)
    assert not has_scope("viewer", Scope.fs_write)
    assert not has_scope("viewer", Scope.api_write)


def test_jwt_round_trip(jwt_secret):
    """Generate and decode JWT preserves all claims."""
    token = generate_token(jwt_secret, "test-user", "analyst")
    decoded = decode_token(jwt_secret, token)
    assert decoded["sub"] == "test-user"
    assert decoded["role"] == "analyst"
    assert "scopes" in decoded
    assert "exp" in decoded


def test_invalid_jwt_raises(jwt_secret):
    """Invalid JWT raises an exception."""
    import jwt
    with pytest.raises(Exception):
        decode_token(jwt_secret, "invalid.token.here")


def test_unknown_role_has_no_scope():
    """Unknown role returns False for all scopes."""
    assert not has_scope("superuser", Scope.admin)
    assert not has_scope("", Scope.db_read)
    assert not has_scope("nonexistent", Scope.fs_read)
