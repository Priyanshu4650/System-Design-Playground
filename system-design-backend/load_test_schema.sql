-- Load testing tables
CREATE TABLE IF NOT EXISTS test_runs (
    test_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, running, completed, failed
    config JSONB NOT NULL,
    total_requests INTEGER,
    succeeded INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    rate_limited INTEGER DEFAULT 0,
    duplicates INTEGER DEFAULT 0,
    retries_total INTEGER DEFAULT 0,
    avg_latency_ms FLOAT,
    p95_latency_ms FLOAT,
    p99_latency_ms FLOAT,
    duration_sec FLOAT
);

CREATE TABLE IF NOT EXISTS test_requests (
    id SERIAL PRIMARY KEY,
    test_id TEXT NOT NULL REFERENCES test_runs(test_id),
    request_id TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL, -- success, failed, rate_limited, duplicate
    status_code INTEGER,
    latency_ms FLOAT,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS request_events (
    id SERIAL PRIMARY KEY,
    test_id TEXT NOT NULL REFERENCES test_runs(test_id),
    request_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp_wall TIMESTAMPTZ NOT NULL,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_test_requests_test_id ON test_requests(test_id);
CREATE INDEX IF NOT EXISTS idx_request_events_test_id ON request_events(test_id);
CREATE INDEX IF NOT EXISTS idx_request_events_request_id ON request_events(request_id);