"""
Blackboard read - all reads from Postgres go through here.
No discipline reads the DB directly.
"""

import os
import re
import psycopg2
import psycopg2.extras
from typing import Any

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ORDER_DIRS = {"ASC", "DESC"}


def _conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)


def _identifier(value: str, *, label: str) -> str:
    if not isinstance(value, str) or not _IDENT.fullmatch(value):
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


def _order_by(value: str | None) -> str:
    if not value:
        return ""
    parts = []
    for raw_part in value.split(","):
        tokens = raw_part.strip().split()
        if not tokens or len(tokens) > 2:
            raise ValueError(f"Invalid order_by clause: {value!r}")
        column = _identifier(tokens[0], label="order_by column")
        if len(tokens) == 2:
            direction = tokens[1].upper()
            if direction not in _ORDER_DIRS:
                raise ValueError(f"Invalid order_by direction: {tokens[1]!r}")
            parts.append(f"{column} {direction}")
        else:
            parts.append(column)
    return "ORDER BY " + ", ".join(parts)


def _limit(value: int | None) -> str:
    if value is None:
        return ""
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid limit: {value!r}") from None
    if n < 1 or n > 500:
        raise ValueError("limit must be between 1 and 500")
    return f"LIMIT {n}"


def blackboard_read(
    table: str,
    filter: dict = None,
    limit: int = 50,
    order_by: str = None,
) -> Any:
    """
    Read rows from a table.

    Returns a single dict if filter produces exactly one row,
    a list of dicts otherwise (or None if no rows).
    """
    table_name = _identifier(table, label="table")
    where_clause = ""
    values = []

    if filter:
        conditions = []
        for col, val in filter.items():
            conditions.append(f"{_identifier(col, label='filter column')} = %s")
            values.append(val)
        where_clause = "WHERE " + " AND ".join(conditions)

    order_clause = _order_by(order_by)
    limit_clause = _limit(limit) if limit else ""

    sql = f"SELECT * FROM {table_name} {where_clause} {order_clause} {limit_clause}".strip()

    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, values)
            rows = [dict(r) for r in cur.fetchall()]

    if not rows:
        return None
    if len(rows) == 1 and filter:
        return rows[0]
    return rows
