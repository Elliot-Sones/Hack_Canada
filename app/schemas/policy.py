import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PolicySearchParams(BaseModel):
    query: str | None = None
    jurisdiction_id: uuid.UUID | None = None
    doc_type: str | None = None
    normalized_type: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PolicyClauseResponse(BaseModel):
    id: uuid.UUID
    section_ref: str | None = None
    page_ref: str | None = None
    raw_text: str
    normalized_type: str | None = None
    normalized_json: dict | None = None
    confidence: float | None = None
    source_document_title: str | None = None

    model_config = {"from_attributes": True}


class PolicySearchResponse(BaseModel):
    clauses: list[PolicyClauseResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
