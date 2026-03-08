import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.models.geospatial import Parcel, ParcelZoningAssignment
from app.models.entitlement import DevelopmentApplication
from app.models.finance import FinancialAssumptionSet, MarketComparable
from app.schemas.geospatial import (
    NearbyApplicationsResponse,
    ParcelDetailResponse,
    ParcelOverlaysResponse,
    ParcelResponse,
    ParcelSearchParams,
    PolicyStackResponse,
    ZoningAnalysisResponse,
    ZoningComponentsResponse,
    ZoningConstraintResponse,
    ZoningStandardsResponse,
)
from app.services.geospatial import build_parcel_search_statement, get_active_parcel_by_id, list_active_snapshot_ids
from app.services.overlay_service import get_parcel_overlays_response
from app.services.policy_stack import get_policy_stack_response
from app.services.zoning_service import ZoningAnalysis, build_zoning_analysis

router = APIRouter()


def _serialize_zoning_analysis(analysis: ZoningAnalysis) -> ZoningAnalysisResponse:
    components = None
    if analysis.components is not None:
        components = ZoningComponentsResponse(
            raw=analysis.components.raw,
            category=analysis.components.category,
            density=analysis.components.density,
            commercial_density=analysis.components.commercial_density,
            residential_density=analysis.components.residential_density,
            height_suffix=analysis.components.height_suffix,
            exception_number=analysis.components.exception_number,
        )

    standards = None
    if analysis.standards is not None:
        standards = ZoningStandardsResponse(
            category=analysis.standards.category,
            label=analysis.standards.label,
            permitted_uses=list(analysis.standards.permitted_uses),
            max_height_m=analysis.standards.max_height_m,
            max_storeys=analysis.standards.max_storeys,
            max_fsi=analysis.standards.max_fsi,
            min_front_setback_m=analysis.standards.min_front_setback_m,
            min_rear_setback_m=analysis.standards.min_rear_setback_m,
            min_interior_side_setback_m=analysis.standards.min_interior_side_setback_m,
            min_exterior_side_setback_m=analysis.standards.min_exterior_side_setback_m,
            max_lot_coverage_pct=analysis.standards.max_lot_coverage_pct,
            min_landscaping_pct=analysis.standards.min_landscaping_pct,
            bylaw_section=analysis.standards.bylaw_section,
            exception_number=analysis.standards.exception_number,
            has_site_specific_height=analysis.standards.has_site_specific_height,
            commercial_fsi=analysis.standards.commercial_fsi,
            residential_fsi=analysis.standards.residential_fsi,
        )

    return ZoningAnalysisResponse(
        parcel_id=analysis.parcel_id,
        address=analysis.address,
        zone_string=analysis.zone_string,
        components=components,
        standards=standards,
        parking_policy_area=analysis.parking_policy_area,
        parking_standards=dict(analysis.parking_standards),
        bicycle_parking=dict(analysis.bicycle_parking),
        amenity_space=dict(analysis.amenity_space),
        overlay_constraints=[
            ZoningConstraintResponse(
                layer_type=constraint.get("layer_type"),
                layer_name=constraint.get("layer_name"),
                impact=constraint.get("impact"),
                affects=list(constraint.get("affects", [])),
            )
            for constraint in analysis.overlay_constraints
        ],
        warnings=list(analysis.warnings),
    )


async def _get_active_zoning_assignment_count(
    db: AsyncSession,
    parcel_id: uuid.UUID,
    active_zoning_snapshot_ids: list[uuid.UUID],
) -> int | None:
    if not active_zoning_snapshot_ids:
        return None

    return await db.scalar(
        select(func.count())
        .select_from(ParcelZoningAssignment)
        .where(ParcelZoningAssignment.parcel_id == parcel_id)
        .where(ParcelZoningAssignment.source_snapshot_id.in_(list(active_zoning_snapshot_ids)))
    )


@router.get("/parcels/search", response_model=list[ParcelResponse])
async def search_parcels(
    params: ParcelSearchParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        _ = params.bbox_bounds
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    active_snapshot_ids = await list_active_snapshot_ids(db, "parcel_base")
    query = build_parcel_search_statement(params, active_snapshot_ids=active_snapshot_ids)
    
    import json
    
    query = query.add_columns(func.ST_AsGeoJSON(Parcel.geom).label("geom_json"))
    result = await db.execute(query)
    
    response = []
    for parcel, geom_json in result:
        p_dict = {
            "id": parcel.id,
            "jurisdiction_id": parcel.jurisdiction_id,
            "pin": parcel.pin,
            "address": parcel.address,
            "lot_area_m2": parcel.lot_area_m2,
            "lot_frontage_m": parcel.lot_frontage_m,
            "zone_code": parcel.zone_code,
            "current_use": parcel.current_use,
            "geom": json.loads(geom_json) if geom_json else None
        }
        response.append(p_dict)
    return response


@router.get("/parcels/{parcel_id}", response_model=ParcelDetailResponse)
async def get_parcel(
    parcel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    active_snapshot_ids = await list_active_snapshot_ids(db, "parcel_base")
    import json
    
    query = select(Parcel, func.ST_AsGeoJSON(Parcel.geom).label("geom_json")).where(Parcel.id == parcel_id)
    if active_snapshot_ids:
        query = query.where(Parcel.source_snapshot_id.in_(list(active_snapshot_ids)))
        
    result = await db.execute(query)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Parcel not found")
        
    parcel, geom_json = row
    p_dict = {
        "id": parcel.id,
        "jurisdiction_id": parcel.jurisdiction_id,
        "pin": parcel.pin,
        "address": parcel.address,
        "lot_area_m2": parcel.lot_area_m2,
        "lot_frontage_m": parcel.lot_frontage_m,
        "zone_code": parcel.zone_code,
        "current_use": parcel.current_use,
        "lot_depth_m": parcel.lot_depth_m,
        "assessed_value": parcel.assessed_value,
        "created_at": parcel.created_at,
        "geom": json.loads(geom_json) if geom_json else None
    }
    return p_dict


@router.get("/parcels/{parcel_id}/zoning-analysis", response_model=ZoningAnalysisResponse)
async def get_parcel_zoning_analysis(
    parcel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    active_snapshot_ids = await list_active_snapshot_ids(db, "parcel_base")
    active_zoning_snapshot_ids = await list_active_snapshot_ids(db, "zoning_geometry")
    parcel = await get_active_parcel_by_id(db, parcel_id, active_snapshot_ids=active_snapshot_ids)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    overlay_response = await get_parcel_overlays_response(db, parcel)
    zoning_assignment_count = await _get_active_zoning_assignment_count(db, parcel.id, active_zoning_snapshot_ids)
    analysis = build_zoning_analysis(
        parcel,
        overlay_data=[overlay.model_dump() for overlay in overlay_response.overlays],
        zoning_assignment_count=zoning_assignment_count,
    )
    return _serialize_zoning_analysis(analysis)


@router.get("/parcels/{parcel_id}/policy-stack", response_model=PolicyStackResponse)
async def get_parcel_policy_stack(
    parcel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    active_snapshot_ids = await list_active_snapshot_ids(db, "parcel_base")
    parcel = await get_active_parcel_by_id(db, parcel_id, active_snapshot_ids=active_snapshot_ids)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return await get_policy_stack_response(db, parcel)


@router.get("/parcels/{parcel_id}/overlays", response_model=ParcelOverlaysResponse)
async def get_parcel_overlays(
    parcel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    active_snapshot_ids = await list_active_snapshot_ids(db, "parcel_base")
    parcel = await get_active_parcel_by_id(db, parcel_id, active_snapshot_ids=active_snapshot_ids)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return await get_parcel_overlays_response(db, parcel)


@router.get("/parcels/{parcel_id}/nearby-applications", response_model=NearbyApplicationsResponse)
async def get_nearby_applications(
    parcel_id: uuid.UUID,
    radius_m: float = 2000,
    limit: int = 20,
    db: AsyncSession = Depends(get_db_session),
):
    active_snapshot_ids = await list_active_snapshot_ids(db, "parcel_base")
    parcel = await get_active_parcel_by_id(db, parcel_id, active_snapshot_ids=active_snapshot_ids)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    radius_m = min(radius_m, 5000)
    limit = min(limit, 50)

    parcel_geom_subq = (
        select(func.ST_Transform(Parcel.geom, 2952))
        .where(Parcel.id == parcel_id)
        .scalar_subquery()
    )

    query = (
        select(
            DevelopmentApplication,
            func.ST_Distance(
                func.ST_Transform(DevelopmentApplication.geom, 2952),
                parcel_geom_subq,
            ).label("distance_m"),
        )
        .where(DevelopmentApplication.jurisdiction_id == parcel.jurisdiction_id)
        .where(DevelopmentApplication.geom.isnot(None))
        .where(
            func.ST_DWithin(
                func.ST_Transform(DevelopmentApplication.geom, 2952),
                parcel_geom_subq,
                radius_m,
            )
        )
        .order_by("distance_m")
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    applications = []
    for app, dist in rows:
        applications.append({
            "id": app.id,
            "app_number": app.app_number,
            "address": app.address,
            "app_type": app.app_type,
            "status": app.status,
            "decision": app.decision,
            "proposed_height_m": app.proposed_height_m,
            "proposed_units": app.proposed_units,
            "distance_m": round(dist, 1) if dist is not None else None,
        })

    return NearbyApplicationsResponse(
        parcel_id=parcel_id,
        applications=applications,
        total=len(applications),
    )


@router.get("/parcels/{parcel_id}/financial-summary")
async def get_parcel_financial_summary(
    parcel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """Quick financial feasibility snapshot for a parcel — no scenario required."""
    active_snapshot_ids = await list_active_snapshot_ids(db, "parcel_base")
    parcel = await get_active_parcel_by_id(db, parcel_id, active_snapshot_ids=active_snapshot_ids)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    # Get default assumption sets
    result = await db.execute(
        select(FinancialAssumptionSet)
        .where(FinancialAssumptionSet.organization_id.is_(None))
        .where(FinancialAssumptionSet.is_default.is_(True))
        .order_by(FinancialAssumptionSet.name)
    )
    assumption_sets = result.scalars().all()

    # Get nearby market comps (within 3km)
    nearby_comps = []
    if parcel.geom is not None:
        parcel_geom_subq = (
            select(func.ST_Transform(Parcel.geom, 2952))
            .where(Parcel.id == parcel_id)
            .scalar_subquery()
        )
        comp_query = (
            select(
                MarketComparable,
                func.ST_Distance(
                    func.ST_Transform(MarketComparable.geom, 2952),
                    parcel_geom_subq,
                ).label("distance_m"),
            )
            .where(MarketComparable.jurisdiction_id == parcel.jurisdiction_id)
            .where(MarketComparable.geom.isnot(None))
            .where(
                func.ST_DWithin(
                    func.ST_Transform(MarketComparable.geom, 2952),
                    parcel_geom_subq,
                    3000,
                )
            )
            .order_by("distance_m")
            .limit(10)
        )
        comp_result = await db.execute(comp_query)
        for comp, dist in comp_result.all():
            nearby_comps.append({
                "comp_type": comp.comp_type,
                "address": comp.address,
                "distance_m": round(dist, 0) if dist else None,
                "attributes": comp.attributes_json,
                "effective_date": str(comp.effective_date) if comp.effective_date else None,
            })

    # Build quick estimate based on zone standards
    from app.services.zoning_service import build_zoning_analysis
    from app.services.overlay_service import get_parcel_overlays_response

    overlay_response = await get_parcel_overlays_response(db, parcel)
    active_zoning_snapshot_ids = await list_active_snapshot_ids(db, "zoning_geometry")
    zoning_assignment_count = await _get_active_zoning_assignment_count(db, parcel.id, active_zoning_snapshot_ids)
    zoning = build_zoning_analysis(
        parcel,
        overlay_data=[o.model_dump() for o in overlay_response.overlays],
        zoning_assignment_count=zoning_assignment_count,
    )

    lot_area = parcel.lot_area_m2 or parcel.geom_area_m2 or 0
    max_fsi = zoning.standards.max_fsi if zoning.standards and zoning.standards.max_fsi else None
    max_height = zoning.standards.max_height_m if zoning.standards else None
    max_storeys = zoning.standards.max_storeys if zoning.standards else None

    # Build feasibility estimate
    estimated_gfa = lot_area * max_fsi if max_fsi and lot_area else None
    rental_assumptions = next((a for a in assumption_sets if a.assumptions_json.get("tenure") == "rental"), None)
    condo_assumptions = next((a for a in assumption_sets if a.assumptions_json.get("tenure") == "condo"), None)

    estimates = {}
    for label, assumptions in [("rental", rental_assumptions), ("condo", condo_assumptions)]:
        if not assumptions or not estimated_gfa:
            continue
        aj = assumptions.assumptions_json
        cost_aj = aj.get("cost_assumptions", {})
        hard_cost_m2 = cost_aj.get("hard_cost_per_m2", 4300)
        soft_pct = cost_aj.get("soft_cost_pct", 0.22)
        contingency_pct = aj.get("contingency", {}).get("construction_contingency_pct", 0.05)

        hard_cost = estimated_gfa * hard_cost_m2
        soft_cost = hard_cost * soft_pct
        contingency = (hard_cost + soft_cost) * contingency_pct
        total_cost = hard_cost + soft_cost + contingency

        # Average revenue per m²
        rev_aj = aj.get("revenue_assumptions", {})
        if label == "rental":
            rents = rev_aj.get("rent_psf_monthly_by_unit_type", {})
            avg_rent_psf = sum(rents.values()) / len(rents) if rents else 4.0
            avg_rent_m2_annual = avg_rent_psf * 10.7639 * 12
            gla = estimated_gfa * 0.82
            revenue = gla * avg_rent_m2_annual
            vacancy = aj.get("vacancy_and_absorption", {}).get("vacancy_rate", 0.035)
            revenue *= (1 - vacancy)
            opex_ratio = aj.get("vacancy_and_absorption", {}).get("opex_ratio", 0.28)
            noi = revenue * (1 - opex_ratio)
            cap_rate = aj.get("valuation", {}).get("cap_rate", 0.0475)
            valuation = noi / cap_rate if cap_rate else revenue
        else:
            sales = rev_aj.get("sale_psf_by_unit_type", {})
            avg_sale_psf = sum(sales.values()) / len(sales) if sales else 1350
            avg_sale_m2 = avg_sale_psf * 10.7639
            gla = estimated_gfa * 0.82
            revenue = gla * avg_sale_m2
            sales_cost = revenue * rev_aj.get("sales_cost_pct", 0.04)
            revenue -= sales_cost
            noi = None
            valuation = revenue

        residual = valuation - total_cost

        estimates[label] = {
            "estimated_gfa_m2": round(estimated_gfa, 0),
            "estimated_gla_m2": round(gla, 0),
            "total_cost": round(total_cost, 0),
            "hard_cost": round(hard_cost, 0),
            "soft_cost": round(soft_cost, 0),
            "revenue": round(revenue, 0),
            "noi": round(noi, 0) if noi else None,
            "valuation": round(valuation, 0),
            "residual_land_value": round(residual, 0),
            "assumption_set": assumptions.name,
        }

    return {
        "parcel_id": str(parcel_id),
        "address": parcel.address,
        "zone_code": parcel.zone_code,
        "lot_area_m2": lot_area,
        "assessed_value": float(parcel.assessed_value) if parcel.assessed_value else None,
        "max_fsi": max_fsi,
        "max_height_m": max_height,
        "max_storeys": max_storeys,
        "estimated_gfa_m2": round(estimated_gfa, 0) if estimated_gfa else None,
        "estimates": estimates,
        "nearby_comps": nearby_comps,
        "assumption_sets": [
            {"id": str(a.id), "name": a.name, "tenure": a.assumptions_json.get("tenure")}
            for a in assumption_sets
        ],
    }
