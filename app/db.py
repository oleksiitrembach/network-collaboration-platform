from __future__ import annotations

import hashlib
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class User:
    id: int
    username: str
    role: str


@dataclass(slots=True)
class Task:
    id: int
    title: str
    description: str
    owner: str
    created_at: datetime


@dataclass(slots=True)
class AuditEvent:
    id: int
    event_type: str
    actor: str
    result: str
    details: str
    created_at: datetime


class Database:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user'
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    result TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            self._ensure_role_column(con)
            con.commit()
        
    def _ensure_role_column(self, con: sqlite3.Connection) -> None:
        columns = [row["name"] for row in con.execute("PRAGMA table_info(users)").fetchall()]
        if "role" not in columns:
            con.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def register_user(self, username: str, password: str) -> User:
        password_hash = self._hash_password(password)
        with self._lock, self._connect() as con:
            self._ensure_role_column(con)
            users_count = con.execute("SELECT COUNT(1) as c FROM users").fetchone()["c"]
            role = "admin" if users_count == 0 else "user"
            cursor = con.execute(
                "INSERT INTO users(username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role),
            )
            con.commit()
            return User(id=cursor.lastrowid, username=username, role=role)

    def ensure_admin_user(self, username: str, password: str) -> User:
        password_hash = self._hash_password(password)
        with self._lock, self._connect() as con:
            self._ensure_role_column(con)
            existing = con.execute(
                "SELECT id, username, role FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if existing is not None:
                if existing["role"] != "admin":
                    con.execute("UPDATE users SET role = 'admin' WHERE id = ?", (existing["id"],))
                    con.commit()
                return User(id=existing["id"], username=existing["username"], role="admin")

            cursor = con.execute(
                "INSERT INTO users(username, password_hash, role) VALUES (?, ?, 'admin')",
                (username, password_hash),
            )
            con.commit()
            return User(id=cursor.lastrowid, username=username, role="admin")

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        password_hash = self._hash_password(password)
        with self._lock, self._connect() as con:
            row = con.execute(
                "SELECT id FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash),
            ).fetchone()
            if row is None:
                return None

            token = str(uuid.uuid4())
            con.execute(
                "INSERT INTO sessions(token, user_id, created_at) VALUES (?, ?, ?)",
                (token, row["id"], datetime.now(UTC).isoformat()),
            )
            con.commit()
            return token

    def get_user_by_token(self, token: str) -> Optional[User]:
        with self._lock, self._connect() as con:
            row = con.execute(
                """
                SELECT users.id, users.username, users.role
                FROM users
                JOIN sessions ON sessions.user_id = users.id
                WHERE sessions.token = ?
                """,
                (token,),
            ).fetchone()
            if row is None:
                return None
            return User(id=row["id"], username=row["username"], role=row["role"])

    def get_user_by_username(self, username: str) -> Optional[User]:
        with self._lock, self._connect() as con:
            self._ensure_role_column(con)
            row = con.execute(
                "SELECT id, username, role FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if row is None:
                return None
            return User(id=row["id"], username=row["username"], role=row["role"])

    def create_task(self, title: str, description: str, user_id: int) -> Task:
        created_at = datetime.now(UTC)
        with self._lock, self._connect() as con:
            cursor = con.execute(
                "INSERT INTO tasks(title, description, user_id, created_at) VALUES (?, ?, ?, ?)",
                (title, description, user_id, created_at.isoformat()),
            )
            row = con.execute(
                """
                SELECT tasks.id, tasks.title, tasks.description, users.username, tasks.created_at
                FROM tasks
                JOIN users ON tasks.user_id = users.id
                WHERE tasks.id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()
            con.commit()
            return Task(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                owner=row["username"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    def list_tasks(self) -> list[Task]:
        with self._lock, self._connect() as con:
            rows = con.execute(
                """
                SELECT tasks.id, tasks.title, tasks.description, users.username, tasks.created_at
                FROM tasks
                JOIN users ON tasks.user_id = users.id
                ORDER BY tasks.id DESC
                """
            ).fetchall()
        return [
            Task(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                owner=row["username"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def log_event(self, event_type: str, actor: str, result: str, details: str) -> None:
        with self._lock, self._connect() as con:
            con.execute(
                "INSERT INTO audit_logs(event_type, actor, result, details, created_at) VALUES (?, ?, ?, ?, ?)",
                (event_type, actor, result, details, datetime.now(UTC).isoformat()),
            )
            con.commit()

    def list_audit_logs(self, limit: int = 100) -> list[AuditEvent]:
        with self._lock, self._connect() as con:
            rows = con.execute(
                """
                SELECT id, event_type, actor, result, details, created_at
                FROM audit_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            AuditEvent(
                id=row["id"],
                event_type=row["event_type"],
                actor=row["actor"],
                result=row["result"],
                details=row["details"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]
