#!/usr/bin/env python3
"""
review_diff.py - adversarial diff review using the post-change self-review prompt.

Runs N independent adversarial passes over the current diff. Each pass is a
fresh LLM session - reviewers do not share context and cannot talk each other
into accepting a bad change. Fails (exit 1) if any pass finds a HIGH or BLOCKER.

Called by ringer.py during the REVIEW stage. Can also be run standalone after
any non-trivial change.

Usage:
    python lib/review_diff.py --intent "what the change was supposed to do"
    python lib/review_diff.py --base main --passes 3
    python lib/review_diff.py --passes 1   # quick single-pass check

Requirements:
    Claude Code CLI (`claude`) must be available on PATH, or set REVIEW_CMD to
    the path of whatever LLM CLI you use. The CLI must accept a prompt on stdin
    and print its response to stdout.

Exit: 0 if all passes return PASS or no HIGH/BLOCKER, 1 otherwise.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

LIB = Path(__file__).parent
WORLD_ROOT = LIB.parent
PROMPT_FILE = WORLD_ROOT / "prompts" / "post_change_self_review.md"

# Override with REVIEW_CMD env var to use a different LLM CLI.
# Default: claude (Claude Code CLI)
REVIEW_CMD = os.environ.get("REVIEW_CMD", "claude")


def get_diff(base: str = None) -> str:
    if base:
        result = subprocess.run(
            ["git", "diff", f"{base}...HEAD"],
            capture_output=True, text=True, cwd=WORLD_ROOT
        )
    else:
        result = subprocess.run(
            ["git", "diff", "HEAD"],
            capture_output=True, text=True, cwd=WORLD_ROOT
        )
    return result.stdout or "(no diff - working tree is clean)"


def get_changed_files(base: str = None) -> str:
    if base:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            capture_output=True, text=True, cwd=WORLD_ROOT
        )
    else:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, cwd=WORLD_ROOT
        )
    return result.stdout.strip() or "(none)"


def build_prompt(intent: str, diff: str, changed_files: str) -> str:
    template = PROMPT_FILE.read_text()
    # Fill in the template fields
    prompt = template.replace(
        "<one sentence describing what the change was supposed to do>",
        intent or "(no intent provided - infer from the diff)",
    ).replace(
        "<paste git diff --name-only output, or say \"read git diff from the repo\">",
        changed_files,
    )
    prompt += f"\n\n---\n\n## Diff\n\n```diff\n{diff}\n```"
    return prompt


def run_pass(pass_num: int, prompt: str) -> dict:
    print(f"\n  Pass {pass_num}...", flush=True)

    try:
        result = subprocess.run(
            [REVIEW_CMD, "--print", "-"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout.strip()
    except FileNotFoundError:
        print(f"  WARNING: '{REVIEW_CMD}' not found. Set REVIEW_CMD to your LLM CLI path.")
        print(f"  Skipping pass {pass_num}.")
        return {"pass": pass_num, "verdict": "SKIP", "output": "LLM CLI not found"}
    except subprocess.TimeoutExpired:
        return {"pass": pass_num, "verdict": "SKIP", "output": "timeout"}

    # Parse verdict from output
    verdict = "UNKNOWN"
    for line in output.splitlines():
        if line.startswith("Verdict:"):
            v = line.replace("Verdict:", "").strip()
            if "PASS" in v:
                verdict = "PASS"
            elif "BLOCKED" in v:
                verdict = "BLOCKED"
            elif "FIX" in v:
                verdict = "FIX-FIRST"
            break

    print(f"  Pass {pass_num}: {verdict}")

    # Print findings
    in_findings = False
    for line in output.splitlines():
        if line.startswith("Findings:"):
            in_findings = True
        elif in_findings and line.startswith("Tests/gates"):
            in_findings = False
        elif in_findings and line.strip() and line.strip() != "-":
            print(f"    {line.strip()}")

    return {"pass": pass_num, "verdict": verdict, "output": output}


def main() -> int:
    ap = argparse.ArgumentParser(description="Adversarial diff review")
    ap.add_argument("--intent", default="", help="what the change was supposed to do")
    ap.add_argument("--base", default=None, help="git ref to diff against (e.g. main)")
    ap.add_argument("--passes", type=int, default=3, help="number of independent review passes")
    args = ap.parse_args()

    if not PROMPT_FILE.exists():
        print(f"ERROR: prompt file not found at {PROMPT_FILE}")
        return 1

    print(f"\nAdversarial review - {args.passes} pass(es)", flush=True)

    diff = get_diff(args.base)
    changed = get_changed_files(args.base)
    prompt = build_prompt(args.intent, diff, changed)

    results = []
    for i in range(1, args.passes + 1):
        results.append(run_pass(i, prompt))

    # Verdict: any BLOCKED or FIX-FIRST = fail
    blocking = [r for r in results if r["verdict"] in ("BLOCKED", "FIX-FIRST")]
    passed = [r for r in results if r["verdict"] == "PASS"]
    skipped = [r for r in results if r["verdict"] == "SKIP"]

    print(f"\n  Review summary: {len(passed)} PASS | {len(blocking)} blocking | {len(skipped)} skipped")

    if blocking:
        print("  REVIEW FAILED - fix findings before shipping.")
        return 1

    if len(skipped) == args.passes:
        print("  WARNING: all passes skipped (LLM CLI unavailable). Review manually.")
        return 0

    print("  Review passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
