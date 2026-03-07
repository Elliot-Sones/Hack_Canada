from fastapi import APIRouter, HTTPException, status

from app.ai.factory import get_ai_provider
from app.config import settings
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse

router = APIRouter()

SYSTEM_PROMPT = """You are an expert land-development due-diligence assistant for the City of Toronto.
You help development analysts, planners, and architects understand zoning regulations,
building policies, setback requirements, height limits, floor space index (FSI),
permitted uses, development potential, and entitlement pathways.

Rules:
- Keep answers grounded and concise.
- Use plain text only.
- Cite by-law sections when you are confident in them.
- Distinguish as-of-right permissions from anything that likely needs a variance.
- If information is uncertain or missing, say so clearly.
"""


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
        prompt_parts.append(f"Parcel context:\n{body.parcel_context.strip()}")
    prompt_parts.append("Conversation:\n" + "\n\n".join(transcript_lines))
    prompt_parts.append("Respond to the latest user message.")

    try:
        response = await provider.generate(
            prompt="\n\n".join(prompt_parts),
            system=SYSTEM_PROMPT,
            max_tokens=1024,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Assistant generation failed: {exc}",
        ) from exc

    return AssistantChatResponse(message=response.content.strip())
