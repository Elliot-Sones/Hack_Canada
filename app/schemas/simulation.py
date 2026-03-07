import uuid
from datetime import datetime

from pydantic import BaseModel


class MassingRequest(BaseModel):
    template_id: uuid.UUID | None = None
    parameters: dict | None = None


class MassingResponse(BaseModel):
    id: uuid.UUID
    scenario_run_id: uuid.UUID
    template_id: uuid.UUID | None = None
    summary_json: dict | None = None
    compliance_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LayoutRunRequest(BaseModel):
    unit_types: list[uuid.UUID] | None = None
    optimization_objective: str = "maximize_revenue"
    parameters: dict | None = None


class LayoutRunResponse(BaseModel):
    id: uuid.UUID
    massing_id: uuid.UUID
    status: str
    objective: str | None = None
    result_json: dict | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
