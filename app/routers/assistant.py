import asyncio
import json
import logging
import re
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_ai_provider
from app.config import settings
from app.data.ontario_policy import (
    MINOR_VARIANCE_FOUR_TESTS,
    ONTARIO_POLICY_HIERARCHY,
    OREG_462_24,
    RECENT_LEGISLATION,
    TORONTO_ZONING_KEY_RULES,
)
from app.data.toronto_zoning import ZONE_STANDARDS
from app.dependencies import get_db_session
from app.schemas.assistant import (
    AssistantChatRequest, AssistantChatResponse, ContractorRecommendation,
    InfraModelParseRequest, InfraModelParseResponse,
    ModelParseRequest, ModelParseResponse, ModelUpdate, ProposedAction,
)
from app.services.zoning_parser import extract_zone_category

logger = logging.getLogger(__name__)

router = APIRouter()

_ACTION_RE = re.compile(r"<!--ACTION:(.*?)-->", re.DOTALL)
_MODEL_RE = re.compile(r"<!--MODEL:(.*?)-->", re.DOTALL)
_CONTRACTORS_RE = re.compile(r"<!--CONTRACTORS:(.*?)-->", re.DOTALL)

_POLICY_CONTEXT = "\n\n".join([
    ONTARIO_POLICY_HIERARCHY,
    TORONTO_ZONING_KEY_RULES,
    OREG_462_24,
    RECENT_LEGISLATION,
    MINOR_VARIANCE_FOUR_TESTS,
])

SYSTEM_PROMPT = f"""You are an expert land-development due-diligence assistant for the City of Toronto and Ontario.

## Your role
Help development analysts, planners, and architects understand:
- Zoning regulations (By-law 569-2013) and permitted uses for a specific site
- Compliance gaps, variance requirements, and approval pathways
- Ontario planning policy hierarchy and how it applies
- Development potential, massing, FSI, setbacks, lot coverage
- Committee of Adjustment (CoA), ZBA, OPA, and site plan processes
- Infrastructure capacity — electrical, water, sewer — and whether nearby grid/pipes can support a project

## Ontario Planning Law Reference
{_POLICY_CONTEXT}

## Two modes

**Answering mode** (default): Answer the user's question using the policy reference above, the parcel context, and the LIVE SITE DATA provided. Be precise — cite by-law sections and specific numbers. When infrastructure data is provided, reference actual nearby substations, power line voltages, water main diameters, etc. Distinguish as-of-right permissions from what needs approval. If information is uncertain or missing, say so.

**Generation mode**: When the user explicitly asks you to generate a planning document, OR when you determine that generating a document is the most useful response to their question, propose it.

To propose generation, append this marker on its own line at the very end of your response:
<!--ACTION:{{"label":"Generate [Document Name]","query":"[complete query describing exactly what to generate and for which site]","doc_types":["doc_type_1","doc_type_2"]}}-->

Examples of when to propose generation:
- "Write a planning rationale for a 4-storey multiplex at 192 Jarvis" → answer briefly then propose
- "Generate the submission package" → propose with "doc_types":"all"
- "Can I build a garden suite here?" → answer the question, do NOT propose generation
- "What's the FSI limit?" → answer the question, do NOT propose generation

Only propose generation when a formal document is genuinely what the user wants. Never propose generation for informational questions.

## Document catalog
When the user needs a formal document, propose generating it using the ACTION marker.
Include a "doc_types" array in the ACTION JSON to specify which document(s) to generate.

Available documents (grouped by when they're useful):

**Core submission package** (propose for "generate the submission package"):
cover_letter, planning_rationale, compliance_matrix, site_plan_data, massing_summary,
unit_mix_summary, financial_feasibility, precedent_report, public_benefit_statement, shadow_study

**Variance & compliance** (propose when discussing variances, CoA, compliance):
four_statutory_tests, variance_justification, as_of_right_check, compliance_review_report

**Approval pathway** (propose when discussing process, timeline, costs):
approval_pathway_document, timeline_cost_estimate, required_studies_checklist,
professional_referral_checklist, building_permit_readiness_checklist, pac_prep_package

**Appeals & responses** (propose when discussing refusals, appeals, mediation):
olt_appeal_brief, revised_rationale, mediation_strategy, correction_response

**Community & readiness** (propose for outreach, submission prep):
neighbour_support_letter, submission_readiness_report, due_diligence_report

Example ACTION markers:
- Single doc: <!--ACTION:{{"label":"Generate As-of-Right Check","query":"...","doc_types":["as_of_right_check"]}}-->
- Multiple related docs: <!--ACTION:{{"label":"Generate Variance Package","query":"...","doc_types":["four_statutory_tests","variance_justification","as_of_right_check"]}}-->
- Full package: <!--ACTION:{{"label":"Generate Full Submission Package","query":"...","doc_types":"all"}}-->

Only propose documents that are relevant to what the user is asking about. Never propose the full package unless the user explicitly asks for it.

## Contractor recommendation tool
IMPORTANT: When the user asks about contractors, professionals, or what team they need, OR when you mention needing specific professionals in your answer, you MUST append the CONTRACTORS marker at the very end of your response. This is how the system fetches real local companies to show the user.

Format — append on its own line at the very end:
<!--CONTRACTORS:{{"trades":["search term 1","search term 2","search term 3"]}}-->

Example: If the user asks "what contractors do I need for a multiplex?", your response should end with:
<!--CONTRACTORS:{{"trades":["general contractor","structural engineer","renovation contractor","architect"]}}-->

Valid search terms: "structural engineer", "general contractor", "architectural lighting consultant", "quantity surveyor", "renovation contractor", "geotechnical engineer", "land surveyor", "arborist", "environmental consultant", "concrete contractor", "planning consultant", "architect", "MEP engineer", "acoustic consultant".

Maximum 4 trades. You MUST include this marker whenever contractors or professionals are discussed — it is invisible to the user and triggers the system to show real nearby companies.

## Rules
- Keep answers concise and grounded — 2–4 short paragraphs maximum for most questions
- Cite by-law sections (e.g. "§10.5.10.20 of By-law 569-2013") and policy clauses when confident
- Distinguish as-of-right from what needs a variance or higher approval
- Never fabricate data — if parcel data is not provided, say so clearly
- When LIVE SITE DATA is provided, USE IT. Reference actual infrastructure scores, distances, voltages, diameters.
- Plain text only, no markdown headers in responses (the ACTION, MODEL, and CONTRACTORS markers are not visible to the user — always include them when applicable)
"""


# Keywords in user message that trigger contractor detection
_CONTRACTOR_USER_TRIGGERS = re.compile(
    r"\b(contractor|contractors|who do i need|what team|hire|find me|recommend|professionals|trades)\b",
    re.IGNORECASE,
)

# Mapping: keyword found in AI response → Google Places trade search term
_RESPONSE_TRADE_MAP = {
    "structural engineer": "structural engineer",
    "general contractor": "general contractor",
    "architect": "architect",
    "planning consultant": "planning consultant",
    "geotechnical engineer": "geotechnical engineer",
    "MEP engineer": "MEP engineer",
    "land surveyor": "land surveyor",
    "arborist": "arborist",
    "environmental consultant": "environmental consultant",
    "concrete contractor": "concrete contractor",
    "acoustic consultant": "acoustic consultant",
    "quantity surveyor": "quantity surveyor",
    "renovation contractor": "renovation contractor",
    "lighting consultant": "architectural lighting consultant",
}


def _detect_contractor_trades(user_text: str, ai_response: str) -> list[str] | None:
    """Detect if the conversation is about contractors and extract relevant trades."""
    if not _CONTRACTOR_USER_TRIGGERS.search(user_text):
        return None

    response_lower = ai_response.lower()
    trades: list[str] = []
    seen: set[str] = set()
    for keyword, trade in _RESPONSE_TRADE_MAP.items():
        if keyword.lower() in response_lower and trade not in seen:
            seen.add(trade)
            trades.append(trade)
            if len(trades) >= 4:
                break

    if not trades:
        trades = ["general contractor", "structural engineer"]

    return trades


async def _fetch_contractors(trades: list[str], lat: float, lng: float) -> list[ContractorRecommendation]:
    """Fetch contractor recommendations from Google Places API."""
    if not settings.GOOGLE_PLACES_API_KEY or not trades:
        return []

    contractors: list[ContractorRecommendation] = []
    async with httpx.AsyncClient(timeout=10) as client:
        for trade in trades[:4]:
            try:
                resp = await client.get(
                    "https://maps.googleapis.com/maps/api/place/textsearch/json",
                    params={
                        "query": f"{trade} near Toronto",
                        "location": f"{lat},{lng}",
                        "radius": "10000",
                        "key": settings.GOOGLE_PLACES_API_KEY,
                    },
                )
                data = resp.json()
                for place in (data.get("results") or [])[:3]:
                    contractors.append(ContractorRecommendation(
                        name=place.get("name", ""),
                        rating=place.get("rating"),
                        review_count=place.get("user_ratings_total"),
                        phone=place.get("formatted_phone_number"),
                        address=place.get("formatted_address"),
                        trade=trade,
                    ))
            except Exception:
                logger.warning("Google Places API error for trade=%s", trade, exc_info=True)
    return contractors


def _parse_response(raw: str, zone_constraints: dict | None = None, zone_code: str | None = None) -> tuple[str, ProposedAction | None, ModelUpdate | None, list[str] | None]:
    """Strip action/model/contractor markers from the response and parse them."""
    text = raw

    # Parse action marker
    action = None
    action_match = _ACTION_RE.search(text)
    if action_match:
        text = _ACTION_RE.sub("", text)
        try:
            data = json.loads(action_match.group(1))
            action = ProposedAction(
                label=data.get("label", "Generate Document"),
                query=data.get("query", ""),
                doc_types=data.get("doc_types"),
            )
        except (json.JSONDecodeError, KeyError):
            pass

    # Parse model update marker
    model_update = None
    model_match = _MODEL_RE.search(text)
    if model_match:
        text = _MODEL_RE.sub("", text)
        try:
            data = json.loads(model_match.group(1))

            # Clamp to zoning limits
            warnings = []
            if zone_constraints:
                max_h = zone_constraints["max_height_m"]
                max_s = zone_constraints["max_storeys"]
                max_cov = zone_constraints["max_lot_coverage_pct"] / 100.0

                if data.get("height_m", 0) > max_h:
                    warnings.append(f"Height clamped from {data['height_m']}m to {max_h}m ({zone_code} zone max)")
                    data["height_m"] = max_h
                if data.get("storeys", 0) > max_s:
                    warnings.append(f"Storeys clamped from {data['storeys']} to {max_s} ({zone_code} zone max)")
                    data["storeys"] = max_s
                if data.get("footprint_coverage", 0) > max_cov:
                    warnings.append(f"Coverage clamped from {data['footprint_coverage']:.0%} to {max_cov:.0%} ({zone_code} zone max)")
                    data["footprint_coverage"] = max_cov

            if warnings:
                data["warnings"] = warnings

            model_update = ModelUpdate(**data)
        except (json.JSONDecodeError, KeyError, Exception):
            pass

    # Parse contractor recommendation marker
    contractor_trades = None
    contractor_match = _CONTRACTORS_RE.search(text)
    if contractor_match:
        text = _CONTRACTORS_RE.sub("", text)
        try:
            data = json.loads(contractor_match.group(1))
            contractor_trades = data.get("trades", [])
        except (json.JSONDecodeError, KeyError):
            pass

    return text.strip(), action, model_update, contractor_trades


# ---------------------------------------------------------------------------
# Data gathering — pull real site data in parallel before AI call
# ---------------------------------------------------------------------------

async def _gather_site_data(
    parcel_id: str | None,
    lat: float | None,
    lng: float | None,
    zone_code: str | None,
    db: AsyncSession,
) -> str:
    """Fetch zoning analysis, electrical capacity, water infrastructure, and
    policy RAG data in parallel. Returns a formatted context string."""

    sections: list[str] = []

    # Parse parcel_id to UUID if provided
    pid = None
    if parcel_id:
        try:
            pid = uuid.UUID(parcel_id)
        except ValueError:
            pass

    # Default coords
    site_lat = lat or 43.6532
    site_lng = lng or -79.3832

    # Launch parallel data fetches
    async def _noop():
        return None
    zoning_task = _fetch_zoning(pid, db) if pid else _noop()
    electrical_task = _fetch_electrical(site_lat, site_lng, db)
    watermain_task = _fetch_watermains(site_lat, site_lng)
    rag_task = _fetch_policy_rag(zone_code, parcel_id)

    zoning_result, electrical_result, watermain_result, rag_result = await asyncio.gather(
        zoning_task, electrical_task, watermain_task, rag_task,
        return_exceptions=True,
    )

    # Format zoning data
    if isinstance(zoning_result, dict) and zoning_result:
        z = zoning_result
        lines = ["## LIVE ZONING ANALYSIS"]
        if z.get("zone_string"):
            lines.append(f"Zone: {z['zone_string']}")
        if z.get("address"):
            lines.append(f"Address: {z['address']}")
        stds = z.get("standards")
        if stds:
            lines.append(f"Max height: {stds.get('max_height_m')}m | Max storeys: {stds.get('max_storeys')}")
            lines.append(f"Max FSI: {stds.get('max_fsi')} | Max lot coverage: {stds.get('max_lot_coverage_pct')}%")
            lines.append(f"Setbacks — front: {stds.get('min_front_setback_m')}m, rear: {stds.get('min_rear_setback_m')}m, side: {stds.get('min_interior_side_setback_m')}m")
            if stds.get("permitted_uses"):
                lines.append(f"Permitted uses: {', '.join(stds['permitted_uses'][:10])}")
            if stds.get("bylaw_section"):
                lines.append(f"By-law section: {stds['bylaw_section']}")
        overlays = z.get("overlay_constraints", [])
        if overlays:
            lines.append("Overlays:")
            for ov in overlays[:5]:
                lines.append(f"  - {ov.get('layer_name', 'Unknown')}: {ov.get('impact', '')}")
        warnings = z.get("warnings", [])
        if warnings:
            lines.append("Warnings: " + "; ".join(warnings[:5]))
        sections.append("\n".join(lines))

    # Format electrical data
    if isinstance(electrical_result, dict) and electrical_result:
        e = electrical_result
        lines = ["## LIVE ELECTRICAL INFRASTRUCTURE"]
        lines.append(f"Infrastructure score: {e.get('infrastructure_score', 'N/A')}/100")
        lines.append(f"Verdict: {e.get('verdict', 'unknown')} (confidence: {e.get('confidence', 0):.0%})")
        sub = e.get("nearest_substation")
        if sub:
            lines.append(f"Nearest substation: {sub.get('name', 'Unknown')} — {sub.get('distance_m', '?')}m away, {sub.get('voltage', 'unknown voltage')}")
        pline = e.get("nearest_power_line")
        if pline:
            lines.append(f"Nearest power line: {pline.get('distance_m', '?')}m away, {pline.get('voltage_kv', '?')} kV")
        detail = e.get("infra_detail", {})
        lines.append(f"Nearby: {detail.get('substations_nearby', 0)} substations, {detail.get('power_lines_nearby', 0)} power lines, {detail.get('transformers_nearby', 0)} transformers")
        recs = e.get("recommendations", [])
        if recs:
            lines.append("Recommendations:")
            for r in recs[:4]:
                lines.append(f"  - {r}")
        sections.append("\n".join(lines))

    # Format watermain data
    if isinstance(watermain_result, list) and watermain_result:
        lines = ["## LIVE WATER INFRASTRUCTURE"]
        lines.append(f"Water mains within 500m: {len(watermain_result)}")
        # Summarize by diameter
        diameters = {}
        materials = {}
        for feat in watermain_result:
            p = feat.get("properties", {})
            d = p.get("diameter_mm")
            m = p.get("material", "Unknown")
            if d:
                diameters[d] = diameters.get(d, 0) + 1
            materials[m] = materials.get(m, 0) + 1
        if diameters:
            sorted_d = sorted(diameters.items(), key=lambda x: -x[1])
            lines.append("Diameters: " + ", ".join(f"{d}mm ({n} segments)" for d, n in sorted_d[:5]))
        if materials:
            sorted_m = sorted(materials.items(), key=lambda x: -x[1])
            lines.append("Materials: " + ", ".join(f"{m} ({n})" for m, n in sorted_m[:5]))
        # Nearest/largest
        largest = max((f for f in watermain_result if f.get("properties", {}).get("diameter_mm")),
                       key=lambda f: f["properties"]["diameter_mm"], default=None)
        if largest:
            p = largest["properties"]
            lines.append(f"Largest nearby main: {p['diameter_mm']}mm {p.get('material', '')} (installed {p.get('install_year', 'unknown')})")
        sections.append("\n".join(lines))

    # Format RAG results
    if isinstance(rag_result, list) and rag_result:
        lines = ["## RELEVANT POLICY EXTRACTS (from RAG)"]
        for r in rag_result[:5]:
            source = r.get("metadata", {}).get("source", "Unknown")
            content = r.get("content", "")[:300]
            score = r.get("score")
            score_str = f" (relevance: {score:.2f})" if score is not None else ""
            lines.append(f"[{source}{score_str}]: {content}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections) if sections else ""


async def _fetch_zoning(parcel_id: uuid.UUID, db: AsyncSession) -> dict | None:
    """Fetch full zoning analysis for a parcel."""
    try:
        from app.services.geospatial import get_active_parcel_by_id, list_active_snapshot_ids
        from app.services.overlay_service import get_parcel_overlays_response
        from app.services.zoning_service import build_zoning_analysis
        from sqlalchemy import func, select
        from app.models.geospatial import ParcelZoningAssignment

        active_snapshot_ids = await list_active_snapshot_ids(db, "parcel_base")
        parcel = await get_active_parcel_by_id(db, parcel_id, active_snapshot_ids=active_snapshot_ids)
        if not parcel:
            return None

        overlay_response = await get_parcel_overlays_response(db, parcel)
        active_zoning_ids = await list_active_snapshot_ids(db, "zoning_geometry")

        zoning_count = None
        if active_zoning_ids:
            zoning_count = await db.scalar(
                select(func.count())
                .select_from(ParcelZoningAssignment)
                .where(ParcelZoningAssignment.parcel_id == parcel_id)
                .where(ParcelZoningAssignment.source_snapshot_id.in_(list(active_zoning_ids)))
            )

        analysis = build_zoning_analysis(
            parcel,
            overlay_data=[o.model_dump() for o in overlay_response.overlays],
            zoning_assignment_count=zoning_count,
        )

        result = {
            "zone_string": analysis.zone_string,
            "address": analysis.address,
            "overlay_constraints": [
                {"layer_name": c.get("layer_name"), "impact": c.get("impact")}
                for c in analysis.overlay_constraints
            ],
            "warnings": list(analysis.warnings),
        }
        if analysis.standards:
            s = analysis.standards
            result["standards"] = {
                "max_height_m": s.max_height_m,
                "max_storeys": s.max_storeys,
                "max_fsi": s.max_fsi,
                "max_lot_coverage_pct": s.max_lot_coverage_pct,
                "min_front_setback_m": s.min_front_setback_m,
                "min_rear_setback_m": s.min_rear_setback_m,
                "min_interior_side_setback_m": s.min_interior_side_setback_m,
                "permitted_uses": list(s.permitted_uses),
                "bylaw_section": s.bylaw_section,
            }
        return result
    except Exception:
        logger.warning("Failed to fetch zoning analysis", exc_info=True)
        return None


async def _fetch_electrical(lat: float, lng: float, db: AsyncSession) -> dict | None:
    """Fetch electrical capacity analysis for a location."""
    try:
        from app.services.electrical_capacity import check_capacity, score_infrastructure
        from app.routers.infrastructure import _query_electrical_bbox

        # Get features from in-memory cache (fast, no DB needed)
        # Use a 2km bbox around the point
        delta = 0.018  # ~2km
        features = _query_electrical_bbox(
            lng - delta, lat - delta, lng + delta, lat + delta,
            limit=200, include_poles=False,
        )

        if not features:
            return None

        result = check_capacity(
            lat=lat, lng=lng, features=features,
            building_type="residential", num_units=1,
        )
        return result
    except Exception:
        logger.warning("Failed to fetch electrical data", exc_info=True)
        return None


async def _fetch_watermains(lat: float, lng: float) -> list | None:
    """Fetch nearby watermain segments from the in-memory cache."""
    try:
        from app.routers.infrastructure import _load_watermains, _geom_intersects_bbox

        features = _load_watermains()
        delta = 0.005  # ~500m
        min_lng, min_lat = lng - delta, lat - delta
        max_lng, max_lat = lng + delta, lat + delta

        nearby = []
        for feat in features:
            if len(nearby) >= 50:
                break
            geom = feat.get("geometry")
            if not geom:
                continue
            if _geom_intersects_bbox(geom, min_lng, min_lat, max_lng, max_lat):
                p = feat.get("properties", {})
                nearby.append({
                    "type": "Feature",
                    "geometry": None,  # Don't include geometry in context
                    "properties": {
                        "diameter_mm": int(p.get("Watermain Diameter")) if p.get("Watermain Diameter") else None,
                        "material": p.get("Watermain Material") or "Unknown",
                        "install_year": int(p.get("Watermain Construction Year")) if p.get("Watermain Construction Year") and str(p.get("Watermain Construction Year")).isdigit() else None,
                    },
                })
        return nearby if nearby else None
    except Exception:
        logger.warning("Failed to fetch watermain data", exc_info=True)
        return None


async def _fetch_policy_rag(zone_code: str | None, parcel_id: str | None) -> list | None:
    """Fetch relevant policy chunks from ChromaDB RAG."""
    try:
        import sys
        from pathlib import Path
        rag_dir = str(Path(__file__).resolve().parents[2] / "fine-tuned-RAG")
        if rag_dir not in sys.path:
            sys.path.insert(0, rag_dir)
        from retriever import search

        query_parts = []
        if zone_code:
            query_parts.append(f"zoning {zone_code}")
        query_parts.append("Ontario planning policy development standards")
        query = " ".join(query_parts)

        # Run sync search in thread pool to not block event loop
        results = await asyncio.to_thread(search, query, 5)
        return results if results else None
    except Exception:
        logger.warning("Failed to fetch RAG results", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assistant/parse-model", response_model=ModelParseResponse, status_code=status.HTTP_200_OK)
async def parse_model_description(body: ModelParseRequest) -> ModelParseResponse:
    """Parse a natural-language building description into 3D model parameters."""
    if not settings.AI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI assistant is not configured on the server",
        )

    provider = get_ai_provider()
    current = body.current_params or {}

    zone_constraints = None
    zone_label = body.zone_code
    if body.zone_code:
        zone_key = extract_zone_category(body.zone_code)
        if zone_key:
            zone_constraints = ZONE_STANDARDS.get(zone_key)
            zone_label = zone_key

    zoning_line = ""
    if zone_constraints:
        zoning_line = (
            f"\nZoning limits ({zone_label} zone): "
            f"max {zone_constraints['max_height_m']}m height, "
            f"max {zone_constraints['max_storeys']} storeys, "
            f"max {zone_constraints['max_lot_coverage_pct']}% coverage, "
            f"max FSI {zone_constraints['max_fsi']}. "
            "Respect these unless the user explicitly asks to exceed them.\n"
        )

    prompt = f"""Extract building parameters from this description. Return a JSON object with exactly these fields:
- storeys (integer): total above-grade floors
- podium_storeys (integer): ground-level base floors (0 if no podium, midrise, or townhouse)
- height_m (float): total height in metres; use podium_storeys * 4.5 + (storeys - podium_storeys) * 3.5
- setback_m (float): tower setback from podium edge in metres (3.0 default for tower_on_podium, 0 otherwise)
- typology (string): one of tower_on_podium | midrise | townhouse | mixed_use_midrise | point_tower | slab
- footprint_coverage (float 0-1): 0.45 for tower/point_tower, 0.60 for midrise/mixed/slab, 0.55 for townhouse
- unit_width (float or null): width of each unit in metres for townhouse typology (default 6.0), null otherwise
- tower_shape (string or null): "square" or "circular" for point_tower typology, null otherwise
{zoning_line}
Current parameters (baseline for unspecified values):
{json.dumps(current)}

Description: "{body.text}"

Return only valid JSON, no explanation."""

    try:
        raw = await provider.generate(prompt=prompt, max_tokens=400)
        content = raw.content.strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content.strip())

        warnings = []
        if zone_constraints:
            max_h = zone_constraints["max_height_m"]
            max_s = zone_constraints["max_storeys"]
            max_cov = zone_constraints["max_lot_coverage_pct"] / 100.0

            if data.get("height_m", 0) > max_h:
                warnings.append(f"Height clamped from {data['height_m']}m to {max_h}m ({zone_label} zone max)")
                data["height_m"] = max_h
            if data.get("storeys", 0) > max_s:
                warnings.append(f"Storeys clamped from {data['storeys']} to {max_s} ({zone_label} zone max)")
                data["storeys"] = max_s
            if data.get("footprint_coverage", 0) > max_cov:
                warnings.append(f"Coverage clamped from {data['footprint_coverage']:.0%} to {max_cov:.0%} ({zone_label} zone max)")
                data["footprint_coverage"] = max_cov

        if warnings:
            data["warnings"] = warnings

        return ModelParseResponse(**data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Model parsing failed: {exc}",
        ) from exc


@router.post("/assistant/chat", response_model=AssistantChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_assistant(
    body: AssistantChatRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AssistantChatResponse:
    if not settings.AI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI assistant is not configured on the server",
        )

    provider = get_ai_provider()
    history = body.messages[-20:]
    transcript_lines = []
    for message in history:
        speaker = "User" if message.role == "user" else "Assistant"
        transcript_lines.append(f"{speaker}: {message.text.strip()}")

    # ── Gather real site data in parallel ──
    site_data = await _gather_site_data(
        parcel_id=body.parcel_id,
        lat=body.lat,
        lng=body.lng,
        zone_code=body.zone_code,
        db=db,
    )

    # ── Build prompt with real data ──
    prompt_parts = []

    if body.parcel_context:
        prompt_parts.append(f"Current site context:\n{body.parcel_context.strip()}")

    if site_data:
        prompt_parts.append(f"LIVE SITE DATA (real-time from municipal databases):\n{site_data}")

    # If a 3D model is active, give the AI the tool to update it
    zone_constraints = None
    zone_label = body.zone_code
    if body.model_params:
        prompt_parts.append(f"Active 3D model parameters:\n{json.dumps(body.model_params)}")

        zoning_line = ""
        if body.zone_code:
            zone_key = extract_zone_category(body.zone_code)
            if zone_key:
                zone_constraints = ZONE_STANDARDS.get(zone_key)
                zone_label = zone_key
            if zone_constraints:
                zoning_line = (
                    f"Zoning limits ({zone_label} zone): "
                    f"max {zone_constraints['max_height_m']}m height, "
                    f"max {zone_constraints['max_storeys']} storeys, "
                    f"max {zone_constraints['max_lot_coverage_pct']}% coverage, "
                    f"max FSI {zone_constraints['max_fsi']}."
                )

        prompt_parts.append(
            "You have a MODEL UPDATE tool. When the user asks to change the building "
            "(height, storeys, typology, setbacks, etc.), update the model by appending "
            "this marker at the end of your response:\n"
            '<!--MODEL:{"storeys":N,"podium_storeys":N,"height_m":N,"setback_m":N,'
            '"typology":"TYPE","footprint_coverage":N,"unit_width":N_OR_NULL,"tower_shape":"SHAPE_OR_NULL"}-->\n'
            "Typology must be one of: tower_on_podium | midrise | townhouse | mixed_use_midrise | point_tower | slab\n"
            "Use the current model parameters as baseline — only change what the user asks for. "
            "Calculate height_m as: podium_storeys * 4.5 + (storeys - podium_storeys) * 3.5\n"
            f"{zoning_line}\n"
            "Always include a brief conversational response before the marker."
        )

    # Include uploaded file context
    if body.upload_context:
        upload_lines = []
        for item in body.upload_context:
            parts = [f"- **{item.filename}**"]
            if item.doc_category:
                parts.append(f"  Category: {item.doc_category}")
            if item.extracted_data:
                building = item.extracted_data.get("building", {})
                dimensions = item.extracted_data.get("dimensions", {})
                details = []
                for key, label in [("storeys", "storeys"), ("height_m", "m height"), ("unit_count", "units"), ("gfa_m2", "m² GFA"), ("building_type", "")]:
                    val = building.get(key)
                    if val is not None:
                        details.append(f"{val} {label}".strip() if label else str(val))
                for key, label in [("lot_area_m2", "m² lot"), ("lot_frontage_m", "m frontage"), ("lot_depth_m", "m depth")]:
                    val = dimensions.get(key)
                    if val is not None:
                        details.append(f"{val} {label}")
                if details:
                    parts.append(f"  Extracted: {', '.join(details)}")
                setback_info = []
                for key, label in [("setback_front_m", "front"), ("setback_rear_m", "rear"), ("setback_side_m", "side")]:
                    val = dimensions.get(key)
                    if val is not None:
                        setback_info.append(f"{label} {val}m")
                if setback_info:
                    parts.append(f"  Setbacks: {', '.join(setback_info)}")
                notes = item.extracted_data.get("notes") or item.extracted_data.get("description")
                if notes:
                    parts.append(f"  Notes: {notes}")
            upload_lines.append("\n".join(parts))
        prompt_parts.append("Uploaded project files (user-provided documents — use this data when answering):\n" + "\n\n".join(upload_lines))

    prompt_parts.append("Conversation:\n" + "\n\n".join(transcript_lines))
    prompt_parts.append("Respond to the latest user message.")

    # ── Single AI call with rich context ──
    try:
        response = await provider.generate(
            prompt="\n\n".join(prompt_parts),
            system=SYSTEM_PROMPT,
            max_tokens=1500,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Assistant generation failed: {exc}",
        ) from exc

    message, proposed_action, model_update, contractor_trades = _parse_response(
        response.content, zone_constraints, zone_label
    )

    # If the AI didn't emit a CONTRACTORS marker, detect from context
    if not contractor_trades:
        contractor_trades = _detect_contractor_trades(
            user_text=history[-1].text if history else "",
            ai_response=message,
        )

    # Fetch real contractor data
    contractors = None
    if contractor_trades:
        c_lat = body.lat or 43.6532
        c_lng = body.lng or -79.3832
        contractors = await _fetch_contractors(contractor_trades, c_lat, c_lng)

    return AssistantChatResponse(
        message=message,
        proposed_action=proposed_action,
        model_update=model_update,
        contractors=contractors or None,
    )


@router.post("/assistant/parse-infra-model", response_model=InfraModelParseResponse, status_code=status.HTTP_200_OK)
async def parse_infra_model(body: InfraModelParseRequest) -> InfraModelParseResponse:
    """Parse a natural-language infrastructure description into model parameters."""
    if not settings.AI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI assistant is not configured on the server",
        )

    provider = get_ai_provider()
    current = body.current_params or {}

    if body.asset_type == "pipeline":
        prompt = f"""Extract pipeline parameters from this description. Return a JSON object with exactly these fields:
- pipe_type (string): one of water_main | sanitary_sewer | storm_sewer | gas_line
- material (string): one of PVC | HDPE | DI | CSP | RCP
- diameter_mm (float): pipe diameter in millimetres
- depth_m (float): burial depth in metres
- slope_pct (float): pipe slope as percentage

Current parameters (baseline for unspecified values):
{json.dumps(current)}

Description: "{body.text}"

Return only valid JSON, no explanation."""
    else:
        prompt = f"""Extract bridge parameters from this description. Return a JSON object with exactly these fields:
- bridge_type (string): one of road_bridge | pedestrian_bridge | culvert
- structure_type (string): one of steel_beam | concrete_slab | concrete_girder | steel_truss | arch | box_culvert
- span_m (float): bridge span in metres
- deck_width_m (float): deck width in metres
- clearance_m (float): vertical clearance in metres

Current parameters (baseline for unspecified values):
{json.dumps(current)}

Description: "{body.text}"

Return only valid JSON, no explanation."""

    try:
        raw = await provider.generate(prompt=prompt, max_tokens=400)
        content = raw.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content.strip())

        return InfraModelParseResponse(
            asset_type=body.asset_type,
            params=data,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Infrastructure model parsing failed: {exc}",
        ) from exc
