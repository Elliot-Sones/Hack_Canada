"""OBC interior compliance checking API endpoints."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.interior_compliance import check_interior_compliance

router = APIRouter(prefix="/compliance")


class InteriorComplianceRequest(BaseModel):
    floor_plan: dict = Field(..., description="Floor plan with rooms, openings, exits")
    ceiling_height_m: float = Field(default=2.7, description="Ceiling height in metres")
    original_floor_plan: dict | None = Field(default=None, description="Original floor plan for load-bearing wall detection")


@router.post("/interior")
def check_interior(body: InteriorComplianceRequest):
    """Run OBC interior compliance checks on a floor plan.

    Returns deterministic compliance results — no AI involved.
    """
    result = check_interior_compliance(
        floor_plan=body.floor_plan,
        ceiling_height_m=body.ceiling_height_m,
        original_floor_plan=body.original_floor_plan,
    )
    return {
        "rules": [asdict(r) for r in result.rules],
        "errors": result.errors,
        "warnings": result.warnings,
        "overall_compliant": result.overall_compliant,
        "load_bearing_warnings": result.load_bearing_warnings,
    }
