"""
Audit logging — records every tool call to a local SQLite database.
"""

import sqlite3
import json
import os
from datetime import datetime, timezone

_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit.db")


def _get_connection():
    conn = sqlite3.connect(_DB_PATH)
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())
    return conn


def log_tool_call(tool_name: str, arguments: dict, result: str, success: bool, is_destructive: bool) -> None:
    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT INTO audit_log (timestamp, tool_name, arguments, result, success, is_destructive)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                tool_name,
                json.dumps(arguments),
                result[:2000],  # truncate very long results
                int(success),
                int(is_destructive),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def query_audit_log(limit: int = 20) -> list[dict]:
    conn = _get_connection()
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()