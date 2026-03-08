from pathlib import Path

from app.services.benchmarks import (
    TorontoCoreBenchmarkCase,
    evaluate_core_benchmark_case,
    load_toronto_core_benchmarks,
    summarize_benchmark_results,
)


def test_load_toronto_core_benchmarks_has_broader_toronto_candidate_set():
    path = Path(__file__).parent / "fixtures" / "benchmarks" / "toronto_core.json"
    cases = load_toronto_core_benchmarks(path)

    assert len(cases) >= 15
    assert all(case.verification_status == "template" for case in cases)
    assert all(case.address_input.endswith(", Toronto, ON") for case in cases)
    assert len({case.address_input for case in cases}) == len(cases)
    assert all(case.expected_parcel and case.expected_parcel.get("address") for case in cases)
    assert all(
        case.expected_policy_stack and case.expected_policy_stack.required_documents == ["Zoning By-law 569-2013"]
        for case in cases
    )
    benchmark_ids = {case.benchmark_id for case in cases}
    assert any(benchmark_id.startswith("toronto-lowrise-") for benchmark_id in benchmark_ids)
    assert any(benchmark_id.startswith("toronto-apartment-") for benchmark_id in benchmark_ids)
    assert any(benchmark_id.startswith("toronto-corridor-") for benchmark_id in benchmark_ids)
    assert any(benchmark_id.startswith("toronto-employment-") for benchmark_id in benchmark_ids)


def test_load_toronto_phase2_benchmarks_has_verified_address_cases():
    path = Path(__file__).parent / "fixtures" / "benchmarks" / "toronto_phase2.json"
    cases = load_toronto_core_benchmarks(path)

    assert len(cases) == 15
    assert all(case.verification_status == "verified" for case in cases)
    assert all(case.expected_parcel == {"address": case.address_input.replace(", Toronto, ON", "")} for case in cases)


def test_load_toronto_showcase_benchmarks_covers_prominent_addresses():
    path = Path(__file__).parent / "fixtures" / "benchmarks" / "toronto_showcase.json"
    cases = load_toronto_core_benchmarks(path)

    assert len(cases) == 5
    assert all(case.verification_status == "template" for case in cases)
    assert [case.address_input for case in cases] == [
        "40 King St W, Toronto, ON",
        "66 Wellington St W, Toronto, ON",
        "100 Queen St W, Toronto, ON",
        "200 Adelaide St W, Toronto, ON",
        "905 Bay St, Toronto, ON",
    ]
    assert all(
        case.expected_policy_stack and case.expected_policy_stack.required_documents == ["Zoning By-law 569-2013"]
        for case in cases
    )


def test_evaluate_verified_benchmark_case():
    case = TorontoCoreBenchmarkCase.model_validate(
        {
            "benchmark_id": "verified-case",
            "verification_status": "verified",
            "source_notes": "Synthetic verified case used to test benchmark scoring logic.",
            "address_input": "100 Queen St W, Toronto, ON",
            "expected_parcel": {"address": "100 Queen St W, Toronto, ON"},
            "expected_zoning": {"zone_code": "CR 3.0", "category": "CR"},
            "expected_policy_stack": {
                "required_documents": ["Zoning By-law 569-2013"],
                "required_sections": ["40.10.40.10"],
            },
            "expected_scenario": {
                "scenario_type": "base",
                "expected_constraints": ["max_height"],
                "expected_metrics": {"max_height_m": 36.0},
            },
        }
    )

    actual = {
        "parcel": {"address": "100 Queen St W, Toronto, ON"},
        "zoning": {"zone_code": "CR 3.0", "category": "CR"},
        "policy_stack": {
            "documents": ["Zoning By-law 569-2013"],
            "sections": ["40.10.40.10"],
        },
        "scenario": {
            "scenario_type": "base",
            "constraints": ["max_height"],
            "metrics": {"max_height_m": 36.0},
        },
    }

    result = evaluate_core_benchmark_case(case, actual)

    assert result.status == "passed"
    assert result.failures == []
    assert result.total_checks == 8


def test_benchmark_summary_ignores_template_cases():
    verified_case = TorontoCoreBenchmarkCase.model_validate(
        {
            "benchmark_id": "verified-case",
            "verification_status": "verified",
            "source_notes": "Synthetic verified case used to test suite summary logic.",
            "address_input": "100 Queen St W, Toronto, ON",
            "expected_parcel": {"address": "100 Queen St W, Toronto, ON"},
        }
    )

    passed = evaluate_core_benchmark_case(
        verified_case,
        {"parcel": {"address": "100 Queen St W, Toronto, ON"}},
    )
    skipped = evaluate_core_benchmark_case(
        TorontoCoreBenchmarkCase.model_validate(
            {
                "benchmark_id": "template-case",
                "verification_status": "template",
                "source_notes": "Pending manual verification.",
                "address_input": "111 Richmond St W, Toronto, ON",
            }
        ),
        {},
    )

    summary = summarize_benchmark_results([passed, skipped])

    assert summary["case_count"] == 1
    assert summary["skipped_case_count"] == 1
    assert summary["pass_rate"] == 1.0
