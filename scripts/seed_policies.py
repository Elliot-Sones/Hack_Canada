"""Seed a curated Toronto MVP policy corpus.

Usage:
    python3 scripts/seed_policies.py
    python3 scripts/seed_policies.py --jurisdiction-name Toronto --province Ontario --country CA
"""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from datetime import date, datetime, time, timezone
from typing import Any

from sqlalchemy import MetaData, Table, and_, delete, insert, or_, select

from app.data.toronto_policy_seed import (
    CURATED_POLICY_OBJECT_KEY_PREFIX,
    CURATED_POLICY_SCHEMA_VERSION,
    CURATED_TORONTO_POLICY_DOCUMENTS,
    LEGACY_SYNTHETIC_SEED_TITLES,
)
from app.config import settings
from app.database import sync_engine
from app.devtools import redact_connection_url, render_preflight_checks, run_preflight_checks, raise_for_failed_checks

SEED_NAMESPACE = uuid.UUID("9a806c6e-1fd0-4e5b-a19a-4f9d93fc2ff4")


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=_json_default)


def _stable_uuid(*parts: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, "::".join(parts))


def _object_key(document_slug: str) -> str:
    return f"{CURATED_POLICY_OBJECT_KEY_PREFIX}{document_slug}"


def _document_file_hash(document: dict[str, Any]) -> str:
    payload = {
        "slug": document["slug"],
        "doc_type": document["doc_type"],
        "title": document["title"],
        "source_url": document["source_url"],
        "publisher": document["publisher"],
        "effective_date": document["effective_date"],
        "source_metadata": document.get("source_metadata", {}),
        "clauses": [
            {
                "slug": clause["slug"],
                "section_ref": clause["section_ref"],
                "page_ref": clause.get("page_ref"),
                "raw_text": clause["raw_text"],
                "normalized_type": clause["normalized_type"],
                "normalized_json": clause["normalized_json"],
                "confidence": clause["confidence"],
                "needs_review": clause["needs_review"],
                "applicability": clause["applicability"],
            }
            for clause in document["clauses"]
        ],
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _prune_values(table: Table, values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if key in table.c}


def _nullable_list(values: list[str] | tuple[str, ...] | None) -> list[str] | None:
    if not values:
        return None
    return list(values)


def _reflect_tables(connection) -> dict[str, Table]:
    metadata = MetaData()
    return {
        "jurisdictions": Table("jurisdictions", metadata, autoload_with=connection),
        "policy_documents": Table("policy_documents", metadata, autoload_with=connection),
        "policy_versions": Table("policy_versions", metadata, autoload_with=connection),
        "policy_clauses": Table("policy_clauses", metadata, autoload_with=connection),
        "policy_applicability_rules": Table("policy_applicability_rules", metadata, autoload_with=connection),
    }


def _resolve_jurisdiction_id(
    connection,
    jurisdictions: Table,
    jurisdiction_name: str,
    province: str,
    country: str,
) -> uuid.UUID:
    query = (
        select(jurisdictions.c.id)
        .where(jurisdictions.c.name == jurisdiction_name)
        .where(jurisdictions.c.province == province)
        .where(jurisdictions.c.country == country)
    )
    rows = connection.execute(query).all()
    if not rows:
        raise RuntimeError(
            "No matching jurisdiction found. Run seed_toronto.py first or pass "
            "--jurisdiction-name/--province/--country for the target jurisdiction."
        )
    if len(rows) > 1:
        raise RuntimeError(
            f"Found {len(rows)} matching jurisdictions for "
            f"{jurisdiction_name}, {province}, {country}. Please de-duplicate first."
        )
    return rows[0][0]


def _delete_managed_documents(connection, policy_documents: Table, jurisdiction_id: uuid.UUID) -> int:
    managed_filter = or_(
        policy_documents.c.object_key.like(f"{CURATED_POLICY_OBJECT_KEY_PREFIX}%"),
        and_(
            policy_documents.c.object_key.like("policies/seed/%"),
            policy_documents.c.title.in_(LEGACY_SYNTHETIC_SEED_TITLES),
        ),
    )
    result = connection.execute(
        delete(policy_documents)
        .where(policy_documents.c.jurisdiction_id == jurisdiction_id)
        .where(managed_filter)
    )
    return int(result.rowcount or 0)


def _document_lineage(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "seed_managed": True,
        "seed_module": "app.data.toronto_policy_seed",
        "seed_schema_version": CURATED_POLICY_SCHEMA_VERSION,
        "document_slug": document["slug"],
        "source_kind": "curated_city_policy_corpus",
    }


def _document_source_metadata(document: dict[str, Any]) -> dict[str, Any]:
    return {
        **document.get("source_metadata", {}),
        "seed_managed": True,
        "seed_schema_version": CURATED_POLICY_SCHEMA_VERSION,
        "source_url": document["source_url"],
        "publisher": document["publisher"],
    }


def _seed_document(
    connection,
    tables: dict[str, Table],
    jurisdiction_id: uuid.UUID,
    document: dict[str, Any],
    seeded_at: datetime,
) -> tuple[int, int]:
    policy_documents = tables["policy_documents"]
    policy_versions = tables["policy_versions"]
    policy_clauses = tables["policy_clauses"]
    policy_applicability_rules = tables["policy_applicability_rules"]

    document_id = _stable_uuid("policy_document", document["slug"])
    version_id = _stable_uuid("policy_version", document["slug"], CURATED_POLICY_SCHEMA_VERSION)
    file_hash = _document_file_hash(document)
    published_at = datetime.combine(document["effective_date"], time.min, tzinfo=timezone.utc)
    clause_confidences = [float(clause["confidence"]) for clause in document["clauses"]]

    document_values = _prune_values(
        policy_documents,
        {
            "id": document_id,
            "jurisdiction_id": jurisdiction_id,
            "doc_type": document["doc_type"],
            "title": document["title"],
            "source_url": document["source_url"],
            "publisher": document["publisher"],
            "acquired_at": seeded_at,
            "effective_date": document["effective_date"],
            "object_key": _object_key(document["slug"]),
            "file_hash": file_hash,
            "lineage_json": _document_lineage(document),
            "redistribution_policy": "Refer users to the official source URL for the full document.",
            "source_schema_version": CURATED_POLICY_SCHEMA_VERSION,
            "license_status": "publicly_available",
            "internal_storage_allowed": True,
            "redistribution_allowed": False,
            "export_allowed": False,
            "derived_export_allowed": True,
            "aggregation_required": False,
            "retention_policy": "retain_until_reseeded",
            "source_metadata_json": _document_source_metadata(document),
            "parse_status": "parsed",
        },
    )
    connection.execute(insert(policy_documents).values(document_values))

    version_values = _prune_values(
        policy_versions,
        {
            "id": version_id,
            "document_id": document_id,
            "version_number": 1,
            "parser_version": CURATED_POLICY_SCHEMA_VERSION,
            "extracted_at": seeded_at,
            "confidence_avg": round(sum(clause_confidences) / len(clause_confidences), 3),
            "confidence_min": min(clause_confidences),
            "clause_count": len(document["clauses"]),
            "published_at": published_at,
            "is_active": True,
        },
    )
    connection.execute(insert(policy_versions).values(version_values))

    clause_count = 0
    rule_count = 0

    for clause in document["clauses"]:
        clause_id = _stable_uuid("policy_clause", document["slug"], clause["slug"])
        clause_values = _prune_values(
            policy_clauses,
            {
                "id": clause_id,
                "policy_version_id": version_id,
                "section_ref": clause["section_ref"],
                "page_ref": clause.get("page_ref"),
                "raw_text": clause["raw_text"],
                "normalized_type": clause["normalized_type"],
                "normalized_json": clause["normalized_json"],
                "confidence": clause["confidence"],
                "needs_review": clause["needs_review"],
            },
        )
        connection.execute(insert(policy_clauses).values(clause_values))
        clause_count += 1

        for rule_index, rule in enumerate(clause["applicability"], start=1):
            rule_id = _stable_uuid("policy_rule", document["slug"], clause["slug"], str(rule_index))
            applicability_payload = {
                **rule.get("applicability_json", {}),
                "seed_managed": True,
                "seed_schema_version": CURATED_POLICY_SCHEMA_VERSION,
                "document_slug": document["slug"],
                "clause_slug": clause["slug"],
            }
            rule_values = _prune_values(
                policy_applicability_rules,
                {
                    "id": rule_id,
                    "policy_clause_id": clause_id,
                    "jurisdiction_id": jurisdiction_id,
                    "zone_filter": _nullable_list(rule.get("zone_filter")),
                    "use_filter": _nullable_list(rule.get("use_filter")),
                    "override_level": rule["override_level"],
                    "applicability_json": applicability_payload,
                },
            )
            connection.execute(insert(policy_applicability_rules).values(rule_values))
            rule_count += 1

    return clause_count, rule_count


def seed_policies(jurisdiction_name: str = "Toronto", province: str = "Ontario", country: str = "CA") -> None:
    with sync_engine.begin() as connection:
        tables = _reflect_tables(connection)
        jurisdiction_id = _resolve_jurisdiction_id(
            connection,
            tables["jurisdictions"],
            jurisdiction_name=jurisdiction_name,
            province=province,
            country=country,
        )
        deleted_count = _delete_managed_documents(connection, tables["policy_documents"], jurisdiction_id)

        seeded_at = datetime.now(timezone.utc)
        total_docs = 0
        total_clauses = 0
        total_rules = 0

        for document in CURATED_TORONTO_POLICY_DOCUMENTS:
            clause_count, rule_count = _seed_document(
                connection,
                tables=tables,
                jurisdiction_id=jurisdiction_id,
                document=document,
                seeded_at=seeded_at,
            )
            total_docs += 1
            total_clauses += clause_count
            total_rules += rule_count

    print(
        "Seeded "
        f"{total_docs} curated Toronto policy documents with "
        f"{total_clauses} clauses and {total_rules} applicability rules "
        f"for {jurisdiction_name}, {province}, {country}. "
        f"Replaced {deleted_count} managed legacy/current seed documents."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed curated Toronto MVP policy documents")
    parser.add_argument("--jurisdiction-name", default="Toronto")
    parser.add_argument("--province", default="Ontario")
    parser.add_argument("--country", default="CA")
    args = parser.parse_args()
    print(f"Database target: {redact_connection_url(settings.DATABASE_URL_SYNC)}")
    checks = run_preflight_checks()
    print(render_preflight_checks(checks))
    try:
        raise_for_failed_checks(checks)
    except RuntimeError as exc:
        raise SystemExit(f"Preflight failed: {exc}") from exc
    seed_policies(
        jurisdiction_name=args.jurisdiction_name,
        province=args.province,
        country=args.country,
    )


if __name__ == "__main__":
    main()
