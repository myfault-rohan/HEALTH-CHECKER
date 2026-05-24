"""Report routes: PDF download and FHIR JSON export."""

import io
import json
import logging
from datetime import datetime, timezone
from xml.sax.saxutils import escape as xml_escape

from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    session,
    url_for,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.user_store import (
    get_all_check_results,
    get_check_result,
    get_check_result_by_id,
    get_user_profile,
    normalize_email,
)
from app.routes.helpers import (
    doctor_required,
    format_datetime_label,
    format_gender,
    is_doctor,
    login_required,
    strip_icon_prefix,
)
from app.services.audit_service import AuditAction, log_event
from app.services.phi_anonymizer import anonymize_bulk, anonymize_check_result
from app.services.prediction_service import ordered_unique

logger = logging.getLogger(__name__)

reports_bp = Blueprint("reports", __name__)


# ---------------------------------------------------------------------------
# PDF generation helper
# ---------------------------------------------------------------------------

def build_pdf_report(check_result):
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f5ea8"),
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportBody",
            parent=styles["BodyText"],
            fontSize=10.5,
            leading=14,
            spaceAfter=6,
        )
    )

    patient = check_result.get("patient", {})
    condition_details = check_result.get("condition_details", [])[:3]
    treatment_points = ordered_unique(
        (check_result.get("remedies") or [])
        + (check_result.get("lifestyle_suggestions") or [])
    )[:8]

    elements = [
        Paragraph(
            "Health Checker Pro - Symptom Analysis Report",
            styles["ReportTitle"],
        ),
        Paragraph(
            f"Patient: Age {xml_escape(str(patient.get('age', 'N/A')))} | Gender {xml_escape(str(format_gender(patient.get('gender'))))}",
            styles["ReportBody"],
        ),
        Paragraph(
            f"Date & Time: {xml_escape(str(format_datetime_label(check_result.get('checked_at'))))}",
            styles["ReportBody"],
        ),
        Spacer(1, 8),
        Paragraph("Symptoms Selected", styles["Heading3"]),
        ListFlowable(
            [
                ListItem(Paragraph(symptom.title(), styles["ReportBody"]))
                for symptom in check_result.get("selected_symptoms", [])
            ],
            bulletType="bullet",
        ),
        Spacer(1, 10),
        Paragraph("Top Condition Matches", styles["Heading3"]),
    ]

    table_data = [["Condition", "Confidence", "Urgency"]]
    for condition in condition_details:
        table_data.append(
            [
                condition.get("name", "Unknown"),
                f"{condition.get('confidence', 0)}%",
                condition.get("urgency", "low").capitalize(),
            ]
        )
    if len(table_data) == 1:
        table_data.append(["No clear match", "-", "-"])

    table = Table(table_data, colWidths=[240, 100, 100])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f5ea8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d5dfeb")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.whitesmoke, colors.HexColor("#edf4fb")],
                ),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.extend(
        [
            table,
            Spacer(1, 12),
            Paragraph("Treatment & Precautions", styles["Heading3"]),
            ListFlowable(
                [
                    ListItem(
                        Paragraph(strip_icon_prefix(item), styles["ReportBody"])
                    )
                    for item in treatment_points
                ]
                or [
                    ListItem(
                        Paragraph("No treatment guidance saved.", styles["ReportBody"])
                    )
                ],
                bulletType="bullet",
            ),
            Spacer(1, 12),
            Paragraph(
                "This is not a medical diagnosis. Consult a licensed physician.",
                styles["Italic"],
            ),
        ]
    )

    document.build(elements)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@reports_bp.route("/report/<int:check_id>/pdf")
@login_required
def download_report(check_id):
    email = normalize_email(session.get("email"))
    check_result = get_check_result(email, check_id) if email else None
    if not check_result:
        if is_doctor(email):
            check_result = get_check_result_by_id(check_id)
    if not check_result:
        flash("Report not found or access denied.", "danger")
        return redirect(url_for("checker.conditions"))

    pdf_buffer = build_pdf_report(check_result)
    log_event(email, AuditAction.EXPORT_PDF, resource=f"check_result:{check_id}")
    filename = f"health-check-report-{check_id}.pdf"
    return Response(
        pdf_buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@reports_bp.route("/api/fhir/export/<int:check_id>")
@login_required
def export_fhir(check_id):
    email = normalize_email(session.get("email"))

    # Try own record first, then fall back to cross-patient (doctor portal)
    check_result = get_check_result(email, check_id)
    patient_email = email
    if not check_result:
        if is_doctor(email):
            check_result = get_check_result_by_id(check_id)
            if check_result:
                patient_email = check_result.get("patient_email", "unknown")
        else:
            flash("Access denied. Clinician authorization required.", "danger")
            return redirect(url_for("dashboard.dashboard"))

    if not check_result:
        flash("Check result not found.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    log_event(email, AuditAction.EXPORT_FHIR, resource=f"check_result:{check_id}")
    patient = get_user_profile(patient_email)

    fhir_bundle = {
        "resourceType": "Bundle",
        "type": "document",
        "timestamp": check_result.get("checked_at", datetime.now(timezone.utc).isoformat()),
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": f"PAT-{patient_email.split('@')[0]}",
                    "gender": patient.get("gender", "unknown"),
                    "birthDate": str(datetime.now(timezone.utc).year - int(patient.get("age", 0))) if patient.get("age") else "unknown"
                }
            },
            {
                "resource": {
                    "resourceType": "ClinicalImpression",
                    "id": f"IMP-{check_id}",
                    "status": "completed",
                    "description": "AI Symptom Checker Analysis",
                    "investigation": [
                        {
                            "code": {"text": "Reported Symptoms"},
                            "item": [{"display": sym} for sym in check_result.get("selected_symptoms", [])]
                        }
                    ],
                    "finding": [
                        {
                            "itemCodeableConcept": {
                                "text": condition.get("name", "Unknown")
                            },
                            "basis": f"Confidence: {condition.get('confidence', 0)}%"
                        } for condition in check_result.get("condition_details", [])
                    ]
                }
            }
        ]
    }

    return Response(
        json.dumps(fhir_bundle, indent=2),
        mimetype="application/fhir+json",
        headers={"Content-Disposition": f"attachment;filename=FHIR_Report_{check_id}.json"}
    )


# ---------------------------------------------------------------------------
# PHI Anonymization endpoints (research / public data exports)
# ---------------------------------------------------------------------------

@reports_bp.route("/api/research/export/<int:check_id>")
@login_required
def export_anonymized(check_id):
    """Export a single check result with all PHI stripped (HIPAA Safe-Harbor)."""
    email = normalize_email(session.get("email"))

    check_result = get_check_result(email, check_id)
    if not check_result:
        if is_doctor(email):
            check_result = get_check_result_by_id(check_id)
        else:
            return Response(json.dumps({"error": "Forbidden - Clinician access required"}), status=403, mimetype="application/json")
    if not check_result:
        return Response(json.dumps({"error": "Not found"}), status=404, mimetype="application/json")

    log_event(email, "EXPORT_ANONYMIZED", resource=f"check_result:{check_id}")
    anon = anonymize_check_result(check_result)

    return Response(
        json.dumps(anon, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename=research_export_{anon.get('anon_id', check_id)}.json"}
    )


@reports_bp.route("/api/research/export/bulk")
@doctor_required
def export_bulk_anonymized():
    """
    Export ALL patient check records with PHI stripped.
    Doctor-only endpoint — for research datasets and analytics.
    """
    email = normalize_email(session.get("email"))
    log_event(email, "EXPORT_BULK_ANONYMIZED", resource="all_check_results")

    all_results = get_all_check_results()
    anonymized = anonymize_bulk(all_results)

    return Response(
        json.dumps({"count": len(anonymized), "records": anonymized}, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=research_dataset_anonymized.json"}
    )
