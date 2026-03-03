# Security Model

## RBAC Matrix

| Scope      | viewer | analyst | developer | admin |
|------------|--------|---------|-----------|-------|
| db:read    | yes    | yes     | yes       | yes   |
| db:write   |        | yes     | yes       | yes   |
| db:admin   |        |         | yes       | yes   |
| api:read   | yes    | yes     | yes       | yes   |
| api:write  |        | yes     | yes       | yes   |
| fs:read    | yes    | yes     | yes       | yes   |
| fs:write   |        |         | yes       | yes   |
| fs:admin   |        |         | yes       | yes   |
| admin      |        |         |           | yes   |

## Threat Model

### SQL Injection
- **Risk**: Malicious SQL in query parameters
- **Mitigation**: Parameterized queries ($1, $2 placeholders), blocked keyword list for DDL operations, SELECT-only restriction on `query()` endpoint

### Path Traversal
- **Risk**: `../../etc/passwd` style attacks
- **Mitigation**: `Path.resolve()` + `is_relative_to(workspace_root)` check on every path operation

### SSRF (Server-Side Request Forgery)
- **Risk**: Requests to internal services (metadata APIs, internal networks)
- **Mitigation**: Domain allowlist, scheme validation (http/https only)

### Rate Abuse
- **Risk**: AI agent floods external APIs or database
- **Mitigation**: Token bucket rate limiter per domain, configurable via env vars

### Privilege Escalation
- **Risk**: Low-privilege token accessing admin tools
- **Mitigation**: JWT role claim validated against ROLE_SCOPES on every request, auth skip only for STDIO transport
