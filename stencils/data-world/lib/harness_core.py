"""
Provider-neutral harness core for a data-world.

The provider adapters only translate model API shapes. This module owns the
World contract: session workspace, prompt context, tool schemas, tool dispatch,
and gate resolution helpers.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _shared.db.read import blackboard_read
from _shared.db.write import blackboard_write
from tools import gate, manage, read, run_stage, run_workflow

WORLD_ROOT = Path(__file__).resolve().parent.parent

COMMON_TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "run_stage",
        "description": (
            "Activate a stage in a discipline. Always pass args with entity_id and "
            "workspace_id for entity-scoped stages. The harness injects workspace_id "
            "when it is omitted."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "discipline": {
                    "type": "string",
                    "description": "Discipline folder name, e.g. example-notes.",
                },
                "stage": {
                    "type": "string",
                    "description": "Stage name or prefix, e.g. 01_read or 01.",
                },
                "args": {
                    "type": "object",
                    "description": "Stage inputs. Include entity_id when the stage is entity-scoped.",
                    "additionalProperties": True,
                },
            },
            "required": ["discipline", "stage", "args"],
        },
    },
    {
        "name": "run_workflow",
        "description": (
            "Run a multi-discipline workflow from workflows/<name>.yaml. Use this "
            "when a request naturally spans several disciplines."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "workflow": {
                    "type": "string",
                    "description": "Workflow name under workflows/, e.g. service-business-ops.",
                },
                "entity_id": {"type": "string"},
                "workspace_id": {"type": "string"},
                "workflow_run_id": {
                    "type": "string",
                    "description": "Existing run id when resuming a gated workflow.",
                },
                "inputs": {
                    "type": "object",
                    "additionalProperties": True,
                    "description": "Workflow inputs available to YAML steps as $inputs.<key>.",
                },
            },
            "required": ["workflow", "entity_id"],
        },
    },
    {
        "name": "read",
        "description": "Read rows from the Postgres blackboard. Use before asserting state.",
        "parameters": {
            "type": "object",
            "properties": {
                "table": {
                    "type": "string",
                    "description": (
                        "Table name. Core tables: entities, workspaces, stage_packets, "
                        "decisions, learnings, gates, entity_activity_log, entity_notes, "
                        "workflow_runs, workflow_steps, business_artifacts, activations."
                    ),
                },
                "filter": {
                    "type": "object",
                    "description": "Column=value filters, ANDed together.",
                    "additionalProperties": True,
                },
                "limit": {"type": "integer", "default": 50, "minimum": 1, "maximum": 500},
                "order_by": {
                    "type": "string",
                    "description": "Simple order clause, e.g. created_at DESC.",
                },
            },
            "required": ["table"],
        },
    },
    {
        "name": "manage",
        "description": "Create, update, or archive rows in the default entities table.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_action": {
                    "type": "string",
                    "enum": ["entity.create", "entity.update", "entity.archive"],
                },
                "payload": {
                    "type": "object",
                    "description": (
                        "For create: name, optional slug/status/metadata. "
                        "For update/archive: include id."
                    ),
                    "additionalProperties": True,
                },
            },
            "required": ["entity_action", "payload"],
        },
    },
    {
        "name": "gate",
        "description": (
            "Open an operator approval gate before an irreversible, externally visible, "
            "or spend-affecting action. Execution stops until the gate is resolved."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "workspace_id": {"type": "string"},
                "risk_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "default": "medium",
                },
                "resume_action": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
            "required": ["question"],
        },
    },
]


def anthropic_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": spec["name"],
            "description": spec["description"],
            "input_schema": spec["parameters"],
        }
        for spec in COMMON_TOOL_SPECS
    ]


def openai_tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": spec["name"],
                "description": spec["description"],
                "parameters": spec["parameters"],
            },
        }
        for spec in COMMON_TOOL_SPECS
    ]


def load_system_prompt(world_root: Path = WORLD_ROOT) -> str:
    agent_md = (world_root / "agent.md").read_text()
    disciplines_md = world_root / "DISCIPLINES.md"
    parts = [agent_md]
    if disciplines_md.exists():
        parts.append(disciplines_md.read_text())
    parts.append(
        """
## Harness Contract

You are inside one active workspace for this session. Use the workspace_id from
the turn context in every stage or gate call. Read the blackboard before making
claims. Work through the five tools only: run_stage, run_workflow, read, manage, gate.
When a gate opens, stop and tell the operator exactly what approval is needed.
Do not invent shell commands, raw SQL, or hidden files.
""".strip()
    )
    return "\n\n---\n\n".join(parts)


def open_workspace(entity_id: str | None = None, name: str = "harness session") -> str:
    row = {
        "entity_id": entity_id,
        "name": name,
        "status": "open",
    }
    written = blackboard_write("workspaces", row, returning="*")
    return str(written["id"])


def turn_context(workspace_id: str) -> dict[str, Any]:
    workspace = blackboard_read("workspaces", {"id": workspace_id})
    packets = blackboard_read(
        "stage_packets",
        {"workspace_id": workspace_id},
        limit=10,
        order_by="created_at DESC",
    )
    gates = blackboard_read(
        "gates",
        {"workspace_id": workspace_id, "status": "open"},
        limit=10,
        order_by="created_at ASC",
    )
    return {
        "workspace_id": workspace_id,
        "workspace": workspace or {},
        "recent_stage_packets": _as_list(packets),
        "open_gates": _as_list(gates),
    }


def user_message_with_context(user_message: str, workspace_id: str) -> str:
    context_json = json.dumps(turn_context(workspace_id), indent=2, default=str)
    return (
        "World turn context from the blackboard:\n"
        f"```json\n{context_json}\n```\n\n"
        f"Operator message:\n{user_message}"
    )


def call_tool(name: str, args: dict[str, Any], *, workspace_id: str | None = None) -> dict[str, Any]:
    args = dict(args or {})
    if name == "run_stage":
        stage_args = dict(args.get("args") or {})
        if workspace_id and not stage_args.get("workspace_id"):
            stage_args["workspace_id"] = workspace_id
        return run_stage(
            discipline=args["discipline"],
            stage=args.get("stage", "01"),
            args=stage_args,
        )
    if name == "run_workflow":
        return run_workflow(
            workflow=args["workflow"],
            entity_id=args["entity_id"],
            workspace_id=args.get("workspace_id") or workspace_id,
            inputs=args.get("inputs"),
            workflow_run_id=args.get("workflow_run_id"),
        )
    if name == "read":
        return read(
            table=args["table"],
            filter=args.get("filter"),
            limit=args.get("limit", 50),
            order_by=args.get("order_by"),
        )
    if name == "manage":
        return manage(args["entity_action"], args["payload"])
    if name == "gate":
        if workspace_id and not args.get("workspace_id"):
            args["workspace_id"] = workspace_id
        return gate(
            question=args["question"],
            workspace_id=args["workspace_id"],
            risk_level=args.get("risk_level", "medium"),
            resume_action=args.get("resume_action"),
        )
    return {"error": f"unknown tool: {name}"}


def call_tool_json(name: str, args: dict[str, Any], *, workspace_id: str | None = None) -> str:
    try:
        return json.dumps(call_tool(name, args, workspace_id=workspace_id), default=str)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def list_open_gates(workspace_id: str | None = None) -> list[dict[str, Any]]:
    filters = {"status": "open"}
    if workspace_id:
        filters["workspace_id"] = workspace_id
    gates = blackboard_read("gates", filters, limit=50, order_by="created_at ASC")
    return _as_list(gates)


def resolve_gate(gate_id: str, *, approved: bool, answer: str = "") -> dict[str, Any]:
    status = "resolved" if approved else "rejected"
    written = blackboard_write(
        "gates",
        {
            "status": status,
            "answer": answer or status,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        },
        where={"id": gate_id, "status": "open"},
        returning="*",
    )
    if not written:
        return {"error": f"Gate {gate_id} not found or already resolved"}
    return written


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
