"""
Base de datos SQLite para rastrear seguidores ya procesados.
Guarda: id, username, fecha en que se les envió el mensaje.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "followers.db")


def init_db():
    """Crea las tablas si no existen."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_followers (
                id          TEXT PRIMARY KEY,
                username    TEXT,
                messaged_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS known_followers (
                id          TEXT PRIMARY KEY,
                username    TEXT,
                first_seen  TEXT NOT NULL
            )
        """)
        conn.commit()


def is_already_messaged(user_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_followers WHERE id = ?", (user_id,)
        ).fetchone()
    return row is not None


def mark_as_messaged(user_id: str, username: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_followers (id, username, messaged_at) VALUES (?, ?, ?)",
            (user_id, username, datetime.utcnow().isoformat()),
        )
        conn.commit()


def get_known_follower_ids() -> set:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT id FROM known_followers").fetchall()
    return {row[0] for row in rows}


def save_known_followers(followers: list[dict]):
    """Recibe lista de dicts con 'id' y 'username'."""
    now = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO known_followers (id, username, first_seen) VALUES (?, ?, ?)",
            [(f["id"], f.get("username", ""), now) for f in followers],
        )
        conn.commit()


def find_new_followers(current_followers: list[dict]) -> list[dict]:
    """Devuelve solo los seguidores que no estaban en la BD antes."""
    known_ids = get_known_follower_ids()
    new_ones = [f for f in current_followers if f["id"] not in known_ids]
    return new_ones
