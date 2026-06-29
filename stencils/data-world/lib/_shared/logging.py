"""
logging.py - activity and decision logging helpers.

Every execute stage uses these instead of writing raw SQL.
Failure mode: logs to stderr and returns False rather than raising - logging
should never crash the caller.

Usage:
    from _shared.logging import log_activity, log_decision

    log_activity(
        entity_id="abc-123",
        workspace_id="ws-456",
        action_type="updated_status",
        description="Status changed from pending to active",
        performed_by="my-discipline/03_execute",
    )
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Optional

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from _shared.db.write import blackboard_write


def log_activity(
    entity_id: str,
    action_type: str,
    description: str,
    performed_by: str,
    *,
    workspace_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> bool:
    """
    Write a row to entity_activity_log. Returns True on success.
    This is append-only - never updates, always inserts.
    """
    try:
        blackboard_write("entity_activity_log", {
            "entity_id": entity_id,
            "workspace_id": workspace_id,
            "action_type": action_type,
            "outcome": {"description": description, **(metadata or {})},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return True
    except Exception as e:
        sys.stderr.write(f"[log_activity] failed: {e}\n")
        return False


def log_decision(
    entity_id: str,
    summary: str,
    rationale: str,
    *,
    workspace_id: Optional[str] = None,
    discipline: Optional[str] = None,
    status: str = "pending",
) -> bool:
    """
    Write a row to decisions. Returns True on success.
    Status values: pending | done | failed | superseded
    """
    try:
        blackboard_write("decisions", {
            "entity_id": entity_id,
            "workspace_id": workspace_id,
            "discipline": discipline,
            "summary": summary[:500],
            "rationale": rationale[:1000] if rationale else None,
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        return True
    except Exception as e:
        sys.stderr.write(f"[log_decision] failed: {e}\n")
        return False


def log_learning(
    entity_id: str,
    summary: str,
    *,
    discipline: Optional[str] = None,
    detail: Optional[dict] = None,
    source: Optional[str] = None,
) -> bool:
    """
    Write a row to learnings - an observation or pattern to carry forward.
    Learnings are read by 01_read stages on future runs.
    Returns True on success.
    """
    try:
        blackboard_write("learnings", {
            "entity_id": entity_id,
            "discipline": discipline,
            "summary": summary[:500],
            "detail": detail or {},
            "source": source,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        return True
    except Exception as e:
        sys.stderr.write(f"[log_learning] failed: {e}\n")
        return False
