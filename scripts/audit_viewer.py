#!/usr/bin/env python3
"""Read and display audit log JSONL files."""
import json
import sys
import os
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="View audit logs")
    parser.add_argument("--log-dir", default="./data/audit_logs", help="Audit log directory")
    parser.add_argument("--resource", help="Filter by resource")
    parser.add_argument("--user", help="Filter by user")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"Log directory not found: {log_dir}")
        sys.exit(1)

    entries = []
    for f in sorted(log_dir.glob("*.jsonl")):
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))

    if args.resource:
        entries = [e for e in entries if e.get("resource") == args.resource]
    if args.user:
        entries = [e for e in entries if e.get("user") == args.user]

    entries = entries[-args.limit:]

    if not entries:
        print("No audit entries found")
        return

    print(f"{'Timestamp':<28} {'User':<15} {'Role':<12} {'Tool':<25} {'Resource':<15} {'Success'}")
    print("-" * 110)
    for e in entries:
        success = "✓" if e.get("success") else "✗"
        print(f"{e.get('timestamp',''):<28} {e.get('user',''):<15} {e.get('role',''):<12} {e.get('tool',''):<25} {e.get('resource',''):<15} {success}")

if __name__ == "__main__":
    main()
