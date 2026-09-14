from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path


class MemoryStore:
    def __init__(self, path: str, limit: int = 40):
        self.path = Path(path)
        self.limit = limit
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scope TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_conversations_scope ON conversations(scope, id)")
            db.commit()

    async def add(self, scope: str, user_id: int, role: str, content: str, created_at: float):
        if not content.strip():
            return
        async with self._lock:
            with self._connect() as db:
                db.execute(
                    "INSERT INTO conversations(scope,user_id,role,content,created_at) VALUES(?,?,?,?,?)",
                    (scope, user_id, role, content, created_at),
                )
                db.execute(
                    "DELETE FROM conversations WHERE scope=? AND id NOT IN "
                    "(SELECT id FROM conversations WHERE scope=? ORDER BY id DESC LIMIT ?)",
                    (scope, scope, self.limit),
                )
                db.commit()

    async def recent(self, scope: str) -> list[tuple[str, str]]:
        async with self._lock:
            with self._connect() as db:
                rows = db.execute(
                    "SELECT role, content FROM conversations WHERE scope=? ORDER BY id DESC LIMIT ?",
                    (scope, self.limit),
                ).fetchall()
        return list(reversed(rows))

    async def clear(self, scope: str):
        async with self._lock:
            with self._connect() as db:
                db.execute("DELETE FROM conversations WHERE scope=?", (scope,))
                db.commit()
