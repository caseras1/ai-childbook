from __future__ import annotations

import hashlib
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "app.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            subject TEXT,
            path TEXT NOT NULL,
            page_count INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def _check_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    check = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return secrets.compare_digest(digest, check)


def create_user(email: str, password: str) -> int:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
        (email, _hash_password(password), int(time.time())),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row


def create_token(user_id: int) -> str:
    token = secrets.token_hex(24)
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tokens (token, user_id, created_at) VALUES (?, ?, ?)",
        (token, user_id, int(time.time())),
    )
    conn.commit()
    conn.close()
    return token


def get_user_by_token(token: str) -> Optional[sqlite3.Row]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT users.* FROM tokens JOIN users ON tokens.user_id = users.id WHERE tokens.token = ?",
        (token,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def authenticate(email: str, password: str) -> Optional[int]:
    user = get_user_by_email(email)
    if not user:
        return None
    if not _check_password(password, user["password_hash"]):
        return None
    return int(user["id"])


def save_story_meta(user_id: int, title: str, subject: str | None, path: str, page_count: int) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO stories (user_id, title, subject, path, page_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, title, subject, path, page_count, int(time.time())),
    )
    conn.commit()
    conn.close()


def list_story_meta(user_id: Optional[int] = None) -> list[dict]:
    conn = _connect()
    cur = conn.cursor()
    if user_id:
        cur.execute(
            "SELECT * FROM stories WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
    else:
        cur.execute("SELECT * FROM stories ORDER BY created_at DESC")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows
