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


def _ensure_column(connection, table_name, column_name, column_sql):
    columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    existing = {column["name"] for column in columns}
    if column_name not in existing:
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"
        )


def _decode_payload(row, payload_key):
    try:
        payload = json.loads(row[payload_key])
    except (TypeError, json.JSONDecodeError):
        return None

    payload["id"] = row["id"]
    if "created_at" not in payload:
        payload["created_at"] = row["created_at"]
    return payload


def init_db(database_path):
    configure_database(database_path)
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS check_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
            """
        )
        _ensure_column(connection, "history", "check_result_id", "INTEGER")
        connection.commit()


def normalize_email(raw_email):
    return (raw_email or "").strip().lower()


def create_user(email, password):
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO users (email, password_hash, age, gender, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                normalize_email(email),
                generate_password_hash(password),
                0,
                "",
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


def get_user_profile(email):
    with get_db_connection() as connection:
        row = connection.execute(
            "SELECT age, gender FROM users WHERE email = ?",
            (normalize_email(email),),
        ).fetchone()
    if row:
        return {"age": row["age"] or 0, "gender": row["gender"] or ""}
    return {"age": 0, "gender": ""}


def update_user_profile(email, age, gender):
    with get_db_connection() as connection:
        connection.execute(
            "UPDATE users SET age = ?, gender = ? WHERE email = ?",
            (age, gender, normalize_email(email)),
        )
        connection.commit()


def save_history_entry(email, payload, check_result_id=None):
    with get_db_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO history (email, created_at, payload_json, check_result_id)
            VALUES (?, ?, ?, ?)
            """,
            (
                normalize_email(email),
                datetime.utcnow().isoformat(timespec="seconds"),
                json.dumps(payload, ensure_ascii=False),
                check_result_id,
            ),
        )
        connection.commit()
    return cursor.lastrowid


def get_history_entries(email):
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, payload_json, check_result_id
            FROM history
            WHERE email = ?
            ORDER BY id DESC
            LIMIT 25
            """,
            (normalize_email(email),),
        ).fetchall()

    parsed_payloads = []
    for row in rows:
        payload = _decode_payload(row, "payload_json")
        if not payload:
            continue
        payload["check_result_id"] = row["check_result_id"]
        if "date" not in payload:
            payload["date"] = row["created_at"]
        parsed_payloads.append(payload)
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


def save_check_result(email, result_json):
    with get_db_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO check_results (email, created_at, result_json)
            VALUES (?, ?, ?)
            """,
            (
                normalize_email(email),
                datetime.utcnow().isoformat(timespec="seconds"),
                json.dumps(result_json, ensure_ascii=False),
            ),
        )
        connection.commit()
    return cursor.lastrowid


def get_check_result(email, check_id):
    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT id, created_at, result_json
            FROM check_results
            WHERE id = ? AND email = ?
            """,
            (check_id, normalize_email(email)),
        ).fetchone()
    if not row:
        return None
    return _decode_payload(row, "result_json")


def get_latest_check_result(email):
    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT id, created_at, result_json
            FROM check_results
            WHERE email = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (normalize_email(email),),
        ).fetchone()
    if not row:
        return None
    return _decode_payload(row, "result_json")


def get_all_check_results(email, limit=None):
    limit_sql = ""
    params = [normalize_email(email)]
    if limit is not None:
        limit_sql = "LIMIT ?"
        params.append(int(limit))

    with get_db_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, created_at, result_json
            FROM check_results
            WHERE email = ?
            ORDER BY id DESC
            {limit_sql}
            """,
            tuple(params),
        ).fetchall()

    parsed_results = []
    for row in rows:
        payload = _decode_payload(row, "result_json")
        if payload:
            parsed_results.append(payload)
    return parsed_results
