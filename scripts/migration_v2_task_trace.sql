-- Migration: Create task_trace table for SkyClaw-inspired resilience
-- Database: hbms_master (or the one defined in DATABASE_URL)
CREATE TABLE IF NOT EXISTS task_trace (
    task_id UUID PRIMARY KEY,
    parent_id UUID,
    task_type VARCHAR(50) NOT NULL,
    payload JSONB,
    status VARCHAR(20) DEFAULT 'PENDING',
    step_index INTEGER DEFAULT 0,
    trace_log JSONB DEFAULT '[]'::jsonb,
    error_msg TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- Index for faster status lookups during worker recovery
CREATE INDEX IF NOT EXISTS idx_task_trace_status ON task_trace(status)
WHERE status IN ('PENDING', 'IN_PROGRESS');
-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ language 'plpgsql';
CREATE OR REPLACE TRIGGER update_task_trace_modtime BEFORE
UPDATE ON task_trace FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();