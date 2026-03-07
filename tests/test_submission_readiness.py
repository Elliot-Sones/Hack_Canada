import uuid

from app.models.plan import DevelopmentPlan, SubmissionDocument
from app.services.submission.readiness import (
    NOT_AVAILABLE_MARKER,
    document_has_unresolved_placeholders,
    evaluate_submission_readiness,
)


def _make_plan() -> DevelopmentPlan:
    plan = DevelopmentPlan(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        created_by=uuid.uuid4(),
        original_query="Build a mixed-use midrise at 123 King Street West",
        parsed_parameters={
            "address": "123 King Street West",
            "project_name": "King West Midrise",
            "development_type": "mixed_use",
            "building_type": "midrise",
        },
        parse_confidence=0.92,
    )
    plan.summary = {
        "parcel_found": True,
        "zoning_resolved": True,
        "massing": {"storeys": 8},
        "layout": {"total_units": 60},
        "finance": {"total_revenue": 1_000_000},
        "compliance": {"overall_compliant": True, "variances_needed": 0},
        "precedents_found": 2,
    }
    return plan


def _make_doc(
    doc_type: str,
    title: str,
    *,
    review_status: str = "approved",
    content_text: str = "ready",
) -> SubmissionDocument:
    return SubmissionDocument(
        id=uuid.uuid4(),
        plan_id=uuid.uuid4(),
        doc_type=doc_type,
        title=title,
        format="markdown",
        status="completed",
        review_status=review_status,
        content_text=content_text,
    )


def test_document_has_unresolved_placeholders():
    assert document_has_unresolved_placeholders(f"Value pending {NOT_AVAILABLE_MARKER}")
    assert not document_has_unresolved_placeholders("Complete document")


def test_evaluate_submission_readiness_flags_blockers_and_review_items():
    plan = _make_plan()
    plan.parsed_parameters.pop("project_name")
    docs = [
        _make_doc("cover_letter", "Cover Letter", content_text=f"{NOT_AVAILABLE_MARKER}"),
        _make_doc("planning_rationale", "Planning Rationale", review_status="under_review"),
    ]

    readiness = evaluate_submission_readiness(plan, docs)

    assert readiness["ready_for_submission"] is False
    assert any(issue["code"] == "missing_project_name" for issue in readiness["blocking_issues"])
    assert any(issue["code"] == "placeholder_document_cover_letter" for issue in readiness["blocking_issues"])
    assert any(issue["code"] == "unapproved_document_planning_rationale" for issue in readiness["review_issues"])


def test_evaluate_submission_readiness_marks_complete_package_ready():
    plan = _make_plan()
    docs = [
        _make_doc("cover_letter", "Cover Letter"),
        _make_doc("planning_rationale", "Planning Rationale"),
        _make_doc("compliance_matrix", "Compliance Matrix"),
        _make_doc("site_plan_data", "Site Plan Data Summary"),
        _make_doc("massing_summary", "Massing & Built Form Summary"),
        _make_doc("unit_mix_summary", "Unit Mix & Layout Summary"),
        _make_doc("financial_feasibility", "Financial Feasibility Summary"),
    ]

    readiness = evaluate_submission_readiness(plan, docs)

    assert readiness["ready_for_submission"] is True
    assert readiness["blocking_issues"] == []
    assert readiness["review_issues"] == []
