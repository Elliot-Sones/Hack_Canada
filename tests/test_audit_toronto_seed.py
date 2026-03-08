import json
import uuid
from pathlib import Path
from types import SimpleNamespace

import scripts.audit_toronto_seed as audit


class FakeOverlay:
    def __init__(self, layer_type: str, layer_name: str = "Test Layer") -> None:
        self.layer_type = layer_type
        self.layer_name = layer_name

    def model_dump(self) -> dict:
        return {
            "layer_type": self.layer_type,
            "layer_name": self.layer_name,
        }


def test_build_benchmark_actual_payload_includes_sorted_unique_fields():
    parcel = SimpleNamespace(address="258 John St", pin="P-100", zone_code="CR 3.0")
    zoning_analysis = SimpleNamespace(
        zone_string="CR 3.0",
        components=SimpleNamespace(category="CR"),
        standards=SimpleNamespace(max_height_m=36.0, max_storeys=12, max_fsi=3.0),
        warnings=["Needs review"],
    )
    overlay_response = SimpleNamespace(
        overlays=[
            SimpleNamespace(layer_type="height_overlay"),
            SimpleNamespace(layer_type="height_overlay"),
            SimpleNamespace(layer_type="setback_overlay"),
        ]
    )
    policy_stack = SimpleNamespace(
        applicable_policies=[
            SimpleNamespace(document_title="Official Plan", section_ref="2.2.1"),
            SimpleNamespace(document_title="Zoning By-law 569-2013", section_ref="40.10.40.10"),
            SimpleNamespace(document_title="Zoning By-law 569-2013", section_ref="40.10.40.10"),
        ]
    )

    actual = audit.build_benchmark_actual_payload(parcel, zoning_analysis, overlay_response, policy_stack)

    assert actual["parcel"] == {"address": "258 John St", "pin": "P-100"}
    assert actual["zoning"]["category"] == "CR"
    assert actual["zoning"]["overlay_layers"] == ["height_overlay", "setback_overlay"]
    assert actual["zoning"]["warnings"] == ["Needs review"]
    assert actual["policy_stack"]["documents"] == ["Official Plan", "Zoning By-law 569-2013"]
    assert actual["policy_stack"]["sections"] == ["2.2.1", "40.10.40.10"]


def test_run_benchmark_suite_summarizes_candidate_resolution(tmp_path: Path, monkeypatch):
    fixture_path = tmp_path / "toronto_core.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "benchmark_id": "verified-case",
                    "verification_status": "verified",
                    "source_notes": "Verified synthetic case for audit harness testing.",
                    "address_input": "100 Queen St W, Toronto, ON",
                    "expected_parcel": {"address": "100 Queen St W"},
                    "expected_zoning": {"zone_code": "CR 3.0", "category": "CR"},
                    "expected_policy_stack": {
                        "required_documents": ["Zoning By-law 569-2013"],
                        "required_sections": ["40.10.40.10"],
                    },
                },
                {
                    "benchmark_id": "template-case",
                    "verification_status": "template",
                    "source_notes": "Template candidate that does not resolve during the test.",
                    "address_input": "5000 Jane St, Toronto, ON",
                    "expected_parcel": {"address": "5000 Jane St"},
                },
            ]
        )
    )

    parcel = SimpleNamespace(id=uuid.uuid4(), address="100 Queen St W", pin="P-100", zone_code="CR 3.0")

    monkeypatch.setattr(
        audit,
        "list_active_snapshot_ids_sync",
        lambda db, snapshot_type, jurisdiction_id=None: [uuid.uuid4()],
    )
    monkeypatch.setattr(audit, "_get_active_zoning_assignment_count", lambda db, parcel_id, snapshot_ids: 2)
    monkeypatch.setattr(
        audit,
        "resolve_active_parcel_by_address_sync",
        lambda db, address, jurisdiction_id=None, active_snapshot_ids=None: parcel
        if address == "100 Queen St W, Toronto, ON"
        else None,
    )
    monkeypatch.setattr(
        audit,
        "get_parcel_overlays_response_sync",
        lambda db, resolved_parcel: SimpleNamespace(overlays=[FakeOverlay("height_overlay")]),
    )
    monkeypatch.setattr(
        audit,
        "build_zoning_analysis",
        lambda resolved_parcel, parking_policy_area="PA3", overlay_data=None, zoning_assignment_count=None: SimpleNamespace(
            zone_string=resolved_parcel.zone_code,
            components=SimpleNamespace(category="CR"),
            standards=SimpleNamespace(max_height_m=36.0, max_storeys=12, max_fsi=3.0),
            warnings=["Parcel frontage/depth data is missing"],
        ),
    )
    monkeypatch.setattr(
        audit,
        "get_policy_stack_response_sync",
        lambda db, resolved_parcel: SimpleNamespace(
            applicable_policies=[
                SimpleNamespace(document_title="Zoning By-law 569-2013", section_ref="40.10.40.10")
            ]
        ),
    )

    summary = audit.run_benchmark_suite(object(), uuid.uuid4(), fixture_path)

    assert summary["verified_summary"]["case_count"] == 1
    assert summary["verified_summary"]["skipped_case_count"] == 1
    assert summary["verified_summary"]["pass_rate"] == 1.0
    assert summary["candidate_summary"]["fixture_case_count"] == 2
    assert summary["candidate_summary"]["resolved_parcel_count"] == 1
    assert summary["candidate_summary"]["cases_with_zone_code"] == 1
    assert summary["candidate_summary"]["cases_with_policy_documents"] == 1
    assert summary["candidate_summary"]["cases_with_overlays"] == 1
    assert summary["candidate_summary"]["cases_with_warnings"] == 1
    assert summary["candidate_summary"]["unresolved_benchmark_ids"] == ["template-case"]
    assert summary["results"][0]["status"] == "passed"
    assert summary["results"][0]["zone_category"] == "CR"
    assert summary["results"][0]["warning_count"] == 1
    assert summary["results"][1]["resolved"] is False


def test_render_text_report_contains_key_sections():
    report = {
        "jurisdiction": {"name": "Toronto", "province": "ON", "country": "CA"},
        "row_counts": {"parcels": 10, "policy_documents": 2},
        "coverage": {
            "parcels": {
                "active_parcel_count": 10,
                "with_address_rate_pct": 90.0,
                "with_zone_code_rate_pct": 80.0,
                "with_lot_area_rate_pct": 70.0,
                "with_lot_frontage_rate_pct": 60.0,
                "with_lot_depth_rate_pct": 50.0,
                "with_current_use_rate_pct": 40.0,
            },
            "zoning": {
                "assigned_parcel_count": 8,
                "multi_zone_parcel_count": 2,
                "multi_zone_parcel_rate_pct": 25.0,
            },
            "development_applications": {
                "count": 5,
                "with_geom_rate_pct": 80.0,
                "linked_to_parcel_rate_pct": 60.0,
                "with_decision_rate_pct": 40.0,
            },
            "policies": {
                "active_version_count": 2,
                "clause_count": 4,
                "rules_with_zone_filter": 3,
                "rules_with_geometry_filter": 1,
            },
        },
        "benchmarks": {
            "verified_summary": {
                "case_count": 1,
                "skipped_case_count": 1,
                "pass_rate": 1.0,
                "check_pass_rate": 1.0,
            },
            "candidate_summary": {
                "resolved_parcel_count": 1,
                "fixture_case_count": 2,
                "resolved_parcel_rate_pct": 50.0,
                "cases_with_zone_code": 1,
                "cases_with_policy_documents": 1,
                "cases_with_overlays": 1,
                "unresolved_benchmark_ids": ["template-case"],
            },
            "results": [
                {
                    "benchmark_id": "verified-case",
                    "verification_status": "verified",
                    "resolved": True,
                    "status": "passed",
                    "zone_code": "CR 3.0",
                    "policy_document_count": 1,
                    "overlay_count": 1,
                    "warning_count": 1,
                    "error": None,
                }
            ],
        },
    }

    rendered = audit.render_text_report(report)

    assert "Toronto Seed Audit" in rendered
    assert "Row counts:" in rendered
    assert "Coverage:" in rendered
    assert "Benchmarks:" in rendered
    assert "verified-case [verified]" in rendered
    assert "unresolved benchmark ids: template-case" in rendered
