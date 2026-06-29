"""
Shared stage logic for the runnable business-operations worked example.

This example is intentionally generic. It proves the World architecture with
neutral operations logic: intake, quote, schedule, and follow-up disciplines
communicate by writing and reading artifacts in Postgres.
"""

from __future__ import annotations

import uuid
from typing import Any

from _shared.db.read import blackboard_read
from _shared.db.write import blackboard_write
from _shared.logging import log_activity, log_decision


CONFIG = {
    "ops-intake": {
        "kind": "intake_summary",
        "title": "Customer intake summary",
        "depends_on": [],
    },
    "ops-quote": {
        "kind": "quote_plan",
        "title": "Quote follow-up plan",
        "depends_on": ["intake_summary"],
    },
    "ops-schedule": {
        "kind": "schedule_plan",
        "title": "Scheduling plan",
        "depends_on": ["quote_plan"],
    },
    "ops-followup": {
        "kind": "followup_plan",
        "title": "Customer follow-up plan",
        "depends_on": ["schedule_plan"],
    },
}


def run_read(discipline: str, entity_id: str, workspace_id: str) -> dict[str, Any]:
    cfg = CONFIG[discipline]
    entity = blackboard_read("entities", {"id": entity_id})
    if not entity:
        return _packet(discipline, "01_read", entity_id, workspace_id, error=f"Entity {entity_id} not found")

    artifacts = _artifacts(entity_id)
    by_kind = {row["kind"]: row for row in artifacts}
    missing = [kind for kind in cfg["depends_on"] if kind not in by_kind]

    return _packet(
        discipline,
        "01_read",
        entity_id,
        workspace_id,
        state={
            "entity": entity,
            "required_artifacts": cfg["depends_on"],
            "available_artifacts": artifacts,
            "missing_artifacts": missing,
        },
        data_gaps=missing,
        ready_for_plan=not missing,
    )


def run_plan(discipline: str, entity_id: str, workspace_id: str, objective: str = "") -> dict[str, Any]:
    state_packet = blackboard_read(
        "stage_packets",
        {"workspace_id": workspace_id, "stage": "01_read", "discipline": discipline},
        order_by="created_at DESC",
        limit=1,
    )
    if not state_packet:
        return _packet(discipline, "02_plan", entity_id, workspace_id, error="No state packet - run 01_read first")

    state = (state_packet.get("packet") or {}).get("state", {})
    missing = state.get("missing_artifacts") or []
    if missing:
        return _packet(
            discipline,
            "02_plan",
            entity_id,
            workspace_id,
            plan={"summary": f"Blocked: missing {', '.join(missing)}", "actions": []},
            ready_for_execute=False,
        )

    entity = state["entity"]
    artifact = _build_artifact(discipline, entity, state.get("available_artifacts") or [], objective)
    action_id = f"{CONFIG[discipline]['kind']}_001"
    return _packet(
        discipline,
        "02_plan",
        entity_id,
        workspace_id,
        plan={
            "summary": f"Write {CONFIG[discipline]['title']} for {entity['name']}",
            "actions": [
                {
                    "id": action_id,
                    "type": "write_business_artifact",
                    "description": f"Persist {CONFIG[discipline]['kind']} to the blackboard",
                    "reversible": True,
                    "requires_gate": False,
                    "payload": artifact,
                }
            ],
        },
        ready_for_execute=True,
    )


def run_execute(discipline: str, entity_id: str, workspace_id: str) -> dict[str, Any]:
    plan_packet = blackboard_read(
        "stage_packets",
        {"workspace_id": workspace_id, "stage": "02_plan", "discipline": discipline},
        order_by="created_at DESC",
        limit=1,
    )
    if not plan_packet:
        return _packet(discipline, "03_execute", entity_id, workspace_id, error="No plan packet - run 02_plan first")

    actions = (plan_packet.get("packet") or {}).get("plan", {}).get("actions", [])
    results = []
    for action in actions:
        if action.get("type") != "write_business_artifact":
            results.append({"action_id": action.get("id"), "status": "skipped", "error": "unknown action type"})
            continue
        payload = action["payload"]
        artifact_id = str(uuid.uuid4())
        blackboard_write(
            "business_artifacts",
            {
                "id": artifact_id,
                "entity_id": entity_id,
                "workspace_id": workspace_id,
                "discipline": discipline,
                "kind": payload["kind"],
                "title": payload["title"],
                "body": payload["body"],
            },
        )
        results.append({"action_id": action["id"], "status": "done", "outcome": {"artifact_id": artifact_id}})

    all_passed = bool(results) and all(r["status"] == "done" for r in results)
    if all_passed:
        log_activity(
            entity_id=entity_id,
            workspace_id=workspace_id,
            action_type=f"{discipline}.artifact_written",
            description=f"{discipline} wrote {CONFIG[discipline]['kind']}",
            performed_by=f"{discipline}/03_execute",
        )
        log_decision(
            entity_id=entity_id,
            workspace_id=workspace_id,
            discipline=discipline,
            summary=f"{CONFIG[discipline]['title']} completed",
            rationale="Business operations workflow advanced through this discipline",
            status="done",
        )

    return _packet(
        discipline,
        "03_execute",
        entity_id,
        workspace_id,
        results=results,
        summary=f"{discipline}: {len([r for r in results if r['status'] == 'done'])} artifact(s) written",
        all_passed=all_passed,
    )


def _artifacts(entity_id: str) -> list[dict[str, Any]]:
    rows = blackboard_read("business_artifacts", {"entity_id": entity_id}, limit=50, order_by="created_at ASC") or []
    if isinstance(rows, dict):
        return [rows]
    return rows


def _build_artifact(
    discipline: str,
    entity: dict[str, Any],
    artifacts: list[dict[str, Any]],
    objective: str,
) -> dict[str, Any]:
    metadata = entity.get("metadata") or {}
    kind = CONFIG[discipline]["kind"]
    title = CONFIG[discipline]["title"]
    prior = {row["kind"]: row.get("body") or {} for row in artifacts}

    if discipline == "ops-intake":
        body = {
            "objective": objective or "Turn a customer request into a completed job",
            "customer_or_job": entity["name"],
            "business_type": metadata.get("business_type", "local service business"),
            "request": metadata.get("request", "new customer job request"),
            "source": metadata.get("source_channel", "phone or web form"),
            "success_metric": "job moved to quoted, scheduled, and followed up",
        }
    elif discipline == "ops-quote":
        intake = prior["intake_summary"]
        body = {
            "request": intake["request"],
            "quote_status": "draft_ready",
            "estimate_basis": metadata.get("estimate_basis", "standard service package"),
            "next_action": "send or approve quote follow-up",
            "owner_check": "required before sending to customer in a real integration",
        }
    elif discipline == "ops-schedule":
        quote = prior["quote_plan"]
        body = {
            "quote_status": quote["quote_status"],
            "schedule_window": metadata.get("preferred_window", "next available business day"),
            "crew_or_owner": metadata.get("owner", "operator"),
            "customer_confirmation": "pending",
        }
    elif discipline == "ops-followup":
        schedule = prior["schedule_plan"]
        body = {
            "scheduled_window": schedule["schedule_window"],
            "messages": ["confirmation", "day-before reminder", "post-job review request"],
            "channels": [metadata.get("preferred_channel", "sms"), "email"],
            "stop_condition": "customer replies or job is closed",
        }
    else:
        body = {"note": f"No artifact builder configured for {discipline}"}

    return {"kind": kind, "title": title, "body": body}


def _packet(discipline: str, stage: str, entity_id: str, workspace_id: str, **fields: Any) -> dict[str, Any]:
    packet = {
        "stage": stage,
        "discipline": discipline,
        "entity_id": entity_id,
        "workspace_id": workspace_id,
    }
    packet.update(fields)
    return packet
