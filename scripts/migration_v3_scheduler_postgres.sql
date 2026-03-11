-- Migration V3: Create Scheduler Tables in PostgreSQL
-- Target DB: hbms_master
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    time VARCHAR(10) NOT NULL,
    type VARCHAR(50) NOT NULL,
    params JSONB DEFAULT '{}',
    command VARCHAR(500),
    enabled BOOLEAN DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS task_history (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(100) NOT NULL,
    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    message TEXT
);
-- Indexing for performance
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_enabled ON scheduled_tasks(enabled);
CREATE INDEX IF NOT EXISTS idx_task_history_execution_time ON task_history(execution_time);