"""AI document analysis using Claude vision API."""

from __future__ import annotations

import base64
import json

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()

_EXTRACTION_SYSTEM_PROMPT = """\
You are an expert architectural plan analyst specializing in Ontario (Canada) land development.
Analyze the provided architectural drawings or documents and extract structured data.

Return a JSON object with the following structure (include only fields you can confidently extract):
{
  "dimensions": {
    "lot_area_m2": number or null,
    "lot_frontage_m": number or null,
    "lot_depth_m": number or null,
    "setback_front_m": number or null,
    "setback_rear_m": number or null,
    "setback_side_m": number or null
  },
  "building": {
    "storeys": number or null,
    "height_m": number or null,
    "unit_count": number or null,
    "gfa_m2": number or null,
    "building_type": string or null,
    "footprint_m2": number or null
  },
  "unit_mix": {
    "studio": {"count": number, "avg_area_m2": number},
    "one_bed": {"count": number, "avg_area_m2": number},
    "two_bed": {"count": number, "avg_area_m2": number},
    "three_bed": {"count": number, "avg_area_m2": number}
  },
  "site_features": {
    "parking_spaces": number or null,
    "parking_type": string or null,
    "access_points": string or null,
    "landscaping_pct": number or null
  },
  "address": string or null,
  "project_name": string or null,
  "labels_and_notes": [string],
  "document_type": string
}

Only include data you can actually see in the drawings. Use metric units.
If a value is unclear, set it to null rather than guessing.
Return ONLY valid JSON, no markdown fencing."""

_COMPLIANCE_SYSTEM_PROMPT = """\
You are an expert Ontario land-use planning consultant reviewing architectural plans for compliance
with the City of Toronto Zoning By-law 569-2013 and the Ontario Building Code.

Analyze the provided drawings and extracted data against applicable codes.
Return a JSON object with:
{
  "issues": [
    {
      "category": "setback|height|density|parking|unit_mix|accessibility|other",
      "severity": "critical|major|minor|info",
      "description": "What the issue is",
      "code_reference": "By-law section or code reference",
      "suggestion": "How to resolve it"
    }
  ],
  "auto_fixable": ["list of issues that can be resolved with simple changes"],
  "requires_professional": ["list of issues needing engineer/architect input"],
  "overall_assessment": "1-2 paragraph summary of compliance status"
}

Be specific about code references. Only cite provisions you are confident about.
Return ONLY valid JSON, no markdown fencing."""


async def _call_claude_vision(
    system_prompt: str,
    page_images: list[bytes],
    user_text: str = "Analyze the provided document pages.",
) -> dict:
    """Send images to Claude vision API and parse JSON response."""
    content_blocks = []
    for img_bytes in page_images:
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        content_blocks.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": b64},
        })
    content_blocks.append({"type": "text", "text": user_text})

    model = settings.AI_MODEL or "claude-sonnet-4-5-20250514"
    payload = {
        "model": model,
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [{"role": "user", "content": content_blocks}],
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.AI_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()

    result = resp.json()
    text = ""
    for block in result.get("content", []):
        if block.get("type") == "text":
            text += block["text"]

    # Strip markdown fencing if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("document_analyzer.json_parse_failed", raw_text=text[:500])
        return {"raw_response": text, "parse_error": True}


async def extract_plan_data(page_images: list[bytes], doc_category: str) -> dict:
    """Send page images to Claude vision API, extract structured data."""
    user_text = (
        f"This is a {doc_category.replace('_', ' ')}. "
        "Extract all measurable data, dimensions, unit counts, areas, and labels visible in these pages."
    )
    return await _call_claude_vision(_EXTRACTION_SYSTEM_PROMPT, page_images, user_text)


async def review_compliance(
    page_images: list[bytes],
    extracted_data: dict,
    zoning_rules: dict | None = None,
) -> dict:
    """AI reviews the plan against applicable codes."""
    context_parts = ["Review these architectural plans for compliance."]
    if extracted_data:
        context_parts.append(f"Previously extracted data: {json.dumps(extracted_data, default=str)}")
    if zoning_rules:
        context_parts.append(f"Applicable zoning rules: {json.dumps(zoning_rules, default=str)}")

    return await _call_claude_vision(_COMPLIANCE_SYSTEM_PROMPT, page_images, "\n\n".join(context_parts))
