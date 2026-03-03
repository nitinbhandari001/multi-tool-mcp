"""Settings and logging configuration for multi-tool-mcp."""

from __future__ import annotations

import dataclasses
import logging
from dataclasses import dataclass
from functools import lru_cache

import structlog


@dataclass(frozen=True)
class Settings:
    database_url: str = "postgresql://dev:devpassword@localhost:5432/portfolio"
    db_pool_min: int = 2
    db_pool_max: int = 10
    db_query_timeout: int = 30
    allowed_tables: str = "users,orders,products,logs,analytics"
    blocked_sql_keywords: str = "DROP,TRUNCATE,ALTER,GRANT,REVOKE"
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    groq_api_key: str = ""
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    allowed_api_domains: str = "api.github.com,jsonplaceholder.typicode.com,httpbin.org"
    api_rate_limit: int = 30
    api_timeout: int = 30
    workspace_root: str = "./data/workspace"
    max_file_size: int = 10485760
    allowed_extensions: str = ".md,.txt,.csv,.json,.yaml,.yml,.html,.xml"
    audit_log_dir: str = "./data/audit_logs"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment / .env file."""
        from dotenv import load_dotenv
        import os

        load_dotenv()

        fields = {f.name: f.default for f in dataclasses.fields(cls)}
        overrides = {
            "database_url": os.getenv("DATABASE_URL"),
            "db_pool_min": int(os.getenv("DB_POOL_MIN", "")) if os.getenv("DB_POOL_MIN") else None,
            "db_pool_max": int(os.getenv("DB_POOL_MAX", "")) if os.getenv("DB_POOL_MAX") else None,
            "db_query_timeout": int(os.getenv("DB_QUERY_TIMEOUT", "")) if os.getenv("DB_QUERY_TIMEOUT") else None,
            "allowed_tables": os.getenv("ALLOWED_TABLES"),
            "blocked_sql_keywords": os.getenv("BLOCKED_SQL_KEYWORDS"),
            "jwt_secret": os.getenv("JWT_SECRET"),
            "jwt_algorithm": os.getenv("JWT_ALGORITHM"),
            "groq_api_key": os.getenv("GROQ_API_KEY"),
            "gemini_api_key": os.getenv("GEMINI_API_KEY"),
            "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
            "allowed_api_domains": os.getenv("ALLOWED_API_DOMAINS"),
            "api_rate_limit": int(os.getenv("API_RATE_LIMIT", "")) if os.getenv("API_RATE_LIMIT") else None,
            "api_timeout": int(os.getenv("API_TIMEOUT", "")) if os.getenv("API_TIMEOUT") else None,
            "workspace_root": os.getenv("WORKSPACE_ROOT"),
            "max_file_size": int(os.getenv("MAX_FILE_SIZE", "")) if os.getenv("MAX_FILE_SIZE") else None,
            "allowed_extensions": os.getenv("ALLOWED_EXTENSIONS"),
            "audit_log_dir": os.getenv("AUDIT_LOG_DIR"),
            "log_level": os.getenv("LOG_LEVEL"),
        }
        kwargs = {k: v for k, v in overrides.items() if v is not None}
        return cls(**{**fields, **kwargs})


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings instance loaded from environment."""
    return Settings.from_env()


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog for the application."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.INFO))
