"""Pydantic schemas for design version control."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BranchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    from_version_id: uuid.UUID | None = None


class BranchResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    created_by: uuid.UUID
    created_at: datetime


class CommitRequest(BaseModel):
    floor_plans: dict | None = None
    model_params: dict | None = None
    message: str = Field(min_length=1, max_length=500)
    parcel_id: uuid.UUID | None = None


class VersionResponse(BaseModel):
    id: uuid.UUID
    branch_id: uuid.UUID
    version_number: int
    floor_plans: dict | None = None
    model_params: dict | None = None
    compliance_status: str
    compliance_details: dict | None = None
    variance_items: list | None = None
    blocking_issues: list | None = None
    message: str
    change_summary: str | None = None
    created_by: uuid.UUID
    created_at: datetime
