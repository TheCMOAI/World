"""
Blackboard write - all mutations to Postgres go through here.
Stage 03 owns domain writes; stage_runtime owns immutable packet writes.
"""

import os
import re
import json
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _json(value: Any) -> psycopg2.extras.Json:
    return psycopg2.extras.Json(value, dumps=lambda obj: json.dumps(obj, default=str))


def _conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)


def _identifier(value: str, *, label: str) -> str:
    if not isinstance(value, str) or not _IDENT.fullmatch(value):
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


def _returning(value: str | None) -> str:
    if not value:
        return ""
    if value == "*":
        return "RETURNING *"
    columns = [_identifier(part.strip(), label="returning column") for part in value.split(",")]
    return "RETURNING " + ", ".join(columns)


def _stage_context() -> tuple[str | None, str | None]:
    return os.environ.get("WORLD_ACTIVE_DISCIPLINE"), os.environ.get("WORLD_ACTIVE_STAGE")


def _binding_for(discipline: str) -> dict:
    world_root = Path(os.environ.get("WORLD_ROOT", Path(__file__).resolve().parents[3]))
    binding = world_root / "disciplines" / discipline / "binding.yaml"
    if not binding.exists():
        return {}
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required for write-surface enforcement") from exc
    return yaml.safe_load(binding.read_text()) or {}


def _enforce_write_surface(table: str) -> None:
    discipline, stage = _stage_context()
    if not discipline or not stage:
        return

    if table == "stage_packets":
        if os.environ.get("WORLD_INTERNAL_PACKET_WRITE") == "1":
            return
        raise PermissionError("stage_packets writes are owned by stage_runtime")

    if not stage.startswith("03"):
        raise PermissionError(f"{discipline}/{stage} may not mutate table {table!r}")

    binding = _binding_for(discipline)
    allowed = set(binding.get("write_surface") or ())
    if table not in allowed:
        raise PermissionError(
            f"{discipline}/{stage} may not mutate table {table!r}; "
            f"add it to disciplines/{discipline}/binding.yaml write_surface"
        )


def blackboard_write(
    table: str,
    data: dict,
    where: dict = None,
    returning: str = None,
) -> Any:
    """
    Insert or update a row in a table.

    If `where` is provided, performs an UPDATE. Otherwise INSERT.
    If `returning` is set (e.g. "*"), returns the resulting row(s).

    Serializes dict/list values to JSON automatically.
    Stamps updated_at on updates.
    """
    table_name = _identifier(table, label="table")
    _enforce_write_surface(table_name)

    # Serialize nested objects
    serialized = {}
    for k, v in data.items():
        key = _identifier(k, label="data column")
        if isinstance(v, (dict, list)):
            serialized[key] = _json(v)
        else:
            serialized[key] = v

    returning_clause = _returning(returning)

    with _conn() as conn:
        with conn.cursor() as cur:
            if where:
                # UPDATE
                serialized["updated_at"] = datetime.now(timezone.utc).isoformat()
                set_parts = [f"{k} = %s" for k in serialized]
                safe_where = {_identifier(k, label="where column"): v for k, v in where.items()}
                where_parts = [f"{k} = %s" for k in safe_where]
                sql = (
                    f"UPDATE {table_name} SET {', '.join(set_parts)} "
                    f"WHERE {' AND '.join(where_parts)} {returning_clause}"
                )
                cur.execute(sql, list(serialized.values()) + list(safe_where.values()))
            else:
                # INSERT
                if "created_at" not in serialized:
                    serialized["created_at"] = datetime.now(timezone.utc).isoformat()
                cols = list(serialized.keys())
                placeholders = ["%s"] * len(cols)
                sql = (
                    f"INSERT INTO {table_name} ({', '.join(cols)}) "
                    f"VALUES ({', '.join(placeholders)}) {returning_clause}"
                )
                cur.execute(sql, list(serialized.values()))

            if returning:
                rows = [dict(r) for r in cur.fetchall()]
                conn.commit()
                return rows[0] if len(rows) == 1 else rows

        conn.commit()
    return None
