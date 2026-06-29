#!/usr/bin/env python3
"""
commit_gate.py - blocks changes that newly break tests.

Compares the current test run against a saved baseline of known-failing tests.
If a test that was previously passing is now failing, the gate returns exit 1.
Pre-existing failures are tolerated - new failures are not.

This is the one rule that stops bug-printing. Run it before every commit.

Usage:
    python lib/commit_gate.py                    # 0 = no new red, 1 = you broke something
    python lib/commit_gate.py --update-baseline  # accept current failures as the new baseline
    python lib/commit_gate.py --json             # machine-readable verdict

Baseline file: lib/.test_baseline.json
Commit this file to git so the team shares the same known-red set.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

BASELINE_FILE = Path(__file__).parent / ".test_baseline.json"
REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"


def get_failures() -> tuple[set[str], str | None]:
    """Run the full suite and return the set of failing test IDs."""
    cmd = [
        sys.executable, "-m", "pytest", str(TESTS_DIR),
        "--tb=no", "-q", "--no-header",
        "-m", "not integration and not network and not slow",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)

    failures = set()
    for line in result.stdout.splitlines():
        # pytest outputs "FAILED tests/foo.py::test_bar" lines
        if line.startswith("FAILED "):
            test_id = line.replace("FAILED ", "").strip().split(" ")[0]
            failures.add(test_id)

    command_error = None
    if result.returncode != 0 and not failures:
        tail = (result.stderr or result.stdout or "pytest failed without reporting a test id").strip()
        command_error = tail[-1000:]
        failures.add("__pytest_command_error__")

    return failures, command_error


def load_baseline() -> set[str]:
    if not BASELINE_FILE.exists():
        return set()
    with open(BASELINE_FILE) as f:
        data = json.load(f)
    return set(data.get("known_failures", []))


def save_baseline(failures: set[str]) -> None:
    with open(BASELINE_FILE, "w") as f:
        json.dump({"known_failures": sorted(failures)}, f, indent=2)
    print(f"Baseline updated: {len(failures)} known failure(s) recorded.")


def run(update_baseline: bool = False, json_only: bool = False) -> int:
    if not TESTS_DIR.exists():
        msg = {"error": f"tests/ not found at {TESTS_DIR}"}
        print(json.dumps(msg) if json_only else msg["error"])
        return 1

    if update_baseline:
        current, _ = get_failures()
        save_baseline(current)
        return 0

    baseline = load_baseline()
    current, command_error = get_failures()

    new_failures = current - baseline
    fixed = baseline - current

    verdict = {
        "new_failures": sorted(new_failures),
        "fixed": sorted(fixed),
        "known_failures": sorted(baseline & current),
        "gate": "pass" if not new_failures else "block",
    }
    if command_error:
        verdict["command_error"] = command_error

    if json_only:
        print(json.dumps(verdict))
    else:
        if new_failures:
            print(f"\nGATE BLOCKED - {len(new_failures)} newly broken test(s):\n")
            for t in sorted(new_failures):
                print(f"  FAIL  {t}")
            if command_error:
                print(f"\nPytest command error:\n{command_error}")
            print(f"\nFix these before committing. Known pre-existing failures: {len(baseline & current)}")
        else:
            print("Gate passed - no new failures.")
            if fixed:
                print(f"  Also fixed {len(fixed)} previously known failure(s): {', '.join(sorted(fixed))}")
            if baseline & current:
                print(f"  Pre-existing known failures (tolerated): {len(baseline & current)}")

    return 0 if not new_failures else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dev World commit gate")
    parser.add_argument("--update-baseline", action="store_true", help="Accept current failures as the new baseline")
    parser.add_argument("--json", action="store_true", dest="json_only", help="Machine-readable verdict")
    args = parser.parse_args()

    sys.exit(run(args.update_baseline, args.json_only))
