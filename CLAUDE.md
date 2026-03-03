# Multi-Tool MCP Server

Status: Implemented

## Package Layout

```
multi_tool_mcp/
├── config.py          # Settings dataclass + configure_logging()
├── exceptions.py      # Exception hierarchy
├── models.py          # Pydantic v2 models
├── server.py          # FastMCP entry point
├── security/
│   ├── roles.py       # Role, Scope, ROLE_SCOPES
│   ├── auth.py        # require_scope, JWT helpers
│   └── audit.py       # AuditLogger, @audit_tool
├── middleware/
│   └── rate_limiter.py  # TokenBucketLimiter
├── services/
│   ├── database.py    # DatabaseService (asyncpg)
│   ├── api_proxy.py   # APIProxyService (httpx + SSRF protection)
│   ├── filesystem.py  # FilesystemService (path traversal protection)
│   └── ai.py          # AIService (Groq->Gemini->OpenRouter cascade)
└── tools/
    ├── db_tools.py    # 6 database tools
    ├── api_tools.py   # 3 API proxy tools
    ├── fs_tools.py    # 5 filesystem tools
    └── admin_tools.py # 4 admin tools (whoami, audit, status, summary)
```

## Commands

```bash
# Setup
py -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
py scripts/setup_db.py      # requires docker compose up -d first

# Run server
py -m multi_tool_mcp.server

# Generate token
py scripts/generate_token.py --role admin --user agent-001

# Run demo
py scripts/demo.py

# Tests
py -m pytest tests/ -v
```

## Key Decisions

- FastMCP 3.0 lifespan API (not on_startup/on_shutdown)
- STDIO transport auto-skips JWT auth
- DB connection failure -> graceful None, tools return "Database unavailable"
- Token bucket rate limiter per API domain
- audit_tool decorator fires tasks via asyncio.create_task (fire-and-forget)
- demo_ table prefix to avoid collision with n8n tables
