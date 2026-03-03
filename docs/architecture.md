# Multi-Tool MCP Server — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                   MCP Clients (AI Agents)                │
└──────────────────────┬──────────────────────────────────┘
                       │ MCP Protocol (STDIO/HTTP+SSE)
┌──────────────────────▼──────────────────────────────────┐
│                  FastMCP 3.0 Server                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  JWT Auth   │  │  18 Tools    │  │ Audit Logging  │  │
│  │  RBAC       │  │  (RBAC-gated)│  │ (JSONL)        │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└──────────────┬──────────────┬────────────────┬──────────┘
               │              │                │
    ┌──────────▼──┐  ┌────────▼──────┐  ┌─────▼────────┐
    │ PostgreSQL   │  │  HTTP APIs    │  │  Filesystem  │
    │ (asyncpg)   │  │  (httpx)      │  │  (workspace) │
    └─────────────┘  └───────────────┘  └──────────────┘
```

## Request Flow

```
Client Request
    │
    ▼
FastMCP Router
    │
    ▼
JWT Verification (HTTP mode only; STDIO skips)
    │
    ▼
RBAC Auth Check (require_scope callable)
    │
    ▼
@audit_tool decorator starts timer
    │
    ▼
Tool Function Executes
    │
    ▼
@audit_tool logs result (success/failure, duration_ms)
    │
    ▼
Response returned to client
```

## RBAC Hierarchy

```
admin       ←── all 9 scopes
  ↑
developer   ←── + db:admin, fs:write, fs:admin
  ↑
analyst     ←── + db:write, api:write
  ↑
viewer      ←── db:read, api:read, fs:read
```

## Security Layers

```
Layer 1: Transport (JWT validation at HTTP level)
Layer 2: RBAC (scope check per tool)
Layer 3: Input validation (SQL keywords, path traversal, SSRF)
Layer 4: Rate limiting (token bucket per domain)
Layer 5: Audit logging (every tool call, success and failure)
```
