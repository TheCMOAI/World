#!/usr/bin/env python3
"""
workflow_runtime.py - execute multi-discipline workflows.

A workflow is a YAML file under workflows/. Each step runs one discipline stage
inside one workspace. The blackboard remains the handoff surface: every stage
returns a packet, stage_runtime records it, and later stages read the packet or
domain tables from Postgres.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

WORLD_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_ROOT = WORLD_ROOT / "workflows"
sys.path.insert(0, str(WORLD_ROOT / "lib"))

import stage_runtime
from _shared.db.read import blackboard_read
from _shared.db.write import blackboard_write


def run_workflow(
    workflow: str,
    entity_id: str,
    *,
    workspace_id: str | None = None,
    inputs: dict[str, Any] | None = None,
    workflow_run_id: str | None = None,
) -> dict[str, Any]:
    spec = _load_workflow(workflow)
    provided_inputs = inputs
    inputs = dict(inputs or {})
    workflow_name = spec.get("name") or Path(workflow).stem

    if workflow_run_id:
        run_row = blackboard_read("workflow_runs", {"id": workflow_run_id})
        if not run_row:
            return {"error": f"workflow_run not found: {workflow_run_id}"}
        workspace_id = str(run_row["workspace_id"])
        if provided_inputs is None:
            inputs = dict(run_row.get("inputs") or {})
    else:
        workspace_id = workspace_id or _open_workspace(entity_id, workflow_name)
        run_row = blackboard_write(
            "workflow_runs",
            {
                "workflow": workflow_name,
                "entity_id": entity_id,
                "workspace_id": workspace_id,
                "status": "running",
                "inputs": inputs,
            },
            returning="*",
        )
        workflow_run_id = str(run_row["id"])

    steps = list(spec.get("steps") or [])
    if not steps:
        _finish_run(workflow_run_id, "failed", {"error": "workflow has no steps"})
        return {"workflow": workflow_name, "workflow_run_id": workflow_run_id, "error": "workflow has no steps"}

    completed = _completed_steps(workflow_run_id)
    outputs: list[dict[str, Any]] = []

    for index, step in enumerate(steps, start=1):
        if index in completed:
            outputs.append({"step_index": index, "status": "skipped_done"})
            continue

        gate_state = _check_step_gate(step, workflow_run_id, workspace_id, index)
        if gate_state.get("status") == "gated":
            _finish_run(workflow_run_id, "gated", gate_state)
            outputs.append(gate_state)
            return _result(workflow_name, workflow_run_id, workspace_id, "gated", outputs)
        if gate_state.get("status") == "rejected":
            _finish_run(workflow_run_id, "failed", gate_state)
            outputs.append(gate_state)
            return _result(workflow_name, workflow_run_id, workspace_id, "failed", outputs)

        _upsert_step(
            workflow_run_id,
            index,
            step,
            "running",
            {"label": step.get("label"), "started_at": datetime.now(timezone.utc).isoformat()},
        )
        args = _step_args(step, inputs)
        args["entity_id"] = entity_id
        args["workspace_id"] = workspace_id

        packet = stage_runtime.dispatch(step["discipline"], step.get("stage", "01_read"), args)
        status = _packet_status(packet)
        step_result = {
            "step_index": index,
            "discipline": step["discipline"],
            "stage": step.get("stage", "01_read"),
            "status": status,
            "packet": packet,
        }
        _upsert_step(workflow_run_id, index, step, status, step_result)
        outputs.append(step_result)

        if status != "done":
            _finish_run(workflow_run_id, "failed", step_result)
            return _result(workflow_name, workflow_run_id, workspace_id, "failed", outputs)

    _finish_run(workflow_run_id, "done", {"steps": len(steps)})
    return _result(workflow_name, workflow_run_id, workspace_id, "done", outputs)


def _load_workflow(workflow: str) -> dict[str, Any]:
    path = Path(workflow)
    if not path.suffix:
        path = WORKFLOWS_ROOT / f"{workflow}.yaml"
    elif not path.is_absolute():
        path = WORKFLOWS_ROOT / path
    if not path.exists():
        raise FileNotFoundError(f"workflow not found: {workflow}")
    data = yaml.safe_load(path.read_text()) or {}
    data["_path"] = str(path)
    return data


def _open_workspace(entity_id: str, workflow_name: str) -> str:
    row = blackboard_write(
        "workspaces",
        {"entity_id": entity_id, "name": f"workflow:{workflow_name}", "status": "open"},
        returning="*",
    )
    return str(row["id"])


def _completed_steps(workflow_run_id: str) -> dict[int, dict[str, Any]]:
    rows = blackboard_read("workflow_steps", {"workflow_run_id": workflow_run_id, "status": "done"}, limit=500)
    if not rows:
        return {}
    if isinstance(rows, dict):
        rows = [rows]
    return {int(row["step_index"]): row for row in rows}


def _upsert_step(
    workflow_run_id: str,
    index: int,
    step: dict[str, Any],
    status: str,
    result: dict[str, Any],
) -> None:
    where = {"workflow_run_id": workflow_run_id, "step_index": index}
    existing = blackboard_read("workflow_steps", where)
    row = {
        "workflow_run_id": workflow_run_id,
        "step_index": index,
        "discipline": step["discipline"],
        "stage": step.get("stage", "01_read"),
        "label": step.get("label"),
        "status": status,
        "result": result,
    }
    if existing:
        blackboard_write("workflow_steps", row, where=where)
    else:
        blackboard_write("workflow_steps", row)


def _finish_run(workflow_run_id: str, status: str, result: dict[str, Any]) -> None:
    row = {"status": status, "result": result}
    if status in {"done", "failed"}:
        row["ended_at"] = datetime.now(timezone.utc).isoformat()
    blackboard_write("workflow_runs", row, where={"id": workflow_run_id})


def _step_args(step: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    args = _expand(step.get("args") or {}, inputs)
    return dict(args)


def _expand(value: Any, inputs: dict[str, Any]) -> Any:
    if isinstance(value, str) and value.startswith("$inputs."):
        return inputs.get(value.split(".", 1)[1])
    if isinstance(value, list):
        return [_expand(v, inputs) for v in value]
    if isinstance(value, dict):
        return {k: _expand(v, inputs) for k, v in value.items()}
    return value


def _packet_status(packet: dict[str, Any]) -> str:
    if not isinstance(packet, dict):
        return "failed"
    if packet.get("error"):
        return "failed"
    if packet.get("all_passed") is False:
        return "failed"
    return "done"


def _check_step_gate(
    step: dict[str, Any],
    workflow_run_id: str,
    workspace_id: str,
    index: int,
) -> dict[str, Any]:
    if not step.get("gate_before"):
        return {"status": "open"}

    prior = blackboard_read(
        "workflow_steps",
        {"workflow_run_id": workflow_run_id, "step_index": index, "status": "gated"},
    )
    if prior:
        result = prior.get("result") or {}
        gate_id = result.get("gate_id")
        if gate_id:
            gate = blackboard_read("gates", {"id": gate_id})
            if gate and gate.get("status") == "resolved":
                return {"status": "open"}
            if gate and gate.get("status") == "rejected":
                return {"status": "rejected", "gate_id": gate_id}
            return {"status": "gated", "gate_id": gate_id, "step_index": index}

    gate = blackboard_write(
        "gates",
        {
            "workspace_id": workspace_id,
            "question": step.get("gate_question") or f"Run workflow step {index}: {step.get('label') or step['discipline']}?",
            "risk_level": step.get("risk_level", "medium"),
            "status": "open",
            "resume_action_json": {"workflow_run_id": workflow_run_id, "step_index": index},
        },
        returning="*",
    )
    result = {"status": "gated", "gate_id": str(gate["id"]), "step_index": index}
    _upsert_step(workflow_run_id, index, step, "gated", result)
    return result


def _result(
    workflow_name: str,
    workflow_run_id: str,
    workspace_id: str,
    status: str,
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "workflow": workflow_name,
        "workflow_run_id": workflow_run_id,
        "workspace_id": workspace_id,
        "status": status,
        "steps": steps,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a World workflow")
    parser.add_argument("--workflow", required=True, help="workflow name under workflows/ or path")
    parser.add_argument("--entity-id", required=True)
    parser.add_argument("--workspace-id")
    parser.add_argument("--workflow-run-id")
    parser.add_argument("--inputs", default="{}", help="JSON inputs available as $inputs.<key>")
    parser.add_argument("--json", action="store_true", dest="json_only")
    args = parser.parse_args()

    result = run_workflow(
        args.workflow,
        args.entity_id,
        workspace_id=args.workspace_id,
        workflow_run_id=args.workflow_run_id,
        inputs=json.loads(args.inputs),
    )
    if args.json_only:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"{result['workflow']} -> {result['status']} ({result['workflow_run_id']})")
        print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("status") in {"done", "gated"} else 1


if __name__ == "__main__":
    sys.exit(main())
