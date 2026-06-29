#!/usr/bin/env bash
# quickstart.sh - get a data-world running in under 5 minutes.
# Run from your data-world root:  bash quickstart.sh
set -euo pipefail

# load .env if present
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
  echo "Loaded .env"
fi

echo ""
echo "=== World quickstart ==="
echo ""

# --- Python ---
if ! command -v python3 &>/dev/null; then
  echo "Error: python3 not found. Install Python 3.11+ first."
  exit 1
fi

PYTHON=$(command -v python3)
PY_OK=$($PYTHON -c "import sys; print('ok' if sys.version_info >= (3,11) else 'old')")
if [ "$PY_OK" != "ok" ]; then
  echo "Error: Python 3.11+ required. ($($PYTHON --version) found)"
  exit 1
fi
echo "[ok] Python $($PYTHON --version | cut -d' ' -f2)"

# --- DATABASE_URL ---
if [ -z "${DATABASE_URL:-}" ]; then
  echo ""
  echo "Error: DATABASE_URL is not set."
  echo ""
  echo "If you have Docker, run this first:"
  echo ""
  echo "  docker run -d --name world-pg \\"
  echo "    -e POSTGRES_PASSWORD=world \\"
  echo "    -e POSTGRES_DB=world \\"
  echo "    -p 5432:5432 postgres:16"
  echo ""
  echo "Then:"
  echo "  export DATABASE_URL=postgresql://postgres:world@localhost:5432/world"
  echo ""
  echo "Or point DATABASE_URL at any running Postgres instance."
  exit 1
fi
echo "[ok] DATABASE_URL set"

# --- requirements ---
echo "Installing requirements..."
$PYTHON -m pip install -r requirements.txt --quiet
echo "[ok] requirements installed"

# --- anthropic (for harness.py) ---
if [ "${SKIP_ANTHROPIC:-}" != "1" ]; then
  echo "Installing anthropic..."
  $PYTHON -m pip install anthropic --quiet
  echo "[ok] anthropic installed"
fi

# --- migration ---
echo "Running migration..."
$PYTHON - <<'PYEOF'
import os, glob, psycopg2
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
for migration in sorted(glob.glob("migrations/*.sql")):
    with open(migration) as f:
        cur.execute(f.read())
conn.commit()
conn.close()
print("[ok] migration complete")
PYEOF

# --- seed one entity ---
echo "Seeding example entity..."
$PYTHON - <<'PYEOF'
import os, json, psycopg2
from datetime import datetime, timezone
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
now = datetime.now(timezone.utc)
cur.execute(
    """
    INSERT INTO entities (name, slug, status, metadata, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (slug) DO UPDATE
      SET name = EXCLUDED.name,
          status = EXCLUDED.status,
          metadata = EXCLUDED.metadata,
          updated_at = EXCLUDED.updated_at
    RETURNING id
    """,
    (
        "Quickstart Entity",
        "quickstart-entity",
        "active",
        json.dumps({
            "source": "quickstart",
            "example": True,
            "business_type": "local service business",
            "request": "new customer job request",
            "preferred_window": "next available business day",
            "owner_email": "owner@example.com",
        }),
        now,
        now,
    ),
)
eid = cur.fetchone()[0]
cur.execute(
    """
    INSERT INTO workspaces (entity_id, name, status, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id
    """,
    (eid, "quickstart smoke", "open", now, now),
)
wid = cur.fetchone()[0]
conn.commit()
conn.close()
print(f"[ok] seeded entity: {eid}")
print(f"[ok] opened workspace: {wid}")
PYEOF

# --- smoke the default note workflow ---
echo "Running example-notes workflow smoke..."
$PYTHON - <<'PYEOF'
import json
import os
import sys

import psycopg2

sys.path.insert(0, "lib")
import workflow_runtime

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute("SELECT id FROM entities WHERE slug = 'quickstart-entity'")
entity_id = str(cur.fetchone()[0])
conn.close()

result = workflow_runtime.run_workflow(
    "example-notes",
    entity_id,
    inputs={"content": "Quickstart note from the default World workflow smoke."},
)
if result.get("status") != "done":
    raise SystemExit(json.dumps(result, indent=2, default=str))

print("[ok] example-notes workflow passed")
PYEOF

# --- smoke generic business-ops worked example ---
echo "Running service-business-ops workflow smoke..."
$PYTHON - <<'PYEOF'
import json
import os
import sys

import psycopg2

sys.path.insert(0, "lib")
import workflow_runtime

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute("SELECT id FROM entities WHERE slug = 'quickstart-entity'")
entity_id = str(cur.fetchone()[0])
conn.close()

result = workflow_runtime.run_workflow(
    "service-business-ops",
    entity_id,
    inputs={"objective": "Prove the World stencil can run a service-business operations loop."},
)
if result.get("status") != "done":
    raise SystemExit(json.dumps(result, indent=2, default=str))

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute(
    """
    SELECT kind
    FROM business_artifacts
    WHERE entity_id = %s
    ORDER BY created_at ASC
    """,
    (entity_id,),
)
kinds = [row[0] for row in cur.fetchall()]
conn.close()
required = ["intake_summary", "quote_plan", "schedule_plan", "followup_plan"]
missing = [kind for kind in required if kind not in kinds]
if missing:
    raise SystemExit(f"Missing business artifacts: {missing}; got {kinds}")

print("[ok] service-business-ops workflow passed")
PYEOF

# --- world_doctor ---
echo "Running world_doctor..."
$PYTHON lib/world_doctor.py

echo ""
echo "=== Ready ==="
echo ""
echo "Your World is running. Two ways to use it:"
echo ""
echo "  1. Point any Claude Code / Codex session at agent.md and start typing."
echo ""
echo "  2. Use harness.py (requires ANTHROPIC_API_KEY):"
echo "       export ANTHROPIC_API_KEY=sk-ant-..."
echo "       python harness.py 'What entities exist in this world?'"
echo "       python harness.py   # interactive REPL"
echo ""
echo "Generic business-ops example workflow is installed:"
echo "       python lib/workflow_runtime.py --workflow service-business-ops --entity-id <uuid> --json"
echo ""
