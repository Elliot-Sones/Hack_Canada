import uuid
from datetime import datetime

from pydantic import BaseModel


class EntitlementRunRequest(BaseModel):
    parameters: dict | None = None


class EntitlementRunResponse(BaseModel):
    id: uuid.UUID
    scenario_run_id: uuid.UUID
    overall_compliance: str
    result_json: dict | None = None
    score: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PrecedentSearchRequest(BaseModel):
    search_params: dict | None = None
    radius_m: float | None = 500.0
    max_results: int = 20


class PrecedentSearchResponse(BaseModel):
    id: uuid.UUID
    scenario_run_id: uuid.UUID
    search_params_json: dict | None = None
    result_count: int = 0
    results_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
