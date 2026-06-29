#!/usr/bin/env python3
"""
dispatch.py - turn activation proposals into opened work.

watch.py proposes activations (status=proposed). This picks them up and opens
the discipline's entry stage for each candidate entity.

It deliberately runs ONLY the entry (read) stage. It never plans and never
executes on its own. The scheduler decides WHAT deserves attention; it does not
decide to mutate. Planning and execution stay with the operating LLM and its
gates - that is the safety boundary that makes autonomy acceptable.

For high-risk activations it opens a gate instead of dispatching, so a human
sees it before any work begins.

Usage:
    python lib/dispatch.py --once            # dispatch all proposed activations
    python lib/dispatch.py --once --limit 5  # cap how many per pass
    python lib/dispatch.py --once --dry-run  # show what would dispatch
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

WORLD_ROOT = Path(__file__).resolve().parent.parent
DISCIPLINES_ROOT = WORLD_ROOT / "disciplines"

sys.path.insert(0, str(WORLD_ROOT / "lib"))
from _shared.db.read import blackboard_read
from _shared.db.write import blackboard_write
import stage_runtime

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def _entry_stage(discipline: str) -> str:
    binding = DISCIPLINES_ROOT / discipline / "binding.yaml"
    if binding.exists():
        data = yaml.safe_load(binding.read_text()) or {}
        return (data.get("activation") or {}).get("entry_stage", "01_read")
    return "01_read"


def _proposed(limit: int) -> list:
    rows = blackboard_read(
        "activations",
        filter={"status": "proposed"},
        order_by="created_at ASC",
        limit=limit,
    )
    if not rows:
        return []
    return [rows] if isinstance(rows, dict) else rows


def dispatch_one(act: dict) -> dict:
    discipline = act["discipline"]
    entity_id = str(act["entity_id"])
    entry = _entry_stage(discipline)

    # High-risk activations never auto-open. Surface a gate first.
    if act.get("risk") == "high":
        gate = blackboard_write("gates", {
            "question": (
                f"Autonomous activation: run '{discipline}' for entity {entity_id}? "
                f"({act.get('reason', '')})"
            ),
            "risk_level": "high",
            "status": "open",
            "resume_action_json": {
                "discipline": discipline,
                "entity_id": entity_id,
                "entry_stage": entry,
                "activation_id": str(act["id"]),
            },
        }, returning="*")
        blackboard_write("activations", {"status": "gated"}, where={"id": act["id"]})
        return {"trigger_key": act["trigger_key"], "result": "gated", "gate_id": str(gate["id"])}

    # Open a workspace for this activation, then run the entry (read) stage only.
    ws = blackboard_write("workspaces", {
        "entity_id": entity_id,
        "name": f"{discipline} (auto)",
        "status": "open",
    }, returning="*")
    workspace_id = str(ws["id"])

    packet = stage_runtime.dispatch(discipline, entry, {
        "entity_id": entity_id,
        "workspace_id": workspace_id,
    })

    blackboard_write("activations", {
        "status": "dispatched",
        "workspace_id": workspace_id,
        "dispatched_at": datetime.now(timezone.utc).isoformat(),
    }, where={"id": act["id"]})

    return {
        "trigger_key": act["trigger_key"],
        "result": "dispatched",
        "workspace_id": workspace_id,
        "entry_stage": entry,
        "stage_error": packet.get("error"),
    }


def main():
    ap = argparse.ArgumentParser(description="World dispatcher - open proposed activations")
    ap.add_argument("--once", action="store_true", help="run a single pass (default)")
    ap.add_argument("--limit", type=int, default=20, help="max activations to dispatch this pass")
    ap.add_argument("--dry-run", action="store_true", help="show what would dispatch, write nothing")
    args = ap.parse_args()

    if not os.environ.get("DATABASE_URL"):
        print("Error: DATABASE_URL not set.")
        sys.exit(1)

    proposed = _proposed(args.limit)
    if not proposed:
        print("No proposed activations.")
        return

    print(f"{len(proposed)} proposed activation(s):")
    for act in proposed:
        if args.dry_run:
            print(f"  .  would dispatch {act['trigger_key']} (risk={act.get('risk')})")
            continue
        res = dispatch_one(act)
        tail = res.get("workspace_id") or res.get("gate_id") or ""
        note = f"  ! stage error: {res['stage_error']}" if res.get("stage_error") else ""
        print(f"  ->  {res['result']}: {act['trigger_key']}  {tail}{note}")


if __name__ == "__main__":
    main()
