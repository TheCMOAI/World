"""
Stage 02 — Plan

Read the state packet and produce a typed plan. No domain mutations.

Usage:
    python run.py --entity-id <id> --workspace-id <id> [--constraints <json>]
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../lib"))

from _shared.db.read import blackboard_read


def run(entity_id: str, workspace_id: str, constraints: dict = None) -> dict:
    # 1. Read the state packet written by 01_read
    state_packet = blackboard_read(
        "stage_packets",
        {"workspace_id": workspace_id, "stage": "01_read"},
        order_by="created_at DESC",
        limit=1,
    )

    if not state_packet:
        return {"error": "No state packet found — run 01_read first", "ready_for_execute": False}

    packet = state_packet.get("packet") or {}
    entity_id = str(state_packet.get("entity_id") or entity_id)
    state = packet.get("state", {})

    # 2. Apply domain logic — replace this with your discipline's planning logic
    actions = []

    # Example: propose an action based on state
    # if state.get("some_condition"):
    #     actions.append({
    #         "id": "action_001",
    #         "type": "your_action_type",
    #         "description": "What this action does",
    #         "reversible": True,
    #         "requires_gate": False,
    #         "payload": {"key": "value"},
    #     })

    plan_packet = {
        "stage": "02_plan",
        "entity_id": entity_id,
        "workspace_id": workspace_id,
        "plan": {
            "summary": "Replace with a one-sentence summary of the plan",
            "actions": actions,
        },
        "ready_for_execute": len(actions) > 0,
    }

    return plan_packet


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--entity-id", required=True)
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--constraints", default="{}")
    args = parser.parse_args()

    result = run(args.entity_id, args.workspace_id, json.loads(args.constraints))
    print(json.dumps(result, indent=2, default=str))
