"""
Gate pattern - human approval before irreversible or high-risk actions.

A gate is written to the `gates` table with status "open".
Execution stops. The operator resolves the gate (via whatever UI or CLI you provide).
The execute stage checks gate resolution before proceeding.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from _shared.db.read import blackboard_read


def check_gate_resolved(workspace_id: str, action_id: str) -> bool:
    """
    Returns True if a gate for this workspace + action has been resolved.
    Returns False if the gate is still open or does not exist.
    """
    gate = blackboard_read(
        "gates",
        {"workspace_id": workspace_id, "status": "resolved"},
    )

    if not gate:
        return False

    # If gate is a list, check any of them covers this action
    if isinstance(gate, list):
        return any(
            g.get("resume_action_json", "{}") and action_id in g.get("resume_action_json", "")
            for g in gate
        )

    return action_id in gate.get("resume_action_json", "")


def resolve_gate(gate_id: str, answer: str) -> dict:
    """
    Resolve a gate with the operator's answer.
    Call this from your gate resolution UI or CLI.
    """
    from _shared.db.write import blackboard_write
    from datetime import datetime, timezone

    return blackboard_write(
        "gates",
        {"status": "resolved", "answer": answer, "resolved_at": datetime.now(timezone.utc).isoformat()},
        where={"id": gate_id},
        returning="*",
    )
