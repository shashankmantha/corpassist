"""
CorpAssist persistent chat history.

A small SQLite store under config.DATA_DIR, keyed per user, so a conversation
survives page refreshes and container restarts. One row per message.
"""
import json
import os
import sqlite3
import time

import config

_DB_PATH = os.path.join(config.DATA_DIR, "chat_history.db")


def _conn():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS messages ("
        "  username TEXT NOT NULL,"
        "  role     TEXT NOT NULL,"       # 'user' or 'assistant'
        "  content  TEXT NOT NULL,"
        "  sources  TEXT,"                # JSON list of retrieved source names
        "  ts       REAL NOT NULL"
        ")"
    )
    return conn


def load(username: str):
    """Return this user's messages oldest-first as UI-ready dicts."""
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT role, content, sources FROM messages "
            "WHERE username = ? ORDER BY ts",
            (username,),
        ).fetchall()
    finally:
        conn.close()
    out = []
    for role, content, sources in rows:
        msg = {"role": role, "content": content}
        if sources:
            try:
                msg["sources"] = json.loads(sources)
            except (ValueError, TypeError):
                pass
        out.append(msg)
    return out


def append(username: str, role: str, content: str, sources=None):
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO messages (username, role, content, sources, ts) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, role, content, json.dumps(sources or []), time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def clear(username: str):
    conn = _conn()
    try:
        conn.execute("DELETE FROM messages WHERE username = ?", (username,))
        conn.commit()
    finally:
        conn.close()
