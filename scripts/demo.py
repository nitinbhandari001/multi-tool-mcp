#!/usr/bin/env python3
"""Demonstrates all 18 tools with different roles. Shows auth denials."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    from dotenv import load_dotenv
    load_dotenv()

    from multi_tool_mcp.config import get_settings, configure_logging
    from multi_tool_mcp.services import create_services
    from multi_tool_mcp.tools import set_container, get_container
    from multi_tool_mcp.security import require_scope, Scope

    settings = get_settings()
    configure_logging("WARNING")

    print("=== Multi-Tool MCP Server Demo ===\n")
    print("Setting up services...")
    container = await create_services(settings)
    set_container(container)

    # 1. Filesystem demo
    print("\n--- Filesystem Tools ---")
    entries = await container.fs.list_directory(".")
    print(f"Workspace contents ({len(entries)} items):")
    for e in entries[:5]:
        prefix = "[DIR]" if e.is_dir else "[FILE]"
        print(f"  {prefix} {e.name}")

    content = await container.fs.read_file("reports/monthly-summary-jan.md")
    print(f"\nRead file (first 100 chars): {content[:100]}...")

    # 2. Database demo
    print("\n--- Database Tools ---")
    if container.db:
        tables = await container.db.list_tables()
        print(f"Tables: {tables[:5]}")

        result = await container.db.query("SELECT name, email, role FROM demo_users", limit=3)
        print(f"Users ({result.row_count} rows):")
        for row in result.rows:
            print(f"  {row}")
    else:
        print("Database unavailable (start docker: docker compose up -d)")

    # 3. API proxy demo
    print("\n--- API Proxy Tools ---")
    allowed = container.api.list_allowed()
    print(f"Allowed domains: {allowed}")
    try:
        resp = await container.api.get("https://jsonplaceholder.typicode.com/todos/1")
        print(f"API response (HTTP {resp.status_code}): {resp.body[:100]}...")
    except Exception as e:
        print(f"API call failed: {e}")

    # 4. Auth demo
    print("\n--- RBAC Demo ---")
    from multi_tool_mcp.security import has_scope, Role
    for role in ["viewer", "analyst", "developer", "admin"]:
        can_write_db = has_scope(role, Scope.db_write)
        can_fs_admin = has_scope(role, Scope.fs_admin)
        can_admin = has_scope(role, Scope.admin)
        print(f"  {role:12} db:write={can_write_db} fs:admin={can_fs_admin} admin={can_admin}")

    # 5. Audit demo
    print("\n--- Audit Log ---")
    entries_audit = await container.audit.query(limit=5)
    print(f"Audit entries: {len(entries_audit)}")

    await container.close()
    print("\n✓ Demo complete!")

if __name__ == "__main__":
    asyncio.run(main())
