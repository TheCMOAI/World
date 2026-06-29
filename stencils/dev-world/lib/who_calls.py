#!/usr/bin/env python3
"""
who_calls.py - live blast-radius checker.

Greps the codebase for every reference to a symbol: function name, class name,
table name, route path, config key. Returns the files and line numbers that
reference it. Run this before touching any load-bearing code.

No symbol graph. No stale index. Live grep, always fresh.

Usage:
    python lib/who_calls.py <symbol>
    python lib/who_calls.py connect_db
    python lib/who_calls.py "tenant_id"         # quoted if it contains special chars
    python lib/who_calls.py run_stage --ext py  # search only .py files
    python lib/who_calls.py run_stage --json    # machine-readable
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Directories to skip - build artifacts, vendored code, generated files.
# Extend this list for your repo's junk directories.
SKIP_DIRS = [
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", "*.egg-info", ".vendor",
]


def search(symbol: str, extensions: list[str] = None, json_only: bool = False) -> int:
    cmd = ["grep", "-rn", "--include=*.py", symbol, str(REPO_ROOT)]

    if extensions:
        cmd = ["grep", "-rn"]
        for ext in extensions:
            cmd += ["--include", f"*.{ext.lstrip('.')}"]
        cmd += [symbol, str(REPO_ROOT)]
    else:
        # Default: search common source file types
        cmd = ["grep", "-rn",
               "--include=*.py", "--include=*.ts", "--include=*.tsx",
               "--include=*.js", "--include=*.yaml", "--include=*.sql",
               symbol, str(REPO_ROOT)]

    # Exclude junk directories
    for skip in SKIP_DIRS:
        cmd += ["--exclude-dir", skip]

    result = subprocess.run(cmd, capture_output=True, text=True)

    hits = []
    for line in result.stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) >= 3:
            filepath, lineno, content = parts[0], parts[1], parts[2].strip()
            # Make path relative to repo root for readability
            try:
                rel = str(Path(filepath).relative_to(REPO_ROOT))
            except ValueError:
                rel = filepath
            hits.append({"file": rel, "line": int(lineno), "content": content})

    if json_only:
        print(json.dumps({"symbol": symbol, "hits": hits, "count": len(hits)}))
    else:
        if not hits:
            print(f"No references to '{symbol}' found.")
        else:
            print(f"'{symbol}' referenced in {len(hits)} location(s):\n")
            for h in hits:
                print(f"  {h['file']}:{h['line']}")
                print(f"    {h['content']}")
            print(f"\nTotal: {len(hits)}")

    return 0 if hits else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dev World blast-radius checker")
    parser.add_argument("symbol", help="Symbol to search for (function, class, table, key...)")
    parser.add_argument("--ext", nargs="+", help="File extensions to search (default: py ts tsx js yaml sql)")
    parser.add_argument("--json", action="store_true", dest="json_only", help="Machine-readable output")
    args = parser.parse_args()

    sys.exit(search(args.symbol, args.ext, args.json_only))
