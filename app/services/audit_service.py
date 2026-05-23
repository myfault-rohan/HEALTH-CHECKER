"""
Audit Logging Service
======================
Provides an immutable audit trail for all Protected Health Information (PHI)
access events. Follows HIPAA-awareness best practices.

Every time a user logs in, views a diagnosis, downloads a PDF, or exports
to FHIR, a record is written here. This log is append-only (no update/delete).

Logged fields:
    - email       : who performed the action
    - action      : what they did (LOGIN, VIEW_CHECK, EXPORT_PDF, EXPORT_FHIR, etc.)
    - resource    : what they accessed (e.g. "check_result:42")
    - ip_address  : client IP at time of action
    - user_agent  : browser/client identifier
    - timestamp   : UTC ISO-8601 string
"""
import logging
from datetime import datetime, timezone

from flask import request
from sqlalchemy import Column, Integer, String, Table, desc, insert, select

from app.models.user_store import metadata

logger = logging.getLogger(__name__)

# ── Audit log table definition ────────────────────────────────────────────────
# We import metadata from user_store so the table is registered in the same
# MetaData instance and gets created by user_store.init_db() → create_all().

audit_log_table = Table(
    "audit_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("timestamp", String, nullable=False),
    Column("email", String, nullable=False),
    Column("action", String, nullable=False),
    Column("resource", String, nullable=True),
    Column("ip_address", String, nullable=True),
    Column("user_agent", String, nullable=True),
    extend_existing=True,
)

# ── Action constants ───────────────────────────────────────────────────────────
class AuditAction:
    LOGIN           = "LOGIN"
    LOGOUT          = "LOGOUT"
    SIGNUP          = "SIGNUP"
    VIEW_DASHBOARD  = "VIEW_DASHBOARD"
    VIEW_CHECK      = "VIEW_CHECK"
    RUN_SYMPTOM_CHECK = "RUN_SYMPTOM_CHECK"
    EXPORT_PDF      = "EXPORT_PDF"
    EXPORT_FHIR     = "EXPORT_FHIR"
    DOCTOR_VIEW     = "DOCTOR_VIEW"
    DELETE_HISTORY  = "DELETE_HISTORY"
    CHAT_QUERY      = "CHAT_QUERY"


def log_event(email: str, action: str, resource: str = None) -> None:
    """
    Write one immutable audit event to the database.

    Safe to call from any route — errors are caught and logged but never
    bubble up to break the request flow.
    """
    import app.models.user_store as _store
    _engine = _store.engine
    if _engine is None:
        logger.warning("Audit: DB not initialised — skipping log for %s / %s", action, email)
        return

    try:
        # Grab request context values safely (works inside and outside request)
        ip = "unknown"
        ua = "unknown"
        try:
            ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
            ua = (request.headers.get("User-Agent") or "unknown")[:255]
        except RuntimeError:
            pass  # Called outside a request context

        with _engine.begin() as conn:
            conn.execute(
                insert(audit_log_table).values(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    email=email,
                    action=action,
                    resource=resource,
                    ip_address=ip,
                    user_agent=ua,
                )
            )
        logger.debug("AUDIT | %s | %s | %s", email, action, resource)

    except Exception:
        logger.exception("Failed to write audit log entry")


def get_recent_audit_events(limit: int = 100) -> list[dict]:
    """Return the most recent audit events (for admin/doctor review)."""
    import app.models.user_store as _store
    _engine = _store.engine
    if _engine is None:
        return []
    try:
        with _engine.connect() as conn:
            rows = conn.execute(
                select(audit_log_table)
                .order_by(desc(audit_log_table.c.id))
                .limit(limit)
            ).mappings().all()
        return [dict(r) for r in rows]
    except Exception:
        logger.exception("Failed to fetch audit log")
        return []
