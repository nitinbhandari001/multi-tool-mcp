import pytest
import json
from pathlib import Path
from multi_tool_mcp.security.audit import AuditLogger
from multi_tool_mcp.models import AuditEntry
from datetime import datetime, timezone


def make_entry(**kwargs) -> AuditEntry:
    defaults = dict(
        timestamp=datetime.now(timezone.utc).isoformat(),
        user="test-user",
        role="admin",
        tool="test_tool",
        resource="test",
        operation="read",
        duration_ms=12.5,
        success=True,
        detail=None,
    )
    defaults.update(kwargs)
    return AuditEntry(**defaults)


async def test_write_entry_to_file(tmp_path):
    """AuditLogger writes JSONL to date-based file."""
    logger = AuditLogger(str(tmp_path))
    entry = make_entry(user="alice")
    await logger.log(entry)

    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 1
    line = files[0].read_text().strip()
    data = json.loads(line)
    assert data["user"] == "alice"


async def test_query_with_resource_filter(tmp_path):
    """Query filters by resource correctly."""
    logger = AuditLogger(str(tmp_path))
    await logger.log(make_entry(resource="database"))
    await logger.log(make_entry(resource="filesystem"))
    await logger.log(make_entry(resource="database"))

    results = await logger.query(resource="database")
    assert len(results) == 2
    assert all(e.resource == "database" for e in results)


async def test_query_with_status_filter(tmp_path):
    """Query filters by success/failure status."""
    logger = AuditLogger(str(tmp_path))
    await logger.log(make_entry(success=True))
    await logger.log(make_entry(success=False))

    successes = await logger.query(status="success")
    failures = await logger.query(status="failure")
    assert len(successes) == 1
    assert len(failures) == 1


async def test_query_limit(tmp_path):
    """Query respects limit parameter."""
    logger = AuditLogger(str(tmp_path))
    for i in range(10):
        await logger.log(make_entry(tool=f"tool_{i}"))

    results = await logger.query(limit=3)
    assert len(results) == 3
