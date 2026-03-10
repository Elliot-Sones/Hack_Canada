"""
policy_stack.py – RAG-backed policy retrieval.

Replaces the former DB-backed query with ChromaDB vector search
from the fine-tuned-RAG system.
"""
import os
import sys
import uuid
from pathlib import Path

from app.models.geospatial import Parcel
from app.schemas.geospatial import (
    PolicyCitationResponse,
    PolicyEntryResponse,
    PolicyStackResponse,
)

# ---------------------------------------------------------------------------
# RAG retriever setup
# ---------------------------------------------------------------------------

_RAG_DIR = str(Path(__file__).resolve().parents[2] / "fine-tuned-RAG")
if _RAG_DIR not in sys.path:
    sys.path.insert(0, _RAG_DIR)

# Lazy-loaded to avoid import errors when chroma_db is missing at import time
_retriever_search = None


def _get_search():
    global _retriever_search
    if _retriever_search is None:
        from retriever import search  # noqa: E402 – lives in fine-tuned-RAG/
        _retriever_search = search
    return _retriever_search


# Deterministic namespace for generating stable UUIDs from source strings
_NS = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def _make_id(text: str) -> uuid.UUID:
    return uuid.uuid5(_NS, text)


# ---------------------------------------------------------------------------
# Build response from RAG results
# ---------------------------------------------------------------------------

def _rag_results_to_response(
    parcel_id: uuid.UUID,
    results: list[dict],
) -> PolicyStackResponse:
    entries: list[PolicyEntryResponse] = []
    citations: list[PolicyCitationResponse] = []

    for i, r in enumerate(results):
        meta = r.get("metadata", {})
        source = meta.get("source", "Unknown Document")
        source_type = meta.get("source_type", "policy")
        page = meta.get("page")
        content = r.get("content", "")
        score = r.get("score")

        clause_id = _make_id(f"{source}:{page}:{i}")
        doc_id = _make_id(source)
        version_id = _make_id(f"{source}:v1")

        section_ref = f"Page {page}" if page else f"Extract {i + 1}"

        entries.append(
            PolicyEntryResponse(
                clause_id=clause_id,
                policy_version_id=version_id,
                document_id=doc_id,
                document_title=source,
                doc_type=source_type,
                override_level=i,
                section_ref=section_ref,
                page_ref=str(page) if page else None,
                raw_text=content,
                normalized_type="rag_extract",
                normalized_json={},
                applicability_json={},
                confidence=score if score is not None else 0.0,
                effective_date=None,
                source_url=None,
                snapshot=None,
            )
        )
        citations.append(
            PolicyCitationResponse(
                clause_id=clause_id,
                document_title=source,
                doc_type=source_type,
                section_ref=section_ref,
                page_ref=str(page) if page else None,
                source_url=None,
                effective_date=None,
            )
        )

    return PolicyStackResponse(
        parcel_id=parcel_id,
        applicable_policies=entries,
        citations=citations,
        snapshots=[],
    )


# ---------------------------------------------------------------------------
# Public API (async kept for router signature compat, but search is sync)
# ---------------------------------------------------------------------------

def _build_query(parcel: Parcel) -> str:
    parts = []
    if parcel.zone_code:
        parts.append(f"zoning {parcel.zone_code}")
    if parcel.address:
        parts.append(parcel.address)
    if parcel.current_use:
        parts.append(parcel.current_use)
    return "Ontario planning policy for " + ", ".join(parts) if parts else "Ontario planning and zoning policy"


async def get_policy_stack_response(db, parcel: Parcel) -> PolicyStackResponse:
    """Called by the parcels router (async endpoint)."""
    search = _get_search()
    query = _build_query(parcel)
    results = search(query, k=8)
    return _rag_results_to_response(parcel.id, results)


def get_policy_stack_response_sync(db, parcel: Parcel) -> PolicyStackResponse:
    """Called by plan tasks (sync background thread)."""
    search = _get_search()
    query = _build_query(parcel)
    results = search(query, k=8)
    return _rag_results_to_response(parcel.id, results)
