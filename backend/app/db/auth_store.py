import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent.parent
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "auth_chat.sqlite3"


class AuthStore:
    def __init__(self, db_path: Optional[str] = None):
        configured_path = db_path or os.getenv("AUTH_DB_PATH")
        self.db_path = Path(configured_path) if configured_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    full_name TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS auth_tokens (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            120_000,
        )
        return digest.hex()

    def create_user(self, username: str, password: str, full_name: Optional[str] = None):
        username = username.strip()
        full_name = full_name.strip() if full_name else None
        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)

        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO users (username, password_hash, salt, full_name, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (username, password_hash, salt, full_name, self._now()),
                )
                return self.get_user_by_id(cursor.lastrowid)
        except sqlite3.IntegrityError:
            return None

    def authenticate_user(self, username: str, password: str):
        user = self.get_user_by_username(username)
        if not user:
            return None

        candidate_hash = self._hash_password(password, user["salt"])
        if not hmac.compare_digest(candidate_hash, user["password_hash"]):
            return None

        return user

    def create_token(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO auth_tokens (token, user_id, created_at) VALUES (?, ?, ?)",
                (token, user_id, self._now()),
            )
        return token

    def delete_token(self, token: str):
        with self._connect() as conn:
            conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))

    def get_user_by_token(self, token: str):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT users.*
                FROM auth_tokens
                JOIN users ON users.id = auth_tokens.user_id
                WHERE auth_tokens.token = ?
                """,
                (token,),
            ).fetchone()
        return row

    def get_user_by_id(self, user_id: int):
        with self._connect() as conn:
            return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    def get_user_by_username(self, username: str):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
                (username.strip(),),
            ).fetchone()

    def add_chat_message(self, user_id: int, role: str, content: str):
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO chat_messages (user_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, role, content, self._now()),
            )
            return cursor.lastrowid

    def list_chat_messages(self, user_id: int, limit: int = 200):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, role, content, created_at
                FROM chat_messages
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return list(reversed(rows))

    def clear_chat_messages(self, user_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))


auth_store = AuthStore()
