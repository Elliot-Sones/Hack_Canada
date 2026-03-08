from app.data.toronto_policy_seed import CURATED_TORONTO_POLICY_DOCUMENTS
from scripts.seed_policies import _document_file_hash


def test_curated_policy_seed_has_real_source_backed_documents():
    assert len(CURATED_TORONTO_POLICY_DOCUMENTS) == 5
    assert all(document["source_url"].startswith("https://www.toronto.ca/") for document in CURATED_TORONTO_POLICY_DOCUMENTS)


def test_curated_policy_seed_uses_real_applicability_filters_and_non_uniform_confidence():
    clauses = [clause for document in CURATED_TORONTO_POLICY_DOCUMENTS for clause in document["clauses"]]
    rules = [rule for clause in clauses for rule in clause["applicability"]]
    confidences = {clause["confidence"] for clause in clauses}

    assert len(clauses) == 15
    assert len(rules) == 15
    assert len(confidences) > 1
    assert any(clause["needs_review"] for clause in clauses)
    assert all(rule.get("zone_filter") for rule in rules)
    assert {rule["override_level"] for rule in rules} == {1, 2, 3, 4, 5}


def test_curated_policy_file_hash_is_deterministic():
    document = CURATED_TORONTO_POLICY_DOCUMENTS[0]

    assert _document_file_hash(document) == _document_file_hash(document)
