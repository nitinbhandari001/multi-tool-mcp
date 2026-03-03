"""Exception hierarchy for multi-tool-mcp."""


class MCPSecurityError(Exception):
    """Base exception for all MCP security-related errors."""


class AuthorizationError(MCPSecurityError):
    """Raised when a user lacks the required scope/role for an operation."""


class RateLimitExceeded(MCPSecurityError):
    """Raised when a user exceeds the allowed request rate."""


class PathTraversalError(MCPSecurityError):
    """Raised when a file path attempts to escape the workspace root."""


class SSRFError(MCPSecurityError):
    """Raised when an API request targets a disallowed or internal domain."""


class SQLValidationError(MCPSecurityError):
    """Raised when SQL contains blocked keywords or invalid structure."""


class DatabaseError(MCPSecurityError):
    """Raised on database connection or query execution failures."""


class AIServiceError(MCPSecurityError):
    """Raised on failures communicating with AI provider APIs."""
