"""Submission document templates with system prompts and user prompt templates.

Each template defines how to generate a specific government submission document.
The AI provider uses these to produce professional, citation-rich content.
"""

DOCUMENT_TEMPLATES = {
    "cover_letter": {
        "system_prompt": (
            "You are a professional urban planning consultant in Toronto, Ontario. "
            "Write a formal cover letter to the City of Toronto Planning Department "
            "introducing a development application. Be concise, professional, and reference "
            "the specific municipal address, application type, and key proposal metrics. "
            "Use standard Canadian business letter format."
        ),
        "user_prompt_template": (
            "Write a cover letter for a development application with these details:\n\n"
            "Address: {address}\n"
            "Project Name: {project_name}\n"
            "Development Type: {development_type}\n"
            "Building Type: {building_type}\n"
            "Proposed Height: {height_m}m ({storeys} storeys)\n"
            "Total Units: {unit_count}\n"
            "GFA: {gross_floor_area_sqm} sqm\n"
            "Applicant Organization: {organization_name}\n\n"
            "Key points to cover:\n"
            "- Introduction of the applicant and property\n"
            "- Brief description of the proposed development\n"
            "- Statement that the proposal conforms to applicable policies\n"
            "- List of enclosed submission documents\n"
            "- Contact information for follow-up"
        ),
        "max_tokens": 2048,
    },

    "planning_rationale": {
        "system_prompt": (
            "You are a senior planning consultant writing a Planning Rationale for submission "
            "to the City of Toronto. This document must:\n"
            "1. Describe the site and surrounding context\n"
            "2. Analyze conformity with the Provincial Policy Statement\n"
            "3. Analyze conformity with the Growth Plan for the Greater Golden Horseshoe\n"
            "4. Analyze conformity with the Toronto Official Plan\n"
            "5. Analyze conformity with applicable Secondary Plans\n"
            "6. Analyze conformity with Zoning By-law 569-2013\n"
            "7. Reference specific policy sections with citations\n"
            "8. Justify any requested variances with precedent\n"
            "9. Conclude with a recommendation for approval\n\n"
            "Use professional planning language. Cite specific bylaw sections. "
            "This is a legal document that will be reviewed by city planners."
        ),
        "user_prompt_template": (
            "Write a Planning Rationale for this development proposal:\n\n"
            "## Site Information\n"
            "Address: {address}\n"
            "Current Zoning: {zoning_code}\n"
            "Lot Area: {lot_area_sqm} sqm\n"
            "Lot Frontage: {lot_frontage_m}m\n"
            "Current Use: {current_use}\n\n"
            "## Proposed Development\n"
            "Project: {project_name}\n"
            "Type: {development_type} — {building_type}\n"
            "Height: {height_m}m ({storeys} storeys)\n"
            "GFA: {gross_floor_area_sqm} sqm\n"
            "Units: {unit_count}\n"
            "Ground Floor: {ground_floor_use}\n"
            "Parking: {parking_type}\n\n"
            "## Policy Context\n"
            "{policy_stack_summary}\n\n"
            "## Compliance Results\n"
            "{compliance_summary}\n\n"
            "## Precedent Applications\n"
            "{precedent_summary}\n\n"
            "## Variances Requested\n"
            "{variance_summary}"
        ),
        "max_tokens": 8192,
    },

    "compliance_matrix": {
        "system_prompt": (
            "You are generating a Policy Compliance Matrix for a Toronto development application. "
            "Present each zoning provision as a row in a structured table format. "
            "For each provision, show: the bylaw section, the required value, the proposed value, "
            "and whether the proposal complies (COMPLIES / VARIANCE REQUIRED). "
            "Use Markdown table format. Be precise with numbers and units."
        ),
        "user_prompt_template": (
            "Generate a compliance matrix for this proposal:\n\n"
            "Address: {address}\n"
            "Zoning: {zoning_code}\n\n"
            "## Proposed Metrics\n"
            "Height: {height_m}m ({storeys} storeys)\n"
            "GFA: {gross_floor_area_sqm} sqm\n"
            "Lot Coverage: {lot_coverage_pct}%\n"
            "FSI/FAR: {fsi}\n"
            "Units: {unit_count}\n\n"
            "## Applicable Provisions\n"
            "{policy_provisions}\n\n"
            "## Entitlement Check Results\n"
            "{entitlement_results}\n\n"
            "Format as a Markdown table with columns:\n"
            "| Provision | By-law Section | Required | Proposed | Status |"
        ),
        "max_tokens": 4096,
        "structured_output": {
            "type": "object",
            "properties": {
                "provisions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "provision": {"type": "string"},
                            "bylaw_section": {"type": "string"},
                            "required_value": {"type": "string"},
                            "proposed_value": {"type": "string"},
                            "status": {"type": "string", "enum": ["COMPLIES", "VARIANCE REQUIRED"]},
                        },
                    },
                },
                "total_compliant": {"type": "integer"},
                "total_variance": {"type": "integer"},
            },
        },
    },

    "site_plan_data": {
        "system_prompt": (
            "You are generating a Site Plan Data Summary for a development application. "
            "Present the parcel geometry, setback dimensions, building footprint, "
            "access points, servicing, and key site dimensions in a clear, structured format. "
            "Use metric units (metres, square metres). Include a data table and narrative description."
        ),
        "user_prompt_template": (
            "Generate a site plan data summary:\n\n"
            "Address: {address}\n"
            "Lot Area: {lot_area_sqm} sqm\n"
            "Lot Frontage: {lot_frontage_m}m\n"
            "Lot Depth: {lot_depth_m}m\n"
            "Current Use: {current_use}\n\n"
            "## Setbacks & Building Envelope\n"
            "{setback_data}\n\n"
            "## Massing Summary\n"
            "{massing_summary}\n\n"
            "Present as structured data tables with metric measurements."
        ),
        "max_tokens": 3072,
    },

    "massing_summary": {
        "system_prompt": (
            "You are generating a Built Form / Massing Summary for a development application. "
            "Describe the building envelope, height strategy, stepback regime, podium/tower "
            "relationship (if applicable), and key volumetric metrics. "
            "Reference Toronto's Tall Building Guidelines where relevant."
        ),
        "user_prompt_template": (
            "Generate a massing summary:\n\n"
            "Project: {project_name}\n"
            "Building Type: {building_type}\n"
            "Height: {height_m}m ({storeys} storeys)\n"
            "GFA: {gross_floor_area_sqm} sqm\n\n"
            "## Massing Parameters\n"
            "{massing_parameters}\n\n"
            "## Policy Constraints Applied\n"
            "{policy_constraints}\n\n"
            "Describe the built form strategy, floor plate sizes, "
            "podium height, tower separation (if applicable), and angular plane compliance."
        ),
        "max_tokens": 3072,
    },

    "unit_mix_summary": {
        "system_prompt": (
            "You are generating a Unit Mix Summary for a Toronto development application. "
            "Present the unit breakdown by type (studio, 1-bed, 2-bed, 3-bed), count, "
            "area ranges, and percentage. Include accessible unit counts. "
            "Reference Toronto's Growing Up Guidelines for family-sized unit requirements."
        ),
        "user_prompt_template": (
            "Generate a unit mix summary:\n\n"
            "Total Units: {unit_count}\n"
            "Building Type: {building_type}\n"
            "GFA: {gross_floor_area_sqm} sqm\n\n"
            "## Unit Mix\n"
            "{unit_mix_data}\n\n"
            "## Layout Optimization Results\n"
            "{layout_results}\n\n"
            "Present as a Markdown table and include family-sized unit compliance analysis."
        ),
        "max_tokens": 3072,
        "structured_output": {
            "type": "object",
            "properties": {
                "units": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "count": {"type": "integer"},
                            "percentage": {"type": "number"},
                            "avg_area_sqm": {"type": "number"},
                            "accessible_count": {"type": "integer"},
                        },
                    },
                },
                "total_units": {"type": "integer"},
                "family_sized_pct": {"type": "number"},
            },
        },
    },

    "financial_feasibility": {
        "system_prompt": (
            "You are generating a Financial Feasibility Summary for a development application. "
            "Present high-level pro forma metrics: revenue projections, construction costs, "
            "land value assumptions, NOI, cap rate, and return estimates. "
            "This is a summary — not a full pro forma — intended to demonstrate project viability. "
            "Use Toronto market assumptions. Present in a professional format suitable for "
            "a planning submission or investor review."
        ),
        "user_prompt_template": (
            "Generate a financial feasibility summary:\n\n"
            "Project: {project_name}\n"
            "Units: {unit_count}\n"
            "GFA: {gross_floor_area_sqm} sqm\n"
            "Building Type: {building_type}\n\n"
            "## Financial Analysis Results\n"
            "{financial_results}\n\n"
            "## Assumptions Used\n"
            "{financial_assumptions}\n\n"
            "## Market Comparables\n"
            "{market_comparables}\n\n"
            "Present key metrics: total development cost, projected revenue, NOI, "
            "cap rate valuation, and estimated return on cost."
        ),
        "max_tokens": 4096,
    },

    "precedent_report": {
        "system_prompt": (
            "You are generating a Precedent Analysis Report for a development application. "
            "Present comparable approved developments nearby, including their address, "
            "application number, approval date, key metrics (height, units, FSI), "
            "and relevant excerpts from planning rationales or staff reports. "
            "This strengthens the application by showing that similar proposals have been approved."
        ),
        "user_prompt_template": (
            "Generate a precedent analysis report:\n\n"
            "Subject Site: {address}\n"
            "Proposed: {building_type}, {height_m}m, {unit_count} units\n"
            "Zoning: {zoning_code}\n\n"
            "## Precedent Search Results\n"
            "{precedent_results}\n\n"
            "## Similarity Analysis\n"
            "{similarity_analysis}\n\n"
            "For each precedent, present: address, app number, decision, key metrics, "
            "and why it supports this proposal."
        ),
        "max_tokens": 4096,
    },

    "public_benefit_statement": {
        "system_prompt": (
            "You are generating a Public Benefit Statement (Section 37 / Community Benefits) "
            "for a Toronto development application. Describe how the proposed development "
            "contributes to the community: affordable housing commitments, public realm "
            "improvements, community facilities, parkland contributions, public art, "
            "sustainability features, and transit infrastructure support. "
            "Reference Toronto's Official Plan policies on community benefits."
        ),
        "user_prompt_template": (
            "Generate a public benefit statement:\n\n"
            "Project: {project_name}\n"
            "Address: {address}\n"
            "Units: {unit_count}\n"
            "Type: {development_type}\n\n"
            "## Proposed Public Benefits\n"
            "{public_benefits}\n\n"
            "## Community Context\n"
            "{community_context}\n\n"
            "Describe community contributions and Section 37 considerations."
        ),
        "max_tokens": 3072,
    },

    "shadow_study": {
        "system_prompt": (
            "You are generating Shadow Study Data for a development application. "
            "Present the shadow impact analysis: which neighboring properties are affected, "
            "duration of shadow at key times (March 21, June 21, September 21), "
            "and comparison to the as-of-right shadow. Reference Toronto's shadow study "
            "requirements and Official Plan policies on sunlight access."
        ),
        "user_prompt_template": (
            "Generate shadow study data:\n\n"
            "Address: {address}\n"
            "Building Height: {height_m}m ({storeys} storeys)\n"
            "Building Footprint: {building_footprint}\n"
            "Orientation: {orientation}\n\n"
            "## Massing Geometry\n"
            "{massing_parameters}\n\n"
            "Present shadow analysis for March 21, June 21, September 21 "
            "at 9:18am, 12:18pm, 3:18pm, and 6:18pm (Toronto standard times). "
            "Note: actual shadow geometry requires 3D modeling — present methodology "
            "and estimated impact based on building dimensions."
        ),
        "max_tokens": 3072,
    },
}
