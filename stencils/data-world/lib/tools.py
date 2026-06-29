"""
World Tool Verbs - the LLM's toolbelt.

These are the only tools the World operator calls. No raw SQL, no shell commands,
no direct file reads outside the World folder. The tools are the fence.

Wire these into your harness's tool definitions (Claude tool_use, OpenAI function
calling, etc.). Each function here is one tool.
"""

from pathlib import Path
from _shared.db.read import blackboard_read
from _shared.db.write import blackboard_write
from stage_runtime import dispatch
from workflow_runtime import run_workflow as _run_workflow

WORLD_ROOT = Path(__file__).parent.parent


def run_stage(discipline: str, stage: str, args: dict) -> dict:
    """
    Activate a stage in a discipline.

    discipline: the discipline folder name (e.g. "customer-research")
    stage:      the stage name or number prefix (e.g. "01_read" or "01")
    args:       inputs required by the stage (entity_id, workspace_id, etc.)

    Returns the stage's output packet.
    """
    return dispatch(discipline, stage, args)


def run_workflow(
    workflow: str,
    entity_id: str,
    workspace_id: str = None,
    inputs: dict = None,
    workflow_run_id: str = None,
) -> dict:
    """
    Run a multi-discipline workflow from workflows/<name>.yaml.

    The workflow runner opens or reuses one workspace, runs each stage in order,
    and records workflow_runs/workflow_steps rows in the blackboard.
    """
    return _run_workflow(
        workflow,
        entity_id,
        workspace_id=workspace_id,
        inputs=inputs,
        workflow_run_id=workflow_run_id,
    )


def read(table: str, filter: dict = None, limit: int = 50, order_by: str = None) -> list:
    """
    Read rows from the blackboard (Postgres).

    table:    table name
    filter:   dict of column=value conditions (ANDed)
    limit:    max rows to return
    order_by: e.g. "created_at DESC"

    Returns a list of row dicts.
    """
    return blackboard_read(table, filter, limit=limit, order_by=order_by)


def manage(entity_action: str, payload: dict) -> dict:
    """
    Create, update, or archive an entity in the blackboard.

    entity_action: "entity.create", "entity.update", or "entity.archive"
    payload:       the data for the action

    Returns the resulting row.
    """
    allowed_actions = {"entity.create", "entity.update", "entity.archive"}
    if entity_action not in allowed_actions:
        return {"error": f"Unknown entity_action: {entity_action}. Use one of: {', '.join(sorted(allowed_actions))}"}

    action = entity_action.split(".", 1)[1]
    payload = dict(payload or {})

    if action == "create":
        if not payload.get("name"):
            return {"error": "entity.create requires 'name' in payload"}
        row = {
            "name": payload["name"],
            "slug": payload.get("slug"),
            "status": payload.get("status", "active"),
            "metadata": payload.get("metadata") or {},
        }
        return blackboard_write("entities", row, returning="*")
    if action == "update":
        entity_id = payload.pop("id", None)
        if not entity_id:
            return {"error": "update requires 'id' in payload"}
        allowed = {"name", "slug", "status", "metadata"}
        row = {k: v for k, v in payload.items() if k in allowed}
        if not row:
            return {"error": f"entity.update requires at least one field: {', '.join(sorted(allowed))}"}
        return blackboard_write("entities", row, where={"id": entity_id}, returning="*")
    if action == "archive":
        entity_id = payload.get("id")
        if not entity_id:
            return {"error": "archive requires 'id' in payload"}
        return blackboard_write("entities", {"status": "archived"}, where={"id": entity_id}, returning="*")

    return {"error": f"Unknown action: {action}. Use create | update | archive"}


def gate(question: str, workspace_id: str, risk_level: str = "medium", resume_action: dict = None) -> dict:
    """
    Surface a decision gate to the operator before proceeding.

    question:      what the operator needs to decide
    workspace_id:  the active workspace
    risk_level:    low | medium | high | critical
    resume_action: what to do when the gate is resolved (stored in DB)

    Returns {"gate_id": "...", "status": "open"} - execution stops until resolved.
    """
    import uuid
    from datetime import datetime, timezone

    gate_row = {
        "id": str(uuid.uuid4()),
        "workspace_id": workspace_id,
        "question": question,
        "risk_level": risk_level,
        "status": "open",
        "resume_action_json": resume_action or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    blackboard_write("gates", gate_row)

    return {"gate_id": gate_row["id"], "status": "open", "question": question}
