-- SQLite Load testing tables
CREATE TABLE IF NOT EXISTS test_runs (
    test_id TEXT PRIMARY KEY,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME,
    status TEXT NOT NULL DEFAULT 'pending',
    config TEXT NOT NULL,
    total_requests INTEGER,
    succeeded INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    rate_limited INTEGER DEFAULT 0,
    duplicates INTEGER DEFAULT 0,
    retries_total INTEGER DEFAULT 0,
    avg_latency_ms REAL,
    p95_latency_ms REAL,
    p99_latency_ms REAL,
    duration_sec REAL
);

CREATE TABLE IF NOT EXISTS test_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    started_at DATETIME NOT NULL,
    completed_at DATETIME,
    status TEXT NOT NULL,
    status_code INTEGER,
    latency_ms REAL,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY (test_id) REFERENCES test_runs(test_id)
);

CREATE TABLE IF NOT EXISTS request_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp_wall DATETIME NOT NULL,
    metadata TEXT,
    FOREIGN KEY (test_id) REFERENCES test_runs(test_id)
);

CREATE INDEX IF NOT EXISTS idx_test_requests_test_id ON test_requests(test_id);
CREATE INDEX IF NOT EXISTS idx_request_events_test_id ON request_events(test_id);
CREATE INDEX IF NOT EXISTS idx_request_events_request_id ON request_events(request_id);