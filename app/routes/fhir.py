"""
SMART on FHIR Compliance Module
=================================
Implements the SMART on FHIR (Substitutable Medical Applications and
Reusable Technologies) discovery protocol, enabling this application to
integrate with any HL7-compliant EHR system (Epic, Cerner, Meditech, etc.).

Endpoints implemented:
  GET /.well-known/smart-configuration   → OAuth2 discovery document
  GET /fhir/metadata                     → FHIR R4 CapabilityStatement
  GET /fhir/Patient/<id>                 → Patient resource (anonymized)

Reference: https://hl7.org/fhir/smart-app-launch/
           https://www.hl7.org/fhir/R4/capabilitystatement.html
"""
import json
import logging
from datetime import datetime, timezone

from flask import Blueprint, Response, request, session

from app.models.user_store import normalize_email
from app.routes.helpers import login_required
from app.services.audit_service import log_event

logger = logging.getLogger(__name__)

fhir_bp = Blueprint("fhir", __name__)


# ---------------------------------------------------------------------------
# SMART on FHIR Discovery Endpoint
# ---------------------------------------------------------------------------

@fhir_bp.route("/.well-known/smart-configuration")
def smart_configuration():
    """
    SMART on FHIR OAuth2 discovery document.

    EHR systems (Epic, Cerner, etc.) fetch this endpoint during the
    SMART App Launch flow to discover authorization capabilities.

    Conforms to: SMART App Launch Framework 2.0
    """
    base = request.host_url.rstrip("/")

    config = {
        "issuer": base,
        "jwks_uri": f"{base}/fhir/.well-known/jwks.json",
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
        "grant_types_supported": ["authorization_code", "client_credentials"],
        "registration_endpoint": f"{base}/oauth/register",
        "scopes_supported": [
            "openid",
            "fhirUser",
            "launch",
            "launch/patient",
            "patient/*.read",
            "patient/Patient.read",
            "patient/Observation.read",
            "patient/ClinicalImpression.read",
            "user/*.read",
            "offline_access",
        ],
        "response_types_supported": ["code"],
        "management_endpoint": f"{base}/fhir/user/manage",
        "introspection_endpoint": f"{base}/oauth/introspect",
        "revocation_endpoint": f"{base}/oauth/revoke",
        "capabilities": [
            "launch-ehr",
            "launch-standalone",
            "client-public",
            "client-confidential-symmetric",
            "context-passthrough-banner",
            "context-style",
            "context-ehr-patient",
            "context-standalone-patient",
            "permission-offline",
            "permission-patient",
            "permission-user",
            "sso-openid-connect",
        ],
        "code_challenge_methods_supported": ["S256"],
    }

    return Response(
        json.dumps(config, indent=2),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},   # Required for EHR iframe launch
    )


# ---------------------------------------------------------------------------
# FHIR R4 Capability Statement
# ---------------------------------------------------------------------------

@fhir_bp.route("/fhir/metadata")
def capability_statement():
    """
    FHIR R4 CapabilityStatement resource.

    Describes what FHIR resources and operations this server supports.
    Required for conformance with the FHIR standard — EHR systems query
    this before initiating any data exchange.
    """
    base = request.host_url.rstrip("/")

    statement = {
        "resourceType": "CapabilityStatement",
        "id": "health-checker-pro",
        "url": f"{base}/fhir/metadata",
        "version": "2.0.0",
        "name": "HealthCheckerProCapabilityStatement",
        "title": "Health Checker Pro — FHIR R4 Capability Statement",
        "status": "active",
        "experimental": False,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "publisher": "Health Checker Pro",
        "description": (
            "AI-powered symptom analysis platform with HistGradientBoosting ML, "
            "SHAP explainability, and SMART on FHIR interoperability."
        ),
        "kind": "instance",
        "software": {
            "name": "Health Checker Pro",
            "version": "2.0.0",
            "releaseDate": "2026-05-01",
        },
        "implementation": {
            "description": "Health Checker Pro ML Diagnostic Platform",
            "url": base,
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "security": {
                    "cors": True,
                    "service": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/restful-security-service",
                                    "code": "SMART-on-FHIR",
                                }
                            ]
                        }
                    ],
                    "description": "SMART on FHIR OAuth2 — see /.well-known/smart-configuration",
                },
                "resource": [
                    {
                        "type": "Patient",
                        "interaction": [{"code": "read"}, {"code": "search-type"}],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "identifier", "type": "token"},
                        ],
                    },
                    {
                        "type": "ClinicalImpression",
                        "interaction": [{"code": "read"}, {"code": "create"}],
                        "documentation": (
                            "Represents a completed AI symptom analysis. "
                            "Contains reported symptoms and ML-predicted conditions."
                        ),
                    },
                    {
                        "type": "Bundle",
                        "interaction": [{"code": "read"}],
                        "documentation": "FHIR document bundles containing Patient + ClinicalImpression resources.",
                    },
                ],
                "operation": [
                    {
                        "name": "export-fhir",
                        "definition": f"{base}/api/fhir/export/{{check_id}}",
                        "documentation": "Export a diagnosis check as a FHIR R4 Bundle document.",
                    },
                    {
                        "name": "export-anonymized",
                        "definition": f"{base}/api/research/export/{{check_id}}",
                        "documentation": "Export an anonymized research record (HIPAA Safe-Harbor).",
                    },
                ],
            }
        ],
    }

    return Response(
        json.dumps(statement, indent=2),
        mimetype="application/fhir+json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


# ---------------------------------------------------------------------------
# FHIR Patient Resource
# ---------------------------------------------------------------------------

@fhir_bp.route("/fhir/Patient/<patient_id>")
@login_required
def get_fhir_patient(patient_id):
    """
    Return an anonymized FHIR R4 Patient resource by hashed patient ID.

    The `patient_id` here is the ANON-XXXX hash, not a real email —
    so this endpoint is safe to expose without PHI leakage.
    """
    email = normalize_email(session.get("email"))
    log_event(email, "FHIR_PATIENT_READ", resource=f"Patient/{patient_id}")

    # Build a minimal Patient resource (no real PHI)
    patient_resource = {
        "resourceType": "Patient",
        "id": patient_id,
        "meta": {
            "versionId": "1",
            "lastUpdated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"],
        },
        "text": {
            "status": "generated",
            "div": "<div>Anonymized Patient Resource — Health Checker Pro</div>",
        },
        "identifier": [
            {
                "system": "urn:health-checker-pro:patient",
                "value": patient_id,
            }
        ],
        "active": True,
    }

    return Response(
        json.dumps(patient_resource, indent=2),
        mimetype="application/fhir+json",
    )
