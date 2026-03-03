"""Audit logging for multi-tool-mcp tool invocations."""
import asyncio
import functools
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..models import AuditEntry


class AuditLogger:
    def __init__(self, log_dir: str) -> None:
        self._dir = Path(log_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._entries: list[AuditEntry] = []
        self._lock = asyncio.Lock()

    async def log(self, entry: AuditEntry) -> None:
        async with self._lock:
            self._entries.append(entry)
            log_file = (
                self._dir
                / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
            )
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")

    async def query(
        self,
        limit: int = 50,
        resource: str | None = None,
        status: str | None = None,
    ) -> list[AuditEntry]:
        entries = list(self._entries)
        if resource:
            entries = [e for e in entries if e.resource == resource]
        if status == "success":
            entries = [e for e in entries if e.success]
        elif status == "failure":
            entries = [e for e in entries if not e.success]
        return entries[-limit:]


def audit_tool(resource: str, operation: str) -> Callable:
    """Decorator that logs tool invocations to the audit logger."""
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = "anonymous"
            role = "unknown"
            try:
                from fastmcp.server.dependencies import get_access_token
                token = get_access_token()
                if token is not None:
                    user = token.client_id or "anonymous"
                    role = token.claims.get("role", "unknown")
            except Exception:
                pass

            from multi_tool_mcp.tools import get_container
            container = get_container()

            start = time.monotonic()
            success = True
            detail = None
            try:
                result = await fn(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                detail = str(e)
                raise
            finally:
                duration_ms = (time.monotonic() - start) * 1000
                if container is not None:
                    entry = AuditEntry(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        user=user,
                        role=role,
                        tool=fn.__name__,
                        resource=resource,
                        operation=operation,
                        duration_ms=round(duration_ms, 2),
                        success=success,
                        detail=detail,
                    )
                    try:
                        asyncio.create_task(container.audit.log(entry))
                    except RuntimeError:
                        pass  # No event loop — skip audit in test context
        return wrapper
    return decorator
