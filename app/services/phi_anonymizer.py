"""
PHI Anonymization Service
==========================
Strips or masks Protected Health Information (PHI) from check results
before sharing data for research, analytics, or demo purposes.

HIPAA Safe-Harbor method (45 CFR §164.514(b)):
  - Names / emails     → removed / one-way hashed
  - Ages               → bucketed into 10-year bands (e.g. "30-39")
  - Dates              → year only (month/day stripped)
  - Record IDs         → replaced with a salted hash

The anonymized output retains full clinical value:
  - Selected symptoms
  - Condition predictions + confidence
  - Urgency levels
  - SHAP feature importances (if present)
"""
import hashlib
import logging
from copy import deepcopy
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Salt makes the hash non-reversible without the salt
_HASH_SALT = "HCP-ANON-2026"


def _hash_id(value: str) -> str:
    """One-way SHA-256 hash with salt — non-reversible pseudonym."""
    raw = f"{_HASH_SALT}:{value}".encode()
    return "ANON-" + hashlib.sha256(raw).hexdigest()[:12].upper()


def _age_bucket(age) -> str:
    """Map an exact age to a 10-year band string, e.g. 34 → '30-39'."""
    try:
        age = int(age)
        if age < 18:
            return "<18"
        low = (age // 10) * 10
        return f"{low}-{low + 9}"
    except (TypeError, ValueError):
        return "unknown"


def _year_only(iso_timestamp: str) -> str:
    """Strip month and day from ISO timestamps — keep year only."""
    try:
        return str(datetime.fromisoformat(iso_timestamp).year)
    except (TypeError, ValueError):
        return "unknown"


def anonymize_check_result(check_result: dict) -> dict:
    """
    Return a deep copy of `check_result` with all PHI fields removed or masked.

    Input:  raw check result dict from user_store (may contain email, age, gender, dates)
    Output: anonymized dict safe for research export / public sharing
    """
    result = deepcopy(check_result)

    # ── Patient block ──────────────────────────────────────────────────────────
    patient = result.get("patient", {})
    patient.pop("email", None)                          # remove email entirely
    patient.pop("name", None)                           # remove any name field
    if "age" in patient:
        patient["age_group"] = _age_bucket(patient.pop("age"))
    # gender is retained — not a direct identifier under HIPAA Safe Harbor

    result["patient"] = patient

    # ── Top-level identifiers ──────────────────────────────────────────────────
    result.pop("patient_email", None)                   # remove raw email field
    result.pop("email", None)

    # Hash the record ID (preserves referential integrity without exposing it)
    raw_id = result.get("id") or result.get("check_id")
    if raw_id is not None:
        result["anon_id"] = _hash_id(str(raw_id))
    result.pop("id", None)
    result.pop("check_id", None)

    # ── Dates — year only ─────────────────────────────────────────────────────
    for date_field in ("checked_at", "created_at"):
        if date_field in result:
            result[date_field] = _year_only(str(result[date_field]))

    # ── Clinical data is kept intact ──────────────────────────────────────────
    # selected_symptoms, condition_details, confidence, urgency, shap_values
    # are all medically relevant and contain no direct identifiers.

    # Add anonymization metadata
    result["_anonymized"] = True
    result["_method"] = "HIPAA Safe-Harbor (45 CFR §164.514(b))"
    result["_anonymized_at"] = datetime.now(timezone.utc).strftime("%Y")

    return result


def anonymize_bulk(check_results: list[dict]) -> list[dict]:
    """Anonymize a list of check results (e.g. for dataset export)."""
    return [anonymize_check_result(r) for r in check_results]
