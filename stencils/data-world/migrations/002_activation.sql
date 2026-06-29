-- World - activation layer (the scheduler)
-- Run AFTER 001_init.sql:
--   psql $DATABASE_URL < migrations/002_activation.sql
--
-- This is the third leg of Hearsay-II: the scheduler. 001 gave you the
-- blackboard (state) and the disciplines do the work. This table is where the
-- watcher (lib/watch.py) proposes work when a discipline's activation condition
-- is met, and where the dispatcher (lib/dispatch.py) records what it opened.
--
-- Nothing here mutates an entity. An activation only says "this discipline
-- deserves attention for this entity, and here's why." Planning and execution
-- still run through the normal read -> plan -> execute flow and its gates.

CREATE TABLE IF NOT EXISTS activations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discipline      TEXT NOT NULL,                     -- which discipline wants to run
    entity_id       UUID REFERENCES entities(id),      -- the candidate entity
    workspace_id    UUID REFERENCES workspaces(id),    -- set once dispatched
    trigger_key     TEXT NOT NULL,                     -- "<discipline>:<entity_id>" - cooldown dedup key
    reason          TEXT,                              -- why this fired, in plain language
    risk            TEXT NOT NULL DEFAULT 'low',       -- low | medium | high
    status          TEXT NOT NULL DEFAULT 'proposed',  -- proposed | dispatched | gated | skipped | failed
    detail          JSONB DEFAULT '{}',                -- the candidate row + any context
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    dispatched_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_activations_status  ON activations(status, created_at);
CREATE INDEX IF NOT EXISTS idx_activations_trigger ON activations(trigger_key, created_at DESC);
