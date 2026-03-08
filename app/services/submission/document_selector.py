"""Deterministic document selector for submission packages.

Chooses which of the 27 document types to generate based on project
context (compliance results, massing, overlays, precedents, etc.).
No AI calls — pure conditional logic.
"""

from __future__ import annotations

import structlog
from dataclasses import dataclass

logger = structlog.get_logger()

# These 14 docs are generated for every project regardless of context.
ALWAYS_GENERATE = frozenset({
    "cover_letter",
    "planning_rationale",
    "compliance_matrix",
    "site_plan_data",
    "massing_summary",
    "unit_mix_summary",
    "approval_pathway_document",
    "as_of_right_check",
    "submission_readiness_report",
    "compliance_review_report",
    "required_studies_checklist",
    "timeline_cost_estimate",
    "building_permit_readiness_checklist",
    "professional_referral_checklist",
})


@dataclass(frozen=True)
class SelectionReason:
    """Records why a conditional document was included or excluded."""

    doc_type: str
    included: bool
    reason: str


def select_documents_for_project(
    compliance_result=None,
    massing: dict | None = None,
    layout: dict | None = None,
    overlays=None,
    precedents: list | None = None,
    parsed: dict | None = None,
    financial_output: dict | None = None,
) -> tuple[list[str], list[SelectionReason]]:
    """Select which documents to generate based on project context.

    Returns:
        (doc_types, reasons) — list of doc_type strings to generate,
        and a list of SelectionReason for each conditional document.
    """
    parsed = parsed or {}
    massing = massing or {}
    precedents = precedents or []
    reasons: list[SelectionReason] = []

    selected = set(ALWAYS_GENERATE)

    # --- Helpers ---
    has_variances = (
        compliance_result is not None
        and len(compliance_result.variances_needed) > 0
    )
    overall_compliant = (
        compliance_result is not None and compliance_result.overall_compliant
    )
    minor_variance_applicable = (
        compliance_result is not None
        and compliance_result.minor_variance_applicable
    )
    has_warnings = (
        compliance_result is not None and len(compliance_result.warnings) > 0
    )
    has_overlays = overlays is not None and (
        # Pydantic model with .overlays list, or plain list
        len(getattr(overlays, "overlays", overlays) or []) > 0
    )
    has_refusal_reasons = bool(parsed.get("refusal_reasons"))
    zone_code = parsed.get("zone_code", "")
    is_r_zone = zone_code.upper().startswith("R") if zone_code else False
    height_m = massing.get("height_m", 0) or 0
    storeys = massing.get("storeys", 0) or 0

    # --- Conditional rules ---
    def _check(doc_type: str, condition: bool, reason_if_yes: str, reason_if_no: str):
        if condition:
            selected.add(doc_type)
            reasons.append(SelectionReason(doc_type, True, reason_if_yes))
        else:
            reasons.append(SelectionReason(doc_type, False, reason_if_no))

    _check(
        "financial_feasibility",
        financial_output is not None,
        "Financial analysis data available",
        "No financial analysis data",
    )

    _check(
        "precedent_report",
        len(precedents) > 0,
        f"{len(precedents)} precedent(s) found",
        "No precedents found",
    )

    _check(
        "public_benefit_statement",
        has_variances,
        "Variances required — public benefit statement supports application",
        "No variances — public benefit statement not needed",
    )

    _check(
        "shadow_study",
        height_m > 10 or storeys > 3,
        f"Height {height_m}m / {storeys} storeys exceeds shadow threshold",
        f"Height {height_m}m / {storeys} storeys below shadow threshold",
    )

    _check(
        "four_statutory_tests",
        has_variances,
        "Variances required — four tests analysis needed",
        "No variances — four tests not applicable",
    )

    _check(
        "variance_justification",
        has_variances,
        "Variances required — justification report needed",
        "No variances — justification not needed",
    )

    _check(
        "due_diligence_report",
        has_overlays or has_warnings or has_variances,
        "Overlays, warnings, or variances present — due diligence warranted",
        "No overlays, warnings, or variances — due diligence not needed",
    )

    _check(
        "olt_appeal_brief",
        has_variances and not minor_variance_applicable,
        "ZBA-level variances — OLT appeal brief may be needed",
        "No ZBA-level variances — OLT appeal brief not needed",
    )

    _check(
        "mediation_strategy",
        has_variances and not overall_compliant,
        "Non-compliant with variances — mediation strategy useful",
        "Compliant or no variances — mediation strategy not needed",
    )

    _check(
        "neighbour_support_letter",
        has_variances and is_r_zone,
        "Variances in R-zone — neighbour support letter useful",
        "No variances or not R-zone — neighbour letter not needed",
    )

    _check(
        "pac_prep_package",
        has_variances,
        "Variances required — PAC prep package needed",
        "No variances — PAC prep not needed",
    )

    _check(
        "revised_rationale",
        has_refusal_reasons,
        "Refusal reasons present — revised rationale needed",
        "No refusal reasons — revised rationale not needed",
    )

    _check(
        "correction_response",
        has_refusal_reasons,
        "Refusal reasons present — correction response needed",
        "No refusal reasons — correction response not needed",
    )

    # Log selection summary
    conditional_included = [r for r in reasons if r.included]
    conditional_excluded = [r for r in reasons if not r.included]
    logger.info(
        "document_selector.result",
        total=len(selected),
        core=len(ALWAYS_GENERATE),
        conditional_included=len(conditional_included),
        conditional_excluded=len(conditional_excluded),
    )
    for r in reasons:
        logger.debug(
            "document_selector.reason",
            doc_type=r.doc_type,
            included=r.included,
            reason=r.reason,
        )

    return sorted(selected), reasons
