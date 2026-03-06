import json
import sqlite3
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

DATABASE_PATH = None


def configure_database(database_path):
    global DATABASE_PATH
    DATABASE_PATH = database_path


def get_db_connection():
    if not DATABASE_PATH:
        raise RuntimeError("Database path is not configured.")
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(database_path):
    configure_database(database_path)
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        connection.commit()


def normalize_email(raw_email):
    return (raw_email or "").strip().lower()


def create_user(email, password):
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO users (email, password_hash, created_at)
            VALUES (?, ?, ?)
            """,
            (
                normalize_email(email),
                generate_password_hash(password),
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        connection.commit()


def verify_user(email, password):
    with get_db_connection() as connection:
        row = connection.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            (normalize_email(email),),
        ).fetchone()
    if not row:
        return False
    return check_password_hash(row["password_hash"], password)


def save_history_entry(email, payload):
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO history (email, created_at, payload_json)
            VALUES (?, ?, ?)
            """,
            (
                normalize_email(email),
                datetime.utcnow().isoformat(timespec="seconds"),
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        connection.commit()


def get_history_entries(email):
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, payload_json
            FROM history
            WHERE email = ?
            ORDER BY id DESC
            LIMIT 25
            """,
            (normalize_email(email),),
        ).fetchall()

    parsed_payloads = []
    for row in rows:
        try:
            payload = json.loads(row["payload_json"])
            payload["id"] = row["id"]
            if "date" not in payload:
                payload["date"] = row["created_at"]
            parsed_payloads.append(payload)
        except json.JSONDecodeError:
            continue
    return parsed_payloads


def delete_history_entry(email, entry_id):
    with get_db_connection() as connection:
        result = connection.execute(
            """
            DELETE FROM history
            WHERE id = ? AND email = ?
            """,
            (entry_id, normalize_email(email)),
        )
        connection.commit()
    return result.rowcount > 0


def clear_history_entries(email):
    with get_db_connection() as connection:
        result = connection.execute(
            """
            DELETE FROM history
            WHERE email = ?
            """,
            (normalize_email(email),),
        )
        connection.commit()
    return result.rowcount
