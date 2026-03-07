import structlog

from app.ai.base import AIProvider

logger = structlog.get_logger()

DEVELOPMENT_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "address": {"type": "string", "description": "Site address or location description"},
        "parcel_pin": {"type": "string", "description": "Parcel PIN if mentioned", "nullable": True},
        "project_name": {"type": "string", "description": "Suggested project name"},
        "development_type": {
            "type": "string",
            "enum": ["residential", "commercial", "mixed_use", "industrial", "institutional"],
        },
        "building_type": {
            "type": "string",
            "enum": ["tower", "midrise", "lowrise", "townhouse", "detached", "mixed"],
        },
        "storeys": {"type": "integer", "description": "Target number of storeys", "nullable": True},
        "height_m": {"type": "number", "description": "Target height in metres", "nullable": True},
        "gross_floor_area_sqm": {"type": "number", "description": "Target GFA in sqm", "nullable": True},
        "unit_count": {"type": "integer", "description": "Target number of units", "nullable": True},
        "ground_floor_use": {
            "type": "string",
            "enum": ["retail", "commercial", "residential", "lobby", "parking"],
            "nullable": True,
        },
        "unit_mix": {
            "type": "object",
            "properties": {
                "studio_pct": {"type": "number"},
                "one_bed_pct": {"type": "number"},
                "two_bed_pct": {"type": "number"},
                "three_bed_pct": {"type": "number"},
            },
            "nullable": True,
        },
        "parking_type": {"type": "string", "enum": ["underground", "surface", "structured", "none"], "nullable": True},
        "amenities": {"type": "array", "items": {"type": "string"}, "nullable": True},
        "policy_variances_requested": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rule_type": {"type": "string"},
                    "requested_value": {"type": "string"},
                    "justification": {"type": "string"},
                },
            },
            "nullable": True,
        },
        "special_considerations": {"type": "array", "items": {"type": "string"}, "nullable": True},
        "confidence": {
            "type": "number",
            "description": "How confident you are in the extraction (0.0-1.0)",
        },
        "clarification_needed": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Questions to ask the user for missing info",
        },
    },
    "required": ["address", "project_name", "development_type", "building_type", "confidence", "clarification_needed"],
}


SYSTEM_PROMPT = """You are a land development analyst in Toronto, Ontario.
Your job is to parse a user's natural language description of a proposed development into structured parameters.

Key context:
- Toronto uses Zoning By-law 569-2013
- Heights are in metres, areas in square metres
- Common zone codes: R (residential), C (commercial), CR (commercial-residential), E (employment)
- Typical Toronto tower: 25-70 storeys. Midrise: 5-11 storeys. Lowrise: 1-4 storeys
- If the user mentions "storeys" but not height, estimate 3.0m per storey (3.5m for ground floor retail)
- If info is missing, set nullable fields to null and add questions to clarification_needed
- Always extract what you can and flag what's ambiguous

Be precise. Do not invent information the user didn't provide."""


async def parse_development_query(provider: AIProvider, query: str) -> dict:
    """Parse a natural language development query into structured parameters."""
    logger.info("query_parser.parsing", query_length=len(query))

    result = await provider.generate_structured(
        prompt=f"Parse this development proposal into structured parameters:\n\n{query}",
        schema=DEVELOPMENT_PARAMS_SCHEMA,
        system=SYSTEM_PROMPT,
    )

    logger.info(
        "query_parser.parsed",
        address=result.get("address"),
        dev_type=result.get("development_type"),
        confidence=result.get("confidence"),
        clarifications=len(result.get("clarification_needed", [])),
    )

    return result
