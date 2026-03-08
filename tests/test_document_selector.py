"""Tests for deterministic document selector."""

from app.services.compliance_engine import ComplianceResult, ComplianceRule
from app.services.submission.document_selector import (
    ALWAYS_GENERATE,
    select_documents_for_project,
)


def _make_variance(parameter="Height", pct=10.0):
    return ComplianceRule(
        parameter=parameter,
        bylaw_section="569-2013 §10.20",
        permitted_value=10.0,
        proposed_value=11.0,
        unit="m",
        compliant=False,
        variance_required=True,
        variance_pct=pct,
    )


def test_as_of_right_project():
    """As-of-right project: only core + financial + precedent, no variance docs."""
    compliance = ComplianceResult(
        rules=[], overall_compliant=True, variances_needed=[], warnings=[]
    )
    docs, reasons = select_documents_for_project(
        compliance_result=compliance,
        massing={"height_m": 8, "storeys": 2},
        financial_output={"noi": 100000},
        precedents=[{"id": 1}],
        parsed={"zone_code": "R"},
    )
    assert "cover_letter" in docs
    assert "financial_feasibility" in docs
    assert "precedent_report" in docs
    # No variance-related docs
    assert "four_statutory_tests" not in docs
    assert "variance_justification" not in docs
    assert "olt_appeal_brief" not in docs
    assert "neighbour_support_letter" not in docs
    assert "pac_prep_package" not in docs
    assert "shadow_study" not in docs  # height <= 10m
    expected_count = len(ALWAYS_GENERATE) + 2  # +financial +precedent
    assert len(docs) == expected_count, f"Expected {expected_count}, got {len(docs)}: {docs}"


def test_minor_variance_r_zone():
    """Variances in R-zone: adds variance docs + neighbour letter, no OLT brief."""
    v = _make_variance(pct=8.0)
    compliance = ComplianceResult(
        rules=[v],
        overall_compliant=False,
        variances_needed=[v],
        minor_variance_applicable=True,
        warnings=["test warning"],
    )
    docs, reasons = select_documents_for_project(
        compliance_result=compliance,
        massing={"height_m": 9, "storeys": 3},
        precedents=[{"id": 1}],
        parsed={"zone_code": "RD"},
    )
    assert "four_statutory_tests" in docs
    assert "variance_justification" in docs
    assert "public_benefit_statement" in docs
    assert "pac_prep_package" in docs
    assert "neighbour_support_letter" in docs
    assert "due_diligence_report" in docs
    assert "mediation_strategy" in docs
    # Minor variance — no OLT brief
    assert "olt_appeal_brief" not in docs
    # No financial
    assert "financial_feasibility" not in docs


def test_zba_level_variances():
    """ZBA-level variances: includes OLT appeal brief."""
    v = _make_variance(pct=35.0)
    compliance = ComplianceResult(
        rules=[v],
        overall_compliant=False,
        variances_needed=[v],
        minor_variance_applicable=False,
        warnings=["ZBA may be required"],
    )
    docs, reasons = select_documents_for_project(
        compliance_result=compliance,
        massing={"height_m": 20, "storeys": 5},
        parsed={"zone_code": "CR"},
    )
    assert "olt_appeal_brief" in docs
    assert "shadow_study" in docs  # height > 10m


def test_refusal_reasons():
    """Refusal reasons in parsed params: adds revised_rationale + correction_response."""
    compliance = ComplianceResult(
        rules=[], overall_compliant=True, variances_needed=[], warnings=[]
    )
    docs, reasons = select_documents_for_project(
        compliance_result=compliance,
        massing={"height_m": 8, "storeys": 2},
        parsed={"refusal_reasons": ["insufficient setback justification"]},
    )
    assert "revised_rationale" in docs
    assert "correction_response" in docs


def test_tall_building_gets_shadow_study():
    """Buildings > 10m or > 3 storeys get shadow study."""
    compliance = ComplianceResult(
        rules=[], overall_compliant=True, variances_needed=[], warnings=[]
    )
    docs, _ = select_documents_for_project(
        compliance_result=compliance,
        massing={"height_m": 15, "storeys": 4},
    )
    assert "shadow_study" in docs


def test_short_building_no_shadow_study():
    """Buildings <= 10m and <= 3 storeys skip shadow study."""
    compliance = ComplianceResult(
        rules=[], overall_compliant=True, variances_needed=[], warnings=[]
    )
    docs, _ = select_documents_for_project(
        compliance_result=compliance,
        massing={"height_m": 9, "storeys": 3},
    )
    assert "shadow_study" not in docs


def test_explicit_subset_unchanged():
    """When generate_subset is provided, the selector isn't used (tested at task level).

    This just verifies ALWAYS_GENERATE has exactly 14 entries.
    """
    assert len(ALWAYS_GENERATE) == 14


def test_selection_reasons_cover_all_conditional():
    """Every conditional doc gets a SelectionReason entry."""
    compliance = ComplianceResult(
        rules=[], overall_compliant=True, variances_needed=[], warnings=[]
    )
    _, reasons = select_documents_for_project(compliance_result=compliance)
    reason_types = {r.doc_type for r in reasons}
    expected_conditional = {
        "financial_feasibility", "precedent_report", "public_benefit_statement",
        "shadow_study", "four_statutory_tests", "variance_justification",
        "due_diligence_report", "olt_appeal_brief", "mediation_strategy",
        "neighbour_support_letter", "pac_prep_package", "revised_rationale",
        "correction_response",
    }
    assert reason_types == expected_conditional


def test_no_compliance_result():
    """Gracefully handles None compliance_result."""
    docs, reasons = select_documents_for_project(
        compliance_result=None,
        massing={"height_m": 5, "storeys": 2},
        financial_output={"noi": 50000},
    )
    assert "financial_feasibility" in docs
    # No variance docs since compliance is None
    assert "four_statutory_tests" not in docs
    assert "olt_appeal_brief" not in docs
