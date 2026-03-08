import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class ParcelSearchParams(BaseModel):
    address: str | None = None
    pin: str | None = None
    zoning_code: str | None = None
    min_lot_area: float | None = None
    max_lot_area: float | None = None
    min_frontage: float | None = None
    bbox: str | None = Field(None, description="Bounding box as 'minx,miny,maxx,maxy'")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def bbox_bounds(self) -> tuple[float, float, float, float] | None:
        if self.bbox is None:
            return None

        parts = [part.strip() for part in self.bbox.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox must be formatted as 'minx,miny,maxx,maxy'")

        try:
            minx, miny, maxx, maxy = (float(part) for part in parts)
        except ValueError as exc:
            raise ValueError("bbox values must be numeric") from exc

        if minx >= maxx or miny >= maxy:
            raise ValueError("bbox min values must be smaller than max values")

        return minx, miny, maxx, maxy


class ParcelResponse(BaseModel):
    id: uuid.UUID
    jurisdiction_id: uuid.UUID
    pin: str | None = None
    address: str | None = None
    lot_area_m2: float | None = None
    lot_frontage_m: float | None = None
    zone_code: str | None = None
    current_use: str | None = None
    geom: dict | None = None

    model_config = {"from_attributes": True}


class ParcelDetailResponse(ParcelResponse):
    lot_depth_m: float | None = None
    assessed_value: float | None = None
    created_at: datetime | None = None


class SnapshotReferenceResponse(BaseModel):
    id: uuid.UUID | None = None
    snapshot_type: str | None = None
    version_label: str | None = None
    published_at: datetime | None = None


class PolicyCitationResponse(BaseModel):
    clause_id: uuid.UUID
    document_title: str
    doc_type: str
    section_ref: str
    page_ref: str | None = None
    source_url: str | None = None
    effective_date: date | None = None


class PolicyEntryResponse(BaseModel):
    clause_id: uuid.UUID
    policy_version_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    doc_type: str
    override_level: int
    section_ref: str
    page_ref: str | None = None
    raw_text: str
    normalized_type: str
    normalized_json: dict
    applicability_json: dict
    confidence: float
    effective_date: date | None = None
    source_url: str | None = None
    snapshot: SnapshotReferenceResponse | None = None


class PolicyStackResponse(BaseModel):
    parcel_id: uuid.UUID
    applicable_policies: list[PolicyEntryResponse] = Field(default_factory=list)
    citations: list[PolicyCitationResponse] = Field(default_factory=list)
    snapshots: list[SnapshotReferenceResponse] = Field(default_factory=list)


class ParcelMetricResponse(BaseModel):
    metric_type: str
    metric_value: float
    unit: str


class OverlayFeatureResponse(BaseModel):
    feature_id: uuid.UUID
    layer_id: uuid.UUID
    layer_name: str
    layer_type: str
    relationship_type: str
    source_record_id: str | None = None
    source_url: str | None = None
    effective_date: date | None = None
    attributes_json: dict = Field(default_factory=dict)
    snapshot: SnapshotReferenceResponse | None = None


class ParcelOverlaysResponse(BaseModel):
    parcel_id: uuid.UUID
    overlays: list[OverlayFeatureResponse] = Field(default_factory=list)
    parcel_metrics: list[ParcelMetricResponse] = Field(default_factory=list)
    snapshots: list[SnapshotReferenceResponse] = Field(default_factory=list)


class NearbyApplicationResponse(BaseModel):
    id: uuid.UUID
    app_number: str
    address: str | None = None
    app_type: str | None = None
    status: str | None = None
    decision: str | None = None
    proposed_height_m: float | None = None
    proposed_units: int | None = None
    distance_m: float | None = None


class NearbyApplicationsResponse(BaseModel):
    parcel_id: uuid.UUID
    applications: list[NearbyApplicationResponse] = Field(default_factory=list)
    total: int = 0


class ZoningComponentsResponse(BaseModel):
    raw: str
    category: str
    density: float | None = None
    commercial_density: float | None = None
    residential_density: float | None = None
    height_suffix: str | None = None
    exception_number: int | None = None


class ZoningStandardsResponse(BaseModel):
    category: str
    label: str
    permitted_uses: list[str] = Field(default_factory=list)
    max_height_m: float | None = None
    max_storeys: int | None = None
    max_fsi: float | None = None
    min_front_setback_m: float
    min_rear_setback_m: float
    min_interior_side_setback_m: float
    min_exterior_side_setback_m: float
    max_lot_coverage_pct: float
    min_landscaping_pct: float
    bylaw_section: str
    exception_number: int | None = None
    has_site_specific_height: bool = False
    commercial_fsi: float | None = None
    residential_fsi: float | None = None


class ZoningConstraintResponse(BaseModel):
    layer_type: str | None = None
    layer_name: str | None = None
    impact: str | None = None
    affects: list[str] = Field(default_factory=list)


class ZoningAnalysisResponse(BaseModel):
    parcel_id: uuid.UUID
    address: str | None = None
    zone_string: str | None = None
    components: ZoningComponentsResponse | None = None
    standards: ZoningStandardsResponse | None = None
    parking_policy_area: str
    parking_standards: dict = Field(default_factory=dict)
    bicycle_parking: dict = Field(default_factory=dict)
    amenity_space: dict = Field(default_factory=dict)
    overlay_constraints: list[ZoningConstraintResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
