#!/usr/bin/env python3
"""
ringer.py - THE RINGER. The gauntlet every finished change must pass.

Nothing is "done" until the Ringer passes. It runs in order and stops at the
first failed stage:

  1. BACKEND     full test suite, no new red vs baseline   (commit_gate.py)
  2. REVIEW      adversarial self-review of the diff       (review_diff.py)
  3. VERDICT     aggregate - PASS only if every stage passed

Usage:
    python lib/ringer.py --intent "fix: null check on entity lookup"
    python lib/ringer.py --base main         # judge the whole branch vs main
    python lib/ringer.py --backend-only      # quick check: tests only
    python lib/ringer.py --no-review         # skip adversarial review

Exit: 0 if every stage passed, 1 if any stage failed.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LIB = Path(__file__).parent
WORLD_ROOT = LIB.parent
WORKSPACES = WORLD_ROOT / "workspaces" / "ringer"


def run_stage(name: str, cmd: list[str]) -> dict:
    print(f"\n{'=' * 70}\n  RINGER | {name}\n{'=' * 70}", flush=True)
    print("  $ " + " ".join(str(c) for c in cmd), flush=True)
    rc = subprocess.run(cmd, cwd=WORLD_ROOT).returncode
    status = {0: "PASS"}.get(rc, "FAIL")
    print(f"  -> {name}: {status} (exit {rc})", flush=True)
    return {"stage": name, "status": status, "exit": rc}


def main() -> int:
    ap = argparse.ArgumentParser(description="The Ringer - full change gauntlet")
    ap.add_argument("--intent", default="", help="what this change is supposed to do")
    ap.add_argument("--base", default=None, help="compare to this git ref (e.g. main)")
    ap.add_argument("--passes", type=int, default=3, help="adversarial review passes (default: 3)")
    ap.add_argument("--backend-only", action="store_true", help="test gate only (fastest)")
    ap.add_argument("--no-review", action="store_true", help="skip adversarial review")
    args = ap.parse_args()

    results = []

    # Stage 1: test gate
    results.append(run_stage("BACKEND - test gate", [sys.executable, str(LIB / "commit_gate.py")]))
    if results[-1]["status"] != "PASS":
        print("\n  Ringer stopped: test gate failed. Fix new failures before continuing.")
        _write_verdict(results, args)
        return 1

    if args.backend_only:
        return _finish(results, args)

    # Stage 2: adversarial review
    if not args.no_review:
        cmd = [sys.executable, str(LIB / "review_diff.py"), "--passes", str(args.passes)]
        if args.base:
            cmd += ["--base", args.base]
        if args.intent:
            cmd += ["--intent", args.intent]
        results.append(run_stage("REVIEW - adversarial diff", cmd))

    return _finish(results, args)


def _finish(results: list, args) -> int:
    failed = [r for r in results if r["status"] != "PASS"]
    verdict = "PASS" if not failed else "FAIL"

    _write_verdict(results, args, verdict)

    print(f"\n{'#' * 70}\n  RINGER VERDICT: {verdict}\n{'#' * 70}")
    for r in results:
        print(f"  {r['status']:8}  {r['stage']}")

    if verdict == "PASS":
        print("\n  Shippable. Every gauntlet stage passed.")
    else:
        print("\n  NOT shippable. Resolve the failed stage(s) above, then re-run.")

    return 0 if verdict == "PASS" else 1


def _write_verdict(results: list, args, verdict: str = "INCOMPLETE") -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = WORKSPACES / ts
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "verdict": verdict,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "intent": args.intent,
        "base": getattr(args, "base", None),
        "stages": results,
    }
    (out / "verdict.json").write_text(json.dumps(report, indent=2))
    print(f"  Report: {out / 'verdict.json'}")


if __name__ == "__main__":
    raise SystemExit(main())
