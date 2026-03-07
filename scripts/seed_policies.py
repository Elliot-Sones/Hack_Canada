"""Seed Toronto policy documents via raw SQL.

Usage:
    python3 scripts/seed_policies.py
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from app.database import sync_engine

DOCUMENTS = [
    {
        "doc_type": "zoning_bylaw",
        "title": "City of Toronto Zoning By-law 569-2013",
        "source_url": "https://www.toronto.ca/city-government/planning-development/zoning-by-law-preliminary-zoning-reviews/zoning-by-law-569-2013-2/",
        "publisher": "City of Toronto",
        "effective_date": date(2013, 5, 9),
        "clauses": [
            ("10.5.40 — Maximum Height", "height_limit",
             "No person shall use any land or erect or use any building or structure in any zone that exceeds the height limit shown on the Height Overlay Map.",
             '{"type": "height_limit", "unit": "metres"}'),
            ("10.5.50 — Floor Space Index", "fsi_limit",
             "The total floor area of all buildings and structures on a lot shall not exceed the permitted floor space index for the zone multiplied by the lot area.",
             '{"type": "fsi_limit"}'),
            ("10.10.40 — Front Yard Setback", "setback",
             "The required minimum building setback from a front lot line is the distance specified in the zone. A setback may be reduced where the lot abuts a lot with a lesser setback.",
             '{"type": "setback", "face": "front"}'),
            ("10.10.50 — Rear Yard Setback", "setback",
             "The minimum rear yard setback is 7.5 metres unless otherwise specified. For lots with a depth of less than 30 metres, the required rear yard setback is 25 percent of the lot depth.",
             '{"type": "setback", "face": "rear"}'),
            ("10.10.60 — Side Yard Setback", "setback",
             "The required minimum side yard setback for a detached house is 0.9 metres on one side and 0.45 metres on the other. For apartment buildings, the minimum is 5.5 metres.",
             '{"type": "setback", "face": "side"}'),
            ("10.20 — Lot Coverage", "lot_coverage",
             "The maximum lot coverage for a building is specified as a percentage of the lot area. Lot coverage includes the area of all buildings measured at grade level.",
             '{"type": "lot_coverage", "unit": "percentage"}'),
            ("10.40 — Permitted Uses", "permitted_use",
             "The uses permitted in a residential zone include a detached house, semi-detached house, duplex, triplex, fourplex, townhouse, and apartment building, subject to the zone category.",
             '{"type": "permitted_use", "zone_category": "residential"}'),
            ("10.60 — Parking Requirements", "parking",
             "Residential uses require a minimum of 0.5 parking spaces per dwelling unit for buildings within 500 metres of a subway station, and 1.0 spaces per unit in all other areas.",
             '{"type": "parking", "unit": "spaces_per_unit"}'),
            ("40.10 — CR Zone General Provisions", "zone_provision",
             "Development in the CR zone is subject to a maximum density specified by the zone label. The first number indicates total density, values in parentheses indicate commercial and residential components.",
             '{"type": "zone_provision", "zone": "CR"}'),
            ("150.10 — R Zone General Provisions", "zone_provision",
             "In the R zone, only a detached house, semi-detached house, townhouse, or other dwelling type as specified is permitted. Maximum height is 10 metres and maximum FSI is 0.6.",
             '{"type": "zone_provision", "zone": "R"}'),
        ],
    },
    {
        "doc_type": "official_plan",
        "title": "City of Toronto Official Plan (2023 Office Consolidation)",
        "source_url": "https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/official-plan/",
        "publisher": "City of Toronto",
        "effective_date": date(2023, 7, 1),
        "clauses": [
            ("2.2.1 — Downtown", "land_use_designation",
             "The Downtown is planned to accommodate growth in employment, housing and commercial activity. Tall buildings may be permitted where they fit within the existing or planned context of the area.",
             '{"type": "land_use_designation", "area": "downtown"}'),
            ("3.1.2 — Built Form", "built_form",
             "New development will be massed and its height, scale, and density designed to fit harmoniously into its existing and planned context. Transition in scale should be provided between areas of different intensity.",
             '{"type": "built_form"}'),
            ("3.1.3 — Tall Buildings", "tall_buildings",
             "Tall buildings should be designed to consist of a base, middle, and top. The base should define the street edge at a pedestrian scale. A minimum separation distance of 25 metres between tower portions is required.",
             '{"type": "tall_buildings", "min_separation_m": 25}'),
            ("4.5 — Mixed Use Areas", "land_use_designation",
             "Mixed Use Areas are made up of a broad range of commercial, residential and institutional uses, in single use or mixed use buildings, as well as parks and open spaces and utilities.",
             '{"type": "land_use_designation", "area": "mixed_use"}'),
            ("4.1 — Neighbourhoods", "land_use_designation",
             "Neighbourhoods are physically stable areas with a character to be preserved. Development within Neighbourhoods will be consistent with the prevailing patterns of the area.",
             '{"type": "land_use_designation", "area": "neighbourhoods"}'),
            ("3.2.1 — Housing", "housing",
             "A full range of housing, in terms of form, tenure, and affordability, will be provided and maintained to meet the current and future needs of residents.",
             '{"type": "housing"}'),
        ],
    },
    {
        "doc_type": "design_guideline",
        "title": "Toronto Mid-Rise Building Performance Standards",
        "source_url": "https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/design-guidelines/mid-rise-buildings/",
        "publisher": "City of Toronto",
        "effective_date": date(2010, 7, 8),
        "clauses": [
            ("Guideline 1 — Street Wall Height", "design_guideline",
             "The street wall height should be no taller than 80 percent of the right-of-way width. A minimum stepback of 2 metres above the street wall is required to provide a transition to the upper storeys.",
             '{"type": "street_wall", "max_ratio": 0.8, "min_stepback_m": 2}'),
            ("Guideline 2 — Angular Plane", "design_guideline",
             "A 45-degree angular plane measured from a height of 80 percent of the right-of-way width at the front property line must not be penetrated by any part of the building above the street wall.",
             '{"type": "angular_plane", "angle_degrees": 45}'),
            ("Guideline 3 — Rear Transition", "design_guideline",
             "Where a mid-rise building abuts a Neighbourhood, a 45-degree angular plane is applied from the rear property line at a height of 7.5 metres.",
             '{"type": "rear_transition", "angle_degrees": 45, "start_height_m": 7.5}'),
            ("Guideline 4 — Maximum Building Depth", "design_guideline",
             "The maximum depth of the floor plate above the street wall should not exceed 25 metres to ensure adequate access to sunlight and natural ventilation.",
             '{"type": "floor_plate", "max_depth_m": 25}'),
        ],
    },
    {
        "doc_type": "design_guideline",
        "title": "Toronto Tall Building Design Guidelines",
        "source_url": "https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/design-guidelines/tall-buildings/",
        "publisher": "City of Toronto",
        "effective_date": date(2013, 5, 1),
        "clauses": [
            ("Section 1.3 — Tower Placement", "design_guideline",
             "Tower portions of tall buildings should achieve a minimum setback of 3 metres from the side and rear property lines and 12.5 metres from the centre of an adjacent tower to achieve a 25-metre separation.",
             '{"type": "tower_placement", "min_setback_m": 3, "min_separation_m": 25}'),
            ("Section 2.1 — Tower Floor Plate", "design_guideline",
             "The floor plate of the tower portion should not exceed 750 square metres for residential towers and 2000 square metres for commercial towers.",
             '{"type": "tower_floor_plate", "max_residential_m2": 750, "max_commercial_m2": 2000}'),
            ("Section 3.1 — Base Building", "design_guideline",
             "The base of a tall building should be between 3 and 6 storeys and should be generally aligned with the street wall height of adjacent buildings along the block.",
             '{"type": "base_building", "min_storeys": 3, "max_storeys": 6}'),
        ],
    },
    {
        "doc_type": "official_plan",
        "title": "Growing Up — Planning for Children in New Vertical Communities",
        "source_url": "https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/design-guidelines/growing-up-planning-for-children-in-new-vertical-communities/",
        "publisher": "City of Toronto",
        "effective_date": date(2020, 7, 28),
        "clauses": [
            ("Guideline 1 — Unit Mix", "design_guideline",
             "A minimum of 25 percent of units in new multi-unit residential buildings should be large units suitable for families (2-bedroom or larger), with 10 percent being 3-bedroom units.",
             '{"type": "unit_mix", "min_large_pct": 25, "min_3bed_pct": 10}'),
            ("Guideline 2 — Unit Size", "design_guideline",
             "Two-bedroom units should have a minimum area of 87 square metres and three-bedroom units should have a minimum area of 100 square metres.",
             '{"type": "unit_size", "min_2bed_m2": 87, "min_3bed_m2": 100}'),
        ],
    },
    {
        "doc_type": "official_plan",
        "title": "Toronto Inclusionary Zoning Policy",
        "source_url": "https://www.toronto.ca/city-government/planning-development/planning-studies-initiatives/inclusionary-zoning-policy/",
        "publisher": "City of Toronto",
        "effective_date": date(2022, 9, 18),
        "clauses": [
            ("IZ-1 — Affordable Set-Aside", "inclusionary_zoning",
             "In Protected Major Transit Station Areas, residential developments with 100 or more units must set aside between 5 and 10 percent of the total residential gross floor area as affordable rental or ownership housing.",
             '{"type": "affordable_set_aside", "min_units_trigger": 100}'),
            ("IZ-2 — Affordability Period", "inclusionary_zoning",
             "Affordable units must remain affordable for a minimum period of 99 years from the date of initial occupancy.",
             '{"type": "affordability_period", "min_years": 99}'),
        ],
    },
]


def seed_policies() -> None:
    from sqlalchemy import text

    with sync_engine.connect() as conn:
        # Check existing
        existing = conn.execute(text("SELECT COUNT(*) FROM policy_documents")).scalar()
        if existing and existing > 0:
            print(f"Already have {existing} policy documents. Skipping.")
            return

        jur = conn.execute(text("SELECT id FROM jurisdictions LIMIT 1")).first()
        if not jur:
            raise RuntimeError("No jurisdiction found. Run seed_toronto.py first.")
        jurisdiction_id = jur[0]

        now = datetime.now(timezone.utc)
        total_docs = 0
        total_clauses = 0

        for doc_data in DOCUMENTS:
            doc_id = uuid.uuid4()
            conn.execute(text("""
                INSERT INTO policy_documents (id, jurisdiction_id, doc_type, title, source_url, publisher,
                    effective_date, object_key, file_hash, parse_status)
                VALUES (:id, :jid, :doc_type, :title, :source_url, :publisher,
                    :effective_date, :object_key, :file_hash, 'parsed')
            """), {
                "id": doc_id, "jid": jurisdiction_id,
                "doc_type": doc_data["doc_type"], "title": doc_data["title"],
                "source_url": doc_data["source_url"], "publisher": doc_data["publisher"],
                "effective_date": doc_data["effective_date"],
                "object_key": f"policies/seed/{doc_id}.pdf",
                "file_hash": str(doc_id),
            })

            version_id = uuid.uuid4()
            conn.execute(text("""
                INSERT INTO policy_versions (id, document_id, version_number, parser_version,
                    extracted_at, confidence_avg, confidence_min, clause_count, published_at, is_active)
                VALUES (:id, :doc_id, 1, 'seed-v1', :now, 0.95, 0.90, :clause_count, :now, true)
            """), {
                "id": version_id, "doc_id": doc_id,
                "now": now, "clause_count": len(doc_data["clauses"]),
            })

            for section_ref, norm_type, raw_text, norm_json in doc_data["clauses"]:
                clause_id = uuid.uuid4()
                conn.execute(text("""
                    INSERT INTO policy_clauses (id, policy_version_id, section_ref, raw_text,
                        normalized_type, normalized_json, confidence, needs_review)
                    VALUES (:id, :vid, :section_ref, :raw_text, :norm_type, CAST(:norm_json AS jsonb), 0.95, false)
                """), {
                    "id": clause_id, "vid": version_id,
                    "section_ref": section_ref, "raw_text": raw_text,
                    "norm_type": norm_type, "norm_json": norm_json,
                })

                rule_id = uuid.uuid4()
                conn.execute(text("""
                    INSERT INTO policy_applicability_rules (id, policy_clause_id, jurisdiction_id,
                        override_level, applicability_json)
                    VALUES (:id, :cid, :jid, 1, CAST('{"scope": "jurisdiction_wide"}' AS jsonb))
                """), {"id": rule_id, "cid": clause_id, "jid": jurisdiction_id})

                total_clauses += 1
            total_docs += 1

        conn.commit()
        print(f"Seeded {total_docs} policy documents with {total_clauses} clauses.")


if __name__ == "__main__":
    seed_policies()
