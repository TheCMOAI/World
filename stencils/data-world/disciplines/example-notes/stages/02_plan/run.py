"""
example-notes / 02_plan

Read the state packet from 01_read, decide what to do, produce a typed plan.
No mutations - plan only.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../lib"))

from _shared.db.read import blackboard_read
from _shared.script_base import standard_args, print_json


def run(entity_id: str, workspace_id: str, intent: str = "create_note", content: str = "") -> dict:
    # 1. Read state packet from 01_read
    state_packet = blackboard_read(
        "stage_packets",
        {"workspace_id": workspace_id, "stage": "01_read", "discipline": "example-notes"},
        order_by="created_at DESC",
        limit=1,
    )

    if not state_packet:
        return {"error": "No state packet from 01_read - run 01_read first", "ready_for_execute": False}

    state = state_packet.get("packet", {}).get("state", {}) if isinstance(state_packet.get("packet"), dict) else {}
    existing_notes = state.get("existing_notes", [])

    actions = []

    if intent == "create_note" and content:
        # Validate against conventions (max 500 chars, no compound notes)
        clean_content = content.strip()[:500]
        actions.append({
            "id": "note_001",
            "type": "create_note",
            "description": f"Add note: '{clean_content[:60]}{'...' if len(clean_content) > 60 else ''}'",
            "reversible": True,
            "requires_gate": False,
            "payload": {"content": clean_content, "topic": "general"},
        })

    elif intent == "summarize" and existing_notes:
        # Summarize by grouping (the LLM handles the actual summarization)
        actions.append({
            "id": "summary_001",
            "type": "create_summary",
            "description": f"Summarize {len(existing_notes)} existing notes",
            "reversible": True,
            "requires_gate": False,
            "payload": {"notes": existing_notes},
        })

    plan_packet = {
        "stage": "02_plan",
        "discipline": "example-notes",
        "entity_id": entity_id,
        "workspace_id": workspace_id,
        "plan": {
            "summary": f"{len(actions)} action(s) planned" if actions else "No actions - retrieve only",
            "actions": actions,
        },
        "ready_for_execute": len(actions) > 0,
    }

    return plan_packet


if __name__ == "__main__":
    parser = standard_args("example-notes / 02_plan")
    parser.add_argument("--intent", default="create_note", choices=["create_note", "summarize", "retrieve"])
    parser.add_argument("--content", default="", help="Note content (for create_note intent)")
    args = parser.parse_args()
    result = run(args.entity_id, args.workspace_id, args.intent, args.content)
    print_json(result, args.json_only)
