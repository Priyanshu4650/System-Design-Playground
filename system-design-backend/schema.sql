CREATE TABLE IF NOT EXISTS requests (
    request_id TEXT PRIMARY KEY,
    received_at TIMESTAMPTZ NOT NULL,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    idempotency_key TEXT,
    status TEXT NOT NULL,
    latency_ms INTEGER,
    retry_count INTEGER DEFAULT 0
);
