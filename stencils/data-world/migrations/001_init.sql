-- World - core schema
-- Run: psql $DATABASE_URL < migrations/001_init.sql

-- ============================================================
-- Entities
-- The "client" equivalent in your World. Rename to match your
-- domain: projects, cases, customers, documents, etc.
-- ============================================================

CREATE TABLE IF NOT EXISTS entities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    slug            TEXT UNIQUE,
    status          TEXT NOT NULL DEFAULT 'active',  -- active | paused | archived
    metadata        JSONB DEFAULT '{}',              -- domain-specific fields go here
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Workspaces
-- A session of work scoped to an entity and a job.
-- Disciplines write their intermediate packets here.
-- ============================================================

CREATE TABLE IF NOT EXISTS workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id       UUID REFERENCES entities(id),
    name            TEXT,
    status          TEXT NOT NULL DEFAULT 'open',   -- open | done | archived
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    ended_at        TIMESTAMPTZ
);

-- ============================================================
-- Workflow runs
-- A multi-discipline workflow running inside one workspace.
-- ============================================================

CREATE TABLE IF NOT EXISTS workflow_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow        TEXT NOT NULL,
    entity_id       UUID REFERENCES entities(id),
    workspace_id    UUID REFERENCES workspaces(id),
    status          TEXT NOT NULL DEFAULT 'running', -- running | gated | done | failed
    inputs          JSONB DEFAULT '{}',
    result          JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    ended_at        TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS workflow_steps (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_run_id UUID REFERENCES workflow_runs(id),
    step_index      INTEGER NOT NULL,
    discipline      TEXT NOT NULL,
    stage           TEXT NOT NULL,
    label           TEXT,
    status          TEXT NOT NULL DEFAULT 'pending', -- pending | running | gated | done | failed
    result          JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(workflow_run_id, step_index)
);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_workspace ON workflow_runs(workspace_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_run ON workflow_steps(workflow_run_id, step_index);

-- ============================================================
-- Stage packets
-- Typed data flowing between stages. Each stage writes its
-- output here so the next stage can read it.
-- ============================================================

CREATE TABLE IF NOT EXISTS stage_packets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID REFERENCES workspaces(id),
    entity_id       UUID REFERENCES entities(id),
    discipline      TEXT NOT NULL,
    stage           TEXT NOT NULL,      -- e.g. "01_read"
    packet          JSONB NOT NULL,     -- the stage output
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stage_packets_workspace ON stage_packets(workspace_id, stage);

-- ============================================================
-- Example notes
-- A tiny domain table used by the built-in example-notes discipline.
-- Keep it while learning the pattern; replace it with your own tables
-- when you build a real World.
-- ============================================================

CREATE TABLE IF NOT EXISTS entity_notes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id       UUID REFERENCES entities(id),
    workspace_id    UUID REFERENCES workspaces(id),
    topic           TEXT DEFAULT 'general',
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_entity_notes_entity ON entity_notes(entity_id, created_at DESC);

-- ============================================================
-- Business operations worked example artifacts
-- A runnable generic example. Intake, quote, schedule, and follow-up
-- disciplines communicate through these artifacts.
-- ============================================================

CREATE TABLE IF NOT EXISTS business_artifacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id       UUID REFERENCES entities(id),
    workspace_id    UUID REFERENCES workspaces(id),
    discipline      TEXT NOT NULL,
    kind            TEXT NOT NULL,
    title           TEXT NOT NULL,
    body            JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_business_artifacts_entity_kind ON business_artifacts(entity_id, kind, created_at DESC);

-- ============================================================
-- Decisions
-- What was decided and why. The LLM writes here after acting.
-- This is the memory - re-read at the start of future runs.
-- ============================================================

CREATE TABLE IF NOT EXISTS decisions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id       UUID REFERENCES entities(id),
    workspace_id    UUID REFERENCES workspaces(id),
    discipline      TEXT,
    summary         TEXT NOT NULL,
    rationale       TEXT,
    outcome         TEXT,               -- filled in after the action completes
    status          TEXT DEFAULT 'pending',  -- pending | done | failed | superseded
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Learnings
-- Observations, patterns, preferences discovered over time.
-- Disciplines read these at the start of each run.
-- ============================================================

CREATE TABLE IF NOT EXISTS learnings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id       UUID REFERENCES entities(id),
    discipline      TEXT,
    summary         TEXT NOT NULL,
    detail          JSONB DEFAULT '{}',
    status          TEXT DEFAULT 'active',   -- active | paused | superseded
    source          TEXT,                    -- what generated this learning
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Gates
-- Human approval required before proceeding.
-- Execute stages check here before running gated actions.
-- ============================================================

CREATE TABLE IF NOT EXISTS gates (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        UUID REFERENCES workspaces(id),
    question            TEXT NOT NULL,
    risk_level          TEXT DEFAULT 'medium',   -- low | medium | high | critical
    status              TEXT DEFAULT 'open',     -- open | resolved | rejected | dismissed
    answer              TEXT,
    resume_action_json  JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ
);

-- ============================================================
-- Entity activity log
-- Append-only history of what happened to each entity.
-- Never update rows here - only insert.
-- ============================================================

CREATE TABLE IF NOT EXISTS entity_activity_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id       UUID REFERENCES entities(id),
    workspace_id    UUID REFERENCES workspaces(id),
    action_type     TEXT NOT NULL,
    action_id       TEXT,
    status          TEXT,
    outcome         JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
