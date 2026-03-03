# multi-tool-mcp

Enterprise MCP server built with FastMCP 3.0. Provides AI agents with secure, RBAC-gated access to PostgreSQL, HTTP APIs, and a sandboxed filesystem — with full audit logging.

## Features

- 18 MCP tools across 4 categories (DB, API, filesystem, admin)
- JWT-based auth with 4 roles: viewer, analyst, developer, admin
- 9 scopes: db:read/write/admin, api:read/write, fs:read/write/admin, admin
- Token bucket rate limiter per API domain
- Path traversal protection on all filesystem ops
- SSRF protection via domain allowlist
- SQL injection prevention (parameterized queries + blocked keyword list)
- JSONL audit log with every tool call (user, role, duration, success/failure)
- AI summarization cascade: Groq -> Gemini -> OpenRouter

## Quick Start

```bash
# 1. Start infrastructure
docker compose up -d   # from C:\Users\Nitin\portfolio\

# 2. Setup DB schema
py scripts/setup_db.py

# 3. Generate a token
py scripts/generate_token.py --role admin --user agent-001

# 4. Run server
py -m multi_tool_mcp.server

# 5. Run demo
py scripts/demo.py
```

## Setup

```bash
py -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
cp .env.example .env   # fill in real keys
```

Required env vars (in `.env`):
- `JWT_SECRET` — min 32 chars
- `DATABASE_URL` — postgresql://user:pass@host:port/db
- `GROQ_API_KEY` / `GEMINI_API_KEY` / `OPENROUTER_API_KEY` — at least one for AI tools

## Tools

### Database (6 tools)
| Tool | Scope | Description |
|------|-------|-------------|
| `query_database` | db:read | SELECT query with auto-LIMIT |
| `execute_sql` | db:write | INSERT/UPDATE/DELETE |
| `list_tables` | db:read | List allowed tables |
| `describe_table` | db:read | Column info for a table |
| `insert_demo_data` | db:write | Insert sample rows |
| `database_stats` | db:admin | Row counts for all tables |

### API Proxy (3 tools)
| Tool | Scope | Description |
|------|-------|-------------|
| `api_get` | api:read | GET request to allowed domain |
| `api_request` | api:write | Any HTTP method to allowed domain |
| `list_allowed_apis` | api:read | List allowlisted domains |

### Filesystem (5 tools)
| Tool | Scope | Description |
|------|-------|-------------|
| `read_file` | fs:read | Read workspace file |
| `write_file` | fs:write | Write workspace file |
| `list_directory` | fs:read | List directory entries |
| `file_info` | fs:read | File metadata |
| `delete_file` | fs:admin | Delete workspace file |

### Admin (4 tools)
| Tool | Scope | Description |
|------|-------|-------------|
| `whoami` | (any) | Current user/role/scopes |
| `audit_log` | admin | Query audit log |
| `system_status` | admin | Service health check |
| `summarize_data` | admin | AI summarization of query results |

## Tests

```bash
py -m pytest tests/ -v
# 38 tests, ~5s
```

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
    └── admin_tools.py # 4 admin tools
```

## Docs

- `docs/architecture.md` — system diagram + request flow
- `docs/security-model.md` — RBAC matrix + threat model
