CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    arguments TEXT,
    result TEXT,
    success INTEGER NOT NULL,
    is_destructive INTEGER NOT NULL
);