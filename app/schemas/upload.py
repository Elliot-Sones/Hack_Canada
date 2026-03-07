import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    status: str
    original_filename: str
    content_type: str
    file_size_bytes: int
    location: str = Field(description="URL to poll for upload status")


class UploadDetail(BaseModel):
    id: uuid.UUID
    original_filename: str
    content_type: str
    file_size_bytes: int
    status: str
    doc_category: str | None = None
    page_count: int | None = None
    extracted_data: dict | None = None
    compliance_findings: dict | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
    error_message: str | None = None
    page_classifications: dict | None = None
    floor_plan_data: dict | None = None
    plan_id: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UploadListItem(BaseModel):
    id: uuid.UUID
    original_filename: str
    content_type: str
    file_size_bytes: int
    status: str
    doc_category: str | None = None
    page_count: int | None = None
    created_at: datetime | None = None


class PageDetail(BaseModel):
    page_number: int
    url: str
    width_px: int | None = None
    height_px: int | None = None
    extracted_text: str | None = None


class GeneratePlanFromUploadRequest(BaseModel):
    project_name: str | None = None


class GenerateResponseRequest(BaseModel):
    response_type: str = Field(
        default="correction_response",
        description="Type of response document to generate: correction_response, compliance_review_report, variance_justification",
    )
