import json
import os
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    delete,
    desc,
    insert,
    select,
    update,
)
from werkzeug.security import check_password_hash, generate_password_hash

engine = None
metadata = MetaData()

users_table = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String, unique=True, nullable=False),
    Column("password_hash", String, nullable=False),
    Column("age", Integer),
    Column("gender", String),
    Column("created_at", String, nullable=False)
)

history_table = Table(
    "history", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String, nullable=False),
    Column("created_at", String, nullable=False),
    Column("payload_json", Text, nullable=False),
    Column("check_result_id", Integer)
)

check_results_table = Table(
    "check_results", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String, nullable=False),
    Column("created_at", String, nullable=False),
    Column("result_json", Text, nullable=False)
)

def init_db(database_path=None):
    global engine
    uri = os.getenv("DATABASE_URL")
    if not uri:
        db_path = database_path or "health_checker.db"
        uri = f"sqlite:///{Path(db_path).resolve()}"
    elif uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    engine = create_engine(uri)
    metadata.create_all(engine)

def normalize_email(raw_email):
    return (raw_email or "").strip().lower()

def create_user(email, password):
    with engine.begin() as conn:
        conn.execute(
            insert(users_table).values(
                email=normalize_email(email),
                password_hash=generate_password_hash(password),
                age=0,
                gender="",
                created_at=datetime.utcnow().isoformat(timespec="seconds")
            )
        )

def verify_user(email, password):
    with engine.connect() as conn:
        row = conn.execute(
            select(users_table.c.password_hash).where(users_table.c.email == normalize_email(email))
        ).mappings().fetchone()
    if not row:
        return False
    return check_password_hash(row["password_hash"], password)

def get_user_profile(email):
    with engine.connect() as conn:
        row = conn.execute(
            select(users_table.c.age, users_table.c.gender).where(users_table.c.email == normalize_email(email))
        ).mappings().fetchone()
    if row:
        return {"age": row["age"] or 0, "gender": row["gender"] or ""}
    return {"age": 0, "gender": ""}

def update_user_profile(email, age, gender):
    with engine.begin() as conn:
        conn.execute(
            update(users_table).where(users_table.c.email == normalize_email(email)).values(
                age=age, gender=gender
            )
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

def save_history_entry(email, payload, check_result_id=None):
    with engine.begin() as conn:
        result = conn.execute(
            insert(history_table).values(
                email=normalize_email(email),
                created_at=datetime.utcnow().isoformat(timespec="seconds"),
                payload_json=json.dumps(payload, ensure_ascii=False),
                check_result_id=check_result_id
            )
        )
        return result.inserted_primary_key[0]

def get_history_entries(email):
    with engine.connect() as conn:
        rows = conn.execute(
            select(history_table).where(history_table.c.email == normalize_email(email)).order_by(desc(history_table.c.id)).limit(25)
        ).mappings().fetchall()

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
    with engine.begin() as conn:
        result = conn.execute(
            delete(history_table).where((history_table.c.id == entry_id) & (history_table.c.email == normalize_email(email)))
        )
        return result.rowcount > 0

def clear_history_entries(email):
    with engine.begin() as conn:
        result = conn.execute(
            delete(history_table).where(history_table.c.email == normalize_email(email))
        )
        return result.rowcount

def save_check_result(email, result_json):
    with engine.begin() as conn:
        result = conn.execute(
            insert(check_results_table).values(
                email=normalize_email(email),
                created_at=datetime.utcnow().isoformat(timespec="seconds"),
                result_json=json.dumps(result_json, ensure_ascii=False)
            )
        )
        return result.inserted_primary_key[0]

def get_check_result(email, check_id):
    with engine.connect() as conn:
        row = conn.execute(
            select(check_results_table).where((check_results_table.c.id == check_id) & (check_results_table.c.email == normalize_email(email)))
        ).mappings().fetchone()
    if not row:
        return None
    return _decode_payload(row, "result_json")

def get_latest_check_result(email):
    with engine.connect() as conn:
        row = conn.execute(
            select(check_results_table).where(check_results_table.c.email == normalize_email(email)).order_by(desc(check_results_table.c.id)).limit(1)
        ).mappings().fetchone()
    if not row:
        return None
    return _decode_payload(row, "result_json")

def get_all_check_results(email, limit=None):
    with engine.connect() as conn:
        query = select(check_results_table).where(check_results_table.c.email == normalize_email(email)).order_by(desc(check_results_table.c.id))
        if limit is not None:
            query = query.limit(int(limit))
        rows = conn.execute(query).mappings().fetchall()

    parsed_results = []
    for row in rows:
        payload = _decode_payload(row, "result_json")
        if payload:
            parsed_results.append(payload)
    return parsed_results

def get_clinic_check_results(limit=50):
    with engine.connect() as conn:
        query = select(check_results_table).order_by(desc(check_results_table.c.id))
        if limit is not None:
            query = query.limit(int(limit))
        rows = conn.execute(query).mappings().fetchall()

    parsed_results = []
    for row in rows:
        payload = _decode_payload(row, "result_json")
        if payload:
            payload["patient_email"] = row["email"]
            payload["id"] = row["id"]
            parsed_results.append(payload)
    return parsed_results

def get_check_result_by_id(check_id):
    """Retrieve a check result by ID without email filtering (for doctor portal)."""
    with engine.connect() as conn:
        row = conn.execute(
            select(check_results_table).where(check_results_table.c.id == check_id)
        ).mappings().fetchone()
    if not row:
        return None
    payload = _decode_payload(row, "result_json")
    if payload:
        payload["patient_email"] = row["email"]
        payload["id"] = row["id"]
    return payload


def get_all_check_results(limit: int = 500) -> list[dict]:
    """
    Retrieve all check results across all patients (no email filter).
    Used for bulk research/anonymized export. Default cap: 500 records.
    """
    return get_clinic_check_results(limit=limit)
