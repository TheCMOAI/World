#!/usr/bin/env python3
"""
run_tests.py - catch-net test runner for a Dev World.

Runs the test suite scoped to a safe directory, survives broken collectors,
and excludes slow/integration markers by default. Never run bare pytest from
the repo root - stale or vendored test files can abort collection silently.

Usage:
    python lib/run_tests.py                        # whole safe suite
    python lib/run_tests.py --select tests/foo.py  # one file (path)
    python lib/run_tests.py --select widget         # -k keyword match
    python lib/run_tests.py --all                   # include integration/network
    python lib/run_tests.py --json                  # machine-readable output only
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Root of this Dev World. If you copy lib/ into another repo root, update this.
REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"

# Markers excluded by default (too slow or require real credentials).
# Add your own slow/integration markers here.
EXCLUDED_MARKERS = ["integration", "network", "slow"]


def _out(payload: dict, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload))
    else:
        print(payload.get("error") or json.dumps(payload, indent=2))


def run(select: str = None, include_all: bool = False, json_only: bool = False) -> int:
    if not TESTS_DIR.exists():
        _out({"error": f"tests/ directory not found at {TESTS_DIR}"}, json_only)
        return 1

    cmd = [sys.executable, "-m", "pytest", str(TESTS_DIR), "-v", "--tb=short"]

    if select:
        # Path-like -> pass as positional arg; keyword -> pass as -k
        if "/" in select or select.endswith(".py"):
            cmd = [sys.executable, "-m", "pytest", select, "-v", "--tb=short"]
        else:
            cmd += ["-k", select]

    if not include_all:
        marker_expr = " and ".join(f"not {m}" for m in EXCLUDED_MARKERS)
        cmd += ["-m", marker_expr]

    if json_only:
        cmd += ["--quiet", "--no-header"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    except FileNotFoundError as exc:
        _out({"error": str(exc), "passed": 0, "failed": 0, "errored": 1, "exit": 1}, json_only)
        return 1

    passed = failed = errored = 0
    for line in result.stdout.splitlines():
        if " passed" in line:
            try:
                passed = int(line.strip().split()[0])
            except (ValueError, IndexError):
                pass
        if " failed" in line:
            try:
                failed = int(line.strip().split()[0])
            except (ValueError, IndexError):
                pass
        if " error" in line:
            try:
                errored = int(line.strip().split()[0])
            except (ValueError, IndexError):
                pass

    if result.returncode != 0 and failed == 0 and errored == 0:
        errored = 1

    summary = {
        "passed": passed,
        "failed": failed,
        "errored": errored,
        "exit": result.returncode,
        "cmd": cmd,
    }
    if result.returncode != 0 and not result.stdout.strip():
        summary["stderr"] = result.stderr.strip()[-1000:]

    if json_only:
        print(json.dumps(summary))
    else:
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print(f"\n--- {passed} passed | {failed} failed | {errored} errored ---")

    return result.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dev World catch-net test runner")
    parser.add_argument("--select", help="Path or -k keyword to scope the run")
    parser.add_argument("--all", action="store_true", dest="include_all", help="Include integration/network markers")
    parser.add_argument("--json", action="store_true", dest="json_only", help="Machine-readable output only")
    args = parser.parse_args()

    sys.exit(run(args.select, args.include_all, args.json_only))
