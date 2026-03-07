from typing import Literal

from pydantic import BaseModel, Field


class AssistantChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=4000)


class AssistantChatRequest(BaseModel):
    messages: list[AssistantChatMessage] = Field(min_length=1, max_length=20)
    parcel_context: str | None = Field(default=None, max_length=2000)


class ProposedAction(BaseModel):
    label: str
    query: str


class AssistantChatResponse(BaseModel):
    message: str
    proposed_action: ProposedAction | None = None
