import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None = None
    status: str
    map_state: dict | None = None
    created_at: datetime
    updated_at: datetime
    parcel_count: int = 0
    plan_count: int = 0
    note_count: int = 0
    conversation_count: int = 0
    upload_count: int = 0

    model_config = {"from_attributes": True}


class AddParcelRequest(BaseModel):
    parcel_id: uuid.UUID
    role: str = "primary"


# ─── Notes ───

class NoteCreate(BaseModel):
    content: str = Field(min_length=1)


class NoteUpdate(BaseModel):
    content: str | None = None
    pinned: bool | None = None


class NoteResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    content: str
    pinned: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Conversations ───

class ConversationCreate(BaseModel):
    title: str | None = None
    messages: list[dict] = Field(default_factory=list)


class ConversationUpdate(BaseModel):
    title: str | None = None
    messages: list[dict] | None = None


class ConversationSummary(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    messages: list[dict]
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Map State ───

class MapStateUpdate(BaseModel):
    center: list[float] | None = None
    zoom: float | None = None
    selected_parcel_ids: list[uuid.UUID] | None = None
    infra_layers: list[str] | None = None


# ─── Scenarios ───

class ScenarioCreate(BaseModel):
    scenario_type: str = Field(default="base", pattern="^(base|variance|what_if)$")
    parent_scenario_id: uuid.UUID | None = None
    snapshot_manifest_id: uuid.UUID | None = None
    parameters: dict | None = None


class ScenarioResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    parent_scenario_id: uuid.UUID | None = None
    scenario_type: str
    status: str
    input_hash: str
    label: str | None = None
    snapshot_manifest_id: uuid.UUID | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
