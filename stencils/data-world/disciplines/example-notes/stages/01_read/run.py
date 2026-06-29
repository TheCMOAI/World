"""
example-notes / 01_read

A fully worked stage example. Read this to understand the pattern.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../lib"))

from _shared.db.read import blackboard_read
from _shared.script_base import standard_args, print_json


def run(entity_id: str, workspace_id: str) -> dict:
    # 1. Read entity
    entity = blackboard_read("entities", {"id": entity_id})
    if not entity:
        return {
            "stage": "01_read",
            "discipline": "example-notes",
            "entity_id": entity_id,
            "workspace_id": workspace_id,
            "error": f"Entity {entity_id} not found",
            "ready_for_plan": False,
        }

    # 2. Read existing notes (newest first, limit 10)
    existing_notes = blackboard_read(
        "entity_notes",
        {"entity_id": entity_id},
        limit=10,
        order_by="created_at DESC",
    ) or []

    # Normalize: blackboard_read returns a single dict when filter yields 1 row
    if isinstance(existing_notes, dict):
        existing_notes = [existing_notes]

    # 3. Read learnings
    learnings = blackboard_read(
        "learnings",
        {"entity_id": entity_id, "status": "active"},
    ) or []
    if isinstance(learnings, dict):
        learnings = [learnings]

    # 4. Assemble state packet
    data_gaps = []
    if not existing_notes:
        data_gaps.append("no_existing_notes")

    return {
        "stage": "01_read",
        "discipline": "example-notes",
        "entity_id": entity_id,
        "workspace_id": workspace_id,
        "state": {
            "entity": entity,
            "existing_notes": existing_notes,
            "learnings": learnings,
        },
        "data_gaps": data_gaps,
        "ready_for_plan": True,
    }


if __name__ == "__main__":
    args = standard_args("example-notes / 01_read").parse_args()
    result = run(args.entity_id, args.workspace_id)
    print_json(result, args.json_only)
