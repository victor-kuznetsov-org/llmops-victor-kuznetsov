"""Session memory in our own Lakebase database: chat_sessions and chat_messages."""

import json
from typing import Any


class ChatMemory:
    def __init__(self, conn: Any) -> None:
        self.conn = conn
        conn.execute(
            "CREATE TABLE IF NOT EXISTS chat_sessions ("
            "session_id text PRIMARY KEY, created_at timestamp DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS chat_messages ("
            "id serial PRIMARY KEY, session_id text NOT NULL REFERENCES chat_sessions, "
            "message jsonb NOT NULL, created_at timestamp DEFAULT CURRENT_TIMESTAMP)"
        )

    def save(self, session_id: str, messages: list[dict]) -> None:
        self.conn.execute(
            "INSERT INTO chat_sessions (session_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (session_id,),
        )
        for m in messages:
            self.conn.execute(
                "INSERT INTO chat_messages (session_id, message) VALUES (%s, %s)",
                (session_id, json.dumps(m)),
            )

    def load(self, session_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT message FROM chat_messages WHERE session_id = %s ORDER BY id",
            (session_id,),
        ).fetchall()
        return [r[0] for r in rows]
