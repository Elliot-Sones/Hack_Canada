import json
import re

from fastapi import APIRouter, HTTPException, status

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
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse, ModelParseRequest, ModelParseResponse, ModelUpdate, ProposedAction
from app.services.zoning_parser import extract_zone_category

router = APIRouter()

_ACTION_RE = re.compile(r"<!--ACTION:(.*?)-->", re.DOTALL)
_MODEL_RE = re.compile(r"<!--MODEL:(.*?)-->", re.DOTALL)

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

## Ontario Planning Law Reference
{_POLICY_CONTEXT}

## Two modes

**Answering mode** (default): Answer the user's question using the policy reference above and the parcel context provided. Be precise — cite by-law sections and specific numbers. Distinguish as-of-right permissions from what needs approval. If information is uncertain or missing, say so.

**Generation mode**: When the user explicitly asks you to generate a planning document (planning rationale, compliance matrix, variance justification, precedent report, or full submission package), OR when you determine that generating a document is the most useful response to their question, propose it.

To propose generation, append this marker on its own line at the very end of your response:
<!--ACTION:{{"label":"Generate [Document Name]","query":"[complete query describing exactly what to generate and for which site]"}}-->

Examples of when to propose generation:
- "Write a planning rationale for a 4-storey multiplex at 192 Jarvis" → answer briefly then propose
- "Generate the submission package" → propose it
- "Can I build a garden suite here?" → answer the question, do NOT propose generation
- "What's the FSI limit?" → answer the question, do NOT propose generation

Only propose generation when a formal document is genuinely what the user wants. Never propose generation for informational questions.

## Rules
- Keep answers concise and grounded — 2–4 short paragraphs maximum for most questions
- Cite by-law sections (e.g. "§10.5.10.20 of By-law 569-2013") and policy clauses when confident
- Distinguish as-of-right from what needs a variance or higher approval
- Never fabricate data — if parcel data is not provided, say so clearly
- Plain text only, no markdown headers in responses
"""


def _parse_response(raw: str, zone_constraints: dict | None = None, zone_code: str | None = None) -> tuple[str, ProposedAction | None, ModelUpdate | None]:
    """Strip action/model markers from the response and parse them."""
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

    return text.strip(), action, model_update


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
async def chat_with_assistant(body: AssistantChatRequest) -> AssistantChatResponse:
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

    prompt_parts = []
    if body.parcel_context:
        prompt_parts.append(f"Current site context:\n{body.parcel_context.strip()}")

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

    # Include uploaded file context so the assistant can reference blueprints, plans, etc.
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
                # Include setbacks if present
                setback_info = []
                for key, label in [("setback_front_m", "front"), ("setback_rear_m", "rear"), ("setback_side_m", "side")]:
                    val = dimensions.get(key)
                    if val is not None:
                        setback_info.append(f"{label} {val}m")
                if setback_info:
                    parts.append(f"  Setbacks: {', '.join(setback_info)}")
                # Include any raw text/notes
                notes = item.extracted_data.get("notes") or item.extracted_data.get("description")
                if notes:
                    parts.append(f"  Notes: {notes}")
            upload_lines.append("\n".join(parts))
        prompt_parts.append("Uploaded project files (user-provided documents — use this data when answering):\n" + "\n\n".join(upload_lines))

    prompt_parts.append("Conversation:\n" + "\n\n".join(transcript_lines))
    prompt_parts.append("Respond to the latest user message.")

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

    message, proposed_action, model_update = _parse_response(
        response.content, zone_constraints, zone_label
    )
    return AssistantChatResponse(message=message, proposed_action=proposed_action, model_update=model_update)
