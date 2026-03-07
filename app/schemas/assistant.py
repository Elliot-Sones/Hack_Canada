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


class ModelParseRequest(BaseModel):
    text: str
    current_params: dict | None = None
    zone_code: str | None = None
    lot_area_m2: float | None = None


class ModelParseResponse(BaseModel):
    storeys: int
    podium_storeys: int
    height_m: float
    setback_m: float
    typology: str
    footprint_coverage: float
    unit_width: float | None = None
    tower_shape: str | None = None
    warnings: list[str] | None = None
