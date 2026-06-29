"""
Stage 03 — Execute

Act on the approved plan. Write outcomes back to the blackboard.

Usage:
    python run.py --entity-id <id> --workspace-id <id>
"""

import argparse
import json
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../lib"))

from _shared.db.read import blackboard_read
from _shared.db.write import blackboard_write
from _shared.gates.gate import check_gate_resolved


def execute_action(action: dict, entity_id: str) -> dict:
    """
    Execute a single action from the plan.
    Replace this with your domain-specific execution logic.
    """
    action_type = action["type"]

    # Route to action handlers
    # if action_type == "your_action_type":
    #     result = your_handler(action["payload"], entity_id)
    #     return {"status": "done", "outcome": result, "error": None}

    return {"status": "skipped", "outcome": {}, "error": f"No handler for action type: {action_type}"}


def run(entity_id: str, workspace_id: str) -> dict:
    # 1. Read plan packet
    plan_packet = blackboard_read(
        "stage_packets",
        {"workspace_id": workspace_id, "stage": "02_plan"},
        order_by="created_at DESC",
        limit=1,
    )

    if not plan_packet:
        return {"error": "No plan packet found — run 02_plan first"}

    packet = plan_packet.get("packet") or {}
    entity_id = str(plan_packet.get("entity_id") or entity_id)
    actions = packet.get("plan", {}).get("actions", [])

    results = []
    for action in actions:
        # 2. Check gate if required
        if action.get("requires_gate"):
            resolved = check_gate_resolved(workspace_id, action["id"])
            if not resolved:
                results.append({
                    "action_id": action["id"],
                    "status": "skipped",
                    "outcome": {},
                    "error": "Gate not resolved — operator approval required",
                })
                continue

        # 3. Execute
        result = execute_action(action, entity_id)
        result["action_id"] = action["id"]
        results.append(result)

        # 4. Log to activity log
        blackboard_write("entity_activity_log", {
            "entity_id": entity_id,
            "workspace_id": workspace_id,
            "action_type": action["type"],
            "action_id": action["id"],
            "status": result["status"],
            "outcome": result["outcome"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    all_passed = all(r["status"] == "done" for r in results)

    result_packet = {
        "stage": "03_execute",
        "entity_id": entity_id,
        "workspace_id": workspace_id,
        "results": results,
        "summary": f"{sum(1 for r in results if r['status'] == 'done')} of {len(results)} actions completed",
        "all_passed": all_passed,
    }

    return result_packet


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--entity-id", required=True)
    parser.add_argument("--workspace-id", required=True)
    args = parser.parse_args()

    result = run(args.entity_id, args.workspace_id)
    print(json.dumps(result, indent=2, default=str))
