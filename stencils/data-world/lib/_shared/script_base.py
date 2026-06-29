"""
script_base.py - shared helpers for stage run.py scripts.

Import from this module in any run.py to get consistent CLI argument parsing,
path setup, and output formatting without duplicating boilerplate.

Usage in a stage run.py:
    from _shared.script_base import standard_args, print_json, fail

    def run(entity_id: str, workspace_id: str) -> dict:
        ...

    if __name__ == "__main__":
        args = standard_args().parse_args()
        result = run(args.entity_id, args.workspace_id)
        print_json(result)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def standard_args(description: str = "World stage") -> argparse.ArgumentParser:
    """
    Standard argument parser for a stage run.py.
    Provides --entity-id, --workspace-id, and --json flags.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--entity-id", required=True, help="Entity ID (UUID)")
    parser.add_argument("--workspace-id", required=True, help="Workspace ID (UUID)")
    parser.add_argument("--json", action="store_true", dest="json_only",
                        help="Output raw JSON only (for machine consumption)")
    return parser


def print_json(data: dict, json_only: bool = False) -> None:
    """Print a result dict. Pretty-prints by default; compact with --json."""
    if json_only or os.environ.get("WORLD_JSON_OUTPUT"):
        print(json.dumps(data, default=str))
    else:
        print(json.dumps(data, indent=2, default=str))


def fail(message: str, exit_code: int = 1) -> None:
    """Print an error to stderr and exit."""
    sys.stderr.write(f"ERROR: {message}\n")
    sys.exit(exit_code)


def world_root() -> Path:
    """Return the World root (two levels up from lib/_shared/)."""
    return Path(__file__).resolve().parents[2]


def ensure_db_url() -> str:
    """Return DATABASE_URL or fail with a clear message."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        fail("DATABASE_URL is not set. Run: export DATABASE_URL=postgresql://user:pass@host:5432/db")
    return url
