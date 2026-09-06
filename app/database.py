"""SQLite persistence for jobs and tracked applications."""

import sqlite3
import hashlib
import hmac
import secrets
from pathlib import Path

DB_PATH = Path("data/recruitment.db")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with connect() as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT DEFAULT '',
            description TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Saved',
            applied_at TEXT,
            notes TEXT DEFAULT '',
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    salt_hex, digest_hex = stored_hash.split("$", 1)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 120_000)
    return hmac.compare_digest(candidate.hex(), digest_hex)


def create_user(name: str, email: str, password: str) -> dict:
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO users(name, email, password_hash) VALUES (?, ?, ?)",
            (name.strip(), email.strip().lower(), _hash_password(password)),
        )
        row = connection.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return dict(row)


def authenticate_user(email: str, password: str) -> dict | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
    if not row or not _verify_password(password, row["password_hash"]):
        return None
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def list_jobs() -> list[dict]:
    with connect() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM jobs ORDER BY id DESC")]


def add_job(title: str, company: str, location: str, description: str) -> dict:
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO jobs(title, company, location, description) VALUES (?, ?, ?, ?)",
            (title, company, location, description),
        )
        row = connection.execute("SELECT * FROM jobs WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)


def add_application(job_id: int, status: str = "Saved", notes: str = "") -> dict:
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO applications(job_id, status, notes) VALUES (?, ?, ?)",
            (job_id, status, notes),
        )
        row = connection.execute("SELECT * FROM applications WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)


def list_applications() -> list[dict]:
    with connect() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT applications.*, jobs.title, jobs.company FROM applications "
            "JOIN jobs ON jobs.id = applications.job_id ORDER BY applications.id DESC"
        )]
