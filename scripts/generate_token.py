#!/usr/bin/env python3
"""Generate a JWT token for testing."""
import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    parser = argparse.ArgumentParser(description="Generate a JWT token for multi-tool-mcp")
    parser.add_argument("--role", choices=["viewer", "analyst", "developer", "admin"], default="viewer")
    parser.add_argument("--user", default="agent-001")
    parser.add_argument("--hours", type=int, default=24)
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    secret = os.getenv("JWT_SECRET", "")
    if not secret:
        print("Warning: JWT_SECRET not set in .env, using test secret")
        secret = "test-secret-for-development-only-32chars"

    from multi_tool_mcp.security.auth import generate_token, decode_token
    token = generate_token(secret, args.user, args.role, args.hours)
    decoded = decode_token(secret, token)

    print(f"\nToken for {args.user} (role: {args.role}):")
    print(f"\n{token}\n")
    print("Decoded claims:")
    for k, v in decoded.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
