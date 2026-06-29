"""
Stage 01 — Read

Gather current state from the blackboard for the entity in scope.
Returns a state packet. No mutations.

Usage:
    python run.py --entity-id <id> --workspace-id <id>
"""

import argparse
import json
import sys
import os

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../lib"))

from _shared.db.read import blackboard_read


def run(entity_id: str, workspace_id: str) -> dict:
    # 1. Read entity base state
    entity = blackboard_read("entities", {"id": entity_id})
    if not entity:
        return {"error": f"Entity {entity_id} not found", "ready_for_plan": False}

    # 2. Read prior decisions relevant to this entity
    prior_decisions = blackboard_read(
        "decisions",
        {"entity_id": entity_id},
        limit=10,
        order_by="created_at DESC",
    )

    # 3. Read prior learnings
    learnings = blackboard_read(
        "learnings",
        {"entity_id": entity_id, "status": "active"},
    )

    # 4. Assemble state packet
    packet = {
        "stage": "01_read",
        "entity_id": entity_id,
        "workspace_id": workspace_id,
        "state": {
            "entity": entity,
            "prior_decisions": prior_decisions or [],
            "learnings": learnings or [],
            # Add domain-specific reads here
        },
        "data_gaps": [],
        "ready_for_plan": True,
    }

    # Flag gaps for optional fields — do not block on missing optional data
    if not prior_decisions:
        packet["data_gaps"].append("no_prior_decisions")

    return packet


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--entity-id", required=True)
    parser.add_argument("--workspace-id", required=True)
    args = parser.parse_args()

    result = run(args.entity_id, args.workspace_id)
    print(json.dumps(result, indent=2, default=str))
