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
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse, ProposedAction

router = APIRouter()

_ACTION_RE = re.compile(r"<!--ACTION:(.*?)-->", re.DOTALL)

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


def _parse_response(raw: str) -> tuple[str, ProposedAction | None]:
    """Strip the action marker from the response and parse it."""
    match = _ACTION_RE.search(raw)
    if not match:
        return raw.strip(), None

    message = _ACTION_RE.sub("", raw).strip()
    try:
        data = json.loads(match.group(1))
        action = ProposedAction(
            label=data.get("label", "Generate Document"),
            query=data.get("query", ""),
        )
    except (json.JSONDecodeError, KeyError):
        action = None

    return message, action


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

    message, proposed_action = _parse_response(response.content)
    return AssistantChatResponse(message=message, proposed_action=proposed_action)
