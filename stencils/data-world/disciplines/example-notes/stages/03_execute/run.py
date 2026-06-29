"""
example-notes / 03_execute

Act on the plan. Write the note. Log the activity. Verify the write.
"""

import json
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../lib"))

from _shared.db.read import blackboard_read
from _shared.db.write import blackboard_write
from _shared.logging import log_activity, log_decision
from _shared.gates.gate import check_gate_resolved
from _shared.script_base import standard_args, print_json


def handle_create_note(action: dict, entity_id: str, workspace_id: str) -> dict:
    payload = action.get("payload", {})
    content = payload.get("content", "").strip()
    topic = payload.get("topic", "general")

    if not content:
        return {"status": "failed", "outcome": {}, "error": "Empty content"}

    note_id = str(uuid.uuid4())
    blackboard_write("entity_notes", {
        "id": note_id,
        "entity_id": entity_id,
        "workspace_id": workspace_id,
        "content": content,
        "topic": topic,
    })

    # Verify the write landed
    written = blackboard_read("entity_notes", {"id": note_id})
    if not written:
        return {"status": "failed", "outcome": {}, "error": "Write did not land - verify DB connection"}

    log_activity(
        entity_id=entity_id,
        workspace_id=workspace_id,
        action_type="note_created",
        description=f"Note added: '{content[:60]}'",
        performed_by="example-notes/03_execute",
    )

    return {"status": "done", "outcome": {"note_id": note_id, "content": content}, "error": None}


def handle_create_summary(action: dict, entity_id: str, workspace_id: str) -> dict:
    payload = action.get("payload", {})
    notes = payload.get("notes", [])

    # In a real discipline, this would call an LLM or use a summary algorithm.
    # Here we produce a simple count summary as a placeholder.
    summary_content = f"Summary of {len(notes)} notes (replace with real summarization logic)"

    note_id = str(uuid.uuid4())
    blackboard_write("entity_notes", {
        "id": note_id,
        "entity_id": entity_id,
        "workspace_id": workspace_id,
        "content": summary_content,
        "topic": "summary",
    })

    return {"status": "done", "outcome": {"note_id": note_id, "summary": summary_content}, "error": None}


ACTION_HANDLERS = {
    "create_note": handle_create_note,
    "create_summary": handle_create_summary,
}


def run(entity_id: str, workspace_id: str) -> dict:
    # 1. Read plan packet
    plan_packet = blackboard_read(
        "stage_packets",
        {"workspace_id": workspace_id, "stage": "02_plan", "discipline": "example-notes"},
        order_by="created_at DESC",
        limit=1,
    )

    if not plan_packet:
        return {"error": "No plan packet - run 02_plan first"}

    packet_data = plan_packet.get("packet", {})
    if isinstance(packet_data, str):
        packet_data = json.loads(packet_data)

    actions = packet_data.get("plan", {}).get("actions", [])
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
                    "error": "Gate not resolved",
                })
                continue

        # 3. Execute
        handler = ACTION_HANDLERS.get(action["type"])
        if not handler:
            results.append({
                "action_id": action["id"],
                "status": "skipped",
                "outcome": {},
                "error": f"No handler for action type: {action['type']}",
            })
            continue

        result = handler(action, entity_id, workspace_id)
        result["action_id"] = action["id"]
        results.append(result)

    all_passed = all(r["status"] == "done" for r in results)
    done_count = sum(1 for r in results if r["status"] == "done")

    # 4. Log decision
    if all_passed and results:
        log_decision(
            entity_id=entity_id,
            workspace_id=workspace_id,
            discipline="example-notes",
            summary=f"Completed {done_count} note action(s)",
            rationale="Operator requested note operation",
            status="done",
        )

    return {
        "stage": "03_execute",
        "discipline": "example-notes",
        "entity_id": entity_id,
        "workspace_id": workspace_id,
        "results": results,
        "summary": f"{done_count} of {len(results)} action(s) completed",
        "all_passed": all_passed,
    }


if __name__ == "__main__":
    args = standard_args("example-notes / 03_execute").parse_args()
    result = run(args.entity_id, args.workspace_id)
    print_json(result, args.json_only)
