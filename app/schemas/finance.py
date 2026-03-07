import uuid
from datetime import datetime

from pydantic import BaseModel


class FinancialRunRequest(BaseModel):
    assumption_set_id: uuid.UUID | None = None
    parameters: dict | None = None


class FinancialRunResponse(BaseModel):
    id: uuid.UUID
    scenario_run_id: uuid.UUID
    assumption_set_id: uuid.UUID | None = None
    status: str
    output_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
