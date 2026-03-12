"""Hardcoded electrical infrastructure standards for Ontario.

All data is deterministic reference data — no AI involved.
Sources: OESC (CSA C22.1 ON:24), OBC Parts 3 & 9, ESA regulations,
Electricity Act 1998, O.Reg 164/99, Toronto Hydro design standards.
"""

# ---------------------------------------------------------------------------
# Regulatory hierarchy
# ---------------------------------------------------------------------------

ELECTRICAL_REGULATORY_HIERARCHY: list[dict] = [
    {
        "level": 1,
        "authority": "Electricity Act, 1998 (S.O. 1998, c.15 Sch.A)",
        "scope": "Provincial — governs generation, transmission, distribution, retail",
        "key_provisions": [
            "Establishes ESA authority for electrical safety",
            "Licencing of electrical contractors and master electricians",
            "Defines Ontario Energy Board regulatory powers",
        ],
    },
    {
        "level": 2,
        "authority": "O.Reg 164/99 — Electrical Safety Code Adoption",
        "scope": "Adopts CSA C22.1 (Canadian Electrical Code) with Ontario amendments",
        "key_provisions": [
            "Makes OESC mandatory for all electrical installations in Ontario",
            "Defines ESA as the inspection authority",
            "Sets permit requirements for all electrical work",
        ],
    },
    {
        "level": 3,
        "authority": "OESC — Ontario Electrical Safety Code (CSA C22.1 ON:24)",
        "scope": "Technical safety standards for all electrical installations",
        "key_provisions": [
            "Wiring methods, conductor sizing, overcurrent protection",
            "GFCI/AFCI protection requirements",
            "Grounding and bonding",
            "Service entrance and panel requirements",
            "ESS (Energy Storage System) installation rules",
        ],
    },
    {
        "level": 4,
        "authority": "Ontario Building Code (O.Reg 332/12)",
        "scope": "Building-level electrical facility requirements",
        "key_provisions": [
            "Part 9 s.9.34 — Electrical facilities for housing",
            "Part 3 — Fire alarm, emergency power for large buildings",
            "Part 3 s.3.2.7 — Electrical room fire separation",
        ],
    },
    {
        "level": 5,
        "authority": "Toronto Green Standard (TGS v4)",
        "scope": "Municipal energy performance requirements",
        "key_provisions": [
            "Tier 1 (mandatory): EV-ready infrastructure, energy efficiency",
            "Tier 2+ (voluntary): Net-zero ready, renewable energy",
        ],
    },
    {
        "level": 6,
        "authority": "Toronto Hydro — Conditions of Service",
        "scope": "Local distribution connection requirements",
        "key_provisions": [
            "Service entrance specifications",
            "Metering requirements",
            "Transformer and switchgear clearances",
            "Underground vs. overhead service standards",
        ],
    },
]

# ---------------------------------------------------------------------------
# OBC Part 9 s.9.34 — Electrical Facilities (Housing)
# ---------------------------------------------------------------------------

OBC_ELECTRICAL_FACILITIES: dict[str, dict] = {
    "lighting_outlets": {
        "standard_ref": "OBC 9.34.2.1",
        "description": "Minimum lighting outlets per room type",
        "requirements": {
            "living_room": {"min_outlets": 1, "wall_switch_required": True},
            "dining_room": {"min_outlets": 1, "wall_switch_required": True},
            "bedroom": {"min_outlets": 1, "wall_switch_required": True},
            "kitchen": {"min_outlets": 1, "wall_switch_required": True},
            "bathroom": {"min_outlets": 1, "wall_switch_required": True},
            "hallway": {"min_outlets": 1, "wall_switch_required": True},
            "stairway": {"min_outlets": 1, "wall_switch_required": True},
            "laundry": {"min_outlets": 1, "wall_switch_required": True},
            "furnace_room": {"min_outlets": 1, "wall_switch_required": True},
            "storage_room": {"min_outlets": 1, "wall_switch_required": True},
            "garage": {"min_outlets": 1, "wall_switch_required": True},
        },
    },
    "exterior_lighting": {
        "standard_ref": "OBC 9.34.2.3",
        "description": "Exterior lighting at every entrance",
        "requirements": {
            "entrance_light_required": True,
            "wall_switch_required": True,
            "note": "At least one lighting outlet controlled by a wall switch at each entrance",
        },
    },
    "stairway_switches": {
        "standard_ref": "OBC 9.34.2.5",
        "description": "3-way switches on stairs with 4 or more risers",
        "requirements": {
            "min_risers_for_3way": 4,
            "note": "Stairways with 4+ risers require 3-way switching at top and bottom",
        },
    },
    "basement_lighting": {
        "standard_ref": "OBC 9.34.2.2",
        "description": "Basement lighting minimum density",
        "requirements": {
            "min_outlets_per_30m2": 1,
            "area_per_outlet_m2": 30,
            "wall_switch_required": True,
            "note": "At least 1 lighting outlet per 30 m² of basement floor area",
        },
    },
}

# ---------------------------------------------------------------------------
# OBC Part 3 — Large Building Electrical Requirements
# ---------------------------------------------------------------------------

OBC_LARGE_BUILDING_ELECTRICAL: dict[str, dict] = {
    "fire_alarm": {
        "standard_ref": "OBC 3.2.4",
        "description": "Fire alarm system requirements",
        "required_when": "Part 3 building (3+ storeys or >600 m² per floor)",
        "requirements": {
            "system_required": True,
            "annunciator_at_entrance": True,
            "zone_per_floor": True,
        },
    },
    "emergency_lighting": {
        "standard_ref": "OBC 3.2.7.3",
        "description": "Emergency lighting in exit paths",
        "required_when": "Part 3 building",
        "requirements": {
            "min_illumination_lux": 10,
            "duration_minutes": 30,
            "locations": ["exit stairs", "corridors", "exit signs", "lobby"],
        },
    },
    "exit_signs": {
        "standard_ref": "OBC 3.4.5",
        "description": "Illuminated exit signs",
        "required_when": "Part 3 building",
        "requirements": {
            "internally_illuminated": True,
            "at_every_exit_door": True,
            "along_exit_path": True,
        },
    },
    "emergency_power": {
        "standard_ref": "OBC 3.2.7.4",
        "description": "Emergency power supply for high buildings",
        "required_when": "Building height > 18 m (high building)",
        "requirements": {
            "building_height_threshold_m": 18,
            "generator_required": True,
            "auto_transfer_switch": True,
            "fuel_supply_hours": 2,
            "loads_served": [
                "fire alarm",
                "emergency lighting",
                "exit signs",
                "fire pump",
                "elevator (at least one)",
                "stairwell pressurization",
            ],
        },
    },
    "electrical_room_fire_separation": {
        "standard_ref": "OBC 3.6.2.1",
        "description": "Fire separation for electrical rooms in Part 3 buildings",
        "required_when": "Part 3 building with electrical room",
        "requirements": {
            "min_fire_resistance_rating_hr": 1,
            "note": "Electrical rooms shall be separated from remainder of building by a fire separation with a fire-resistance rating of not less than 1 h",
        },
    },
}

# ---------------------------------------------------------------------------
# OESC Key Requirements (CSA C22.1 ON:24)
# ---------------------------------------------------------------------------

OESC_KEY_REQUIREMENTS: dict[str, dict] = {
    "gfci_protection": {
        "standard_ref": "OESC Rule 26-700",
        "description": "Ground Fault Circuit Interrupter protection zones",
        "required_zones": [
            "kitchen_countertop",
            "bathroom",
            "laundry",
            "garage",
            "outdoor",
            "unfinished_basement",
        ],
        "trip_threshold_ma": 5,
        "note": "Class A GFCI required — trips at 5 mA ground fault current",
    },
    "panel_capacity": {
        "standard_ref": "OESC Rule 8-200",
        "description": "Minimum service/panel amperage",
        "requirements": {
            "min_residential_amps": 100,
            "min_residential_multi_unit_amps": 200,
            "multi_unit_threshold": 2,
            "note": "100A minimum for single-unit residential; 200A for 2+ units",
        },
    },
    "permit_requirements": {
        "standard_ref": "O.Reg 164/99 s.6",
        "description": "ESA permit required for all electrical work",
        "requirements": {
            "permit_required": True,
            "exceptions": [
                "Replacing receptacle/switch cover plates",
                "Replacing light bulbs",
                "Resetting breakers",
            ],
            "note": "All electrical work (installation, alteration, repair) requires an ESA permit except minor maintenance",
        },
    },
    "ess_installation": {
        "standard_ref": "OESC Rule 64-900",
        "description": "Energy Storage System installation requirements",
        "requirements": {
            "listed_equipment_required": True,
            "disconnect_required": True,
            "signage_required": True,
            "note": "Battery ESS must be listed to UL 9540 or equivalent, with accessible disconnect and hazard signage",
        },
    },
}

# ---------------------------------------------------------------------------
# ESA Inspection Stages
# ---------------------------------------------------------------------------

ESA_INSPECTION_STAGES: list[dict] = [
    {
        "stage": "service",
        "description": "Service entrance inspection",
        "timing": "Before utility energizes the service",
        "checks": [
            "Service entrance cable/conduit routing",
            "Panel grounding and bonding",
            "Meter base installation",
            "Service size matches permit",
        ],
    },
    {
        "stage": "rough_in",
        "description": "Rough-in wiring inspection",
        "timing": "After wiring, before drywall closure",
        "checks": [
            "Wire gauge matches circuit amperage",
            "Box fill calculations",
            "AFCI/GFCI branch circuit compliance",
            "Proper stapling and support",
            "Grounding continuity",
        ],
    },
    {
        "stage": "final",
        "description": "Final inspection",
        "timing": "After all devices installed, before occupancy",
        "checks": [
            "All devices and covers installed",
            "GFCI/AFCI devices tested",
            "Panel labelling complete",
            "Smoke/CO detector circuits verified",
            "Polarity and ground check on all receptacles",
        ],
    },
]

# ---------------------------------------------------------------------------
# Pole Type Specifications (Toronto Topographic Mapping)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Voltage Tier Classification — for map visualization & capacity analysis
# ---------------------------------------------------------------------------

VOLTAGE_TIERS: dict[str, dict] = {
    "transmission_500kv": {
        "label": "500 kV Transmission",
        "min_kv": 200,
        "max_kv": 999,
        "color": "#e74c3c",
        "line_width_factor": 4.0,
        "typical_capacity_mva": 1000,
        "description": "IESO bulk transmission (Hydro One corridor)",
    },
    "transmission_115kv": {
        "label": "115 kV Transmission",
        "min_kv": 100,
        "max_kv": 199,
        "color": "#e67e22",
        "line_width_factor": 3.0,
        "typical_capacity_mva": 200,
        "description": "Sub-transmission feeding municipal stations",
    },
    "distribution_27kv": {
        "label": "27.6 kV Distribution",
        "min_kv": 20,
        "max_kv": 99,
        "color": "#3498db",
        "line_width_factor": 2.0,
        "typical_capacity_mva": 30,
        "description": "Toronto Hydro primary distribution feeder",
    },
    "distribution_13kv": {
        "label": "13.8 kV Distribution",
        "min_kv": 5,
        "max_kv": 19.9,
        "color": "#2ecc71",
        "line_width_factor": 1.5,
        "typical_capacity_mva": 12,
        "description": "Toronto Hydro secondary distribution",
    },
    "local_secondary": {
        "label": "Local Secondary",
        "min_kv": 0.1,
        "max_kv": 4.99,
        "color": "#f1c40f",
        "line_width_factor": 1.0,
        "typical_capacity_mva": 2,
        "description": "Local 120/240V – 600V service",
    },
    "unknown": {
        "label": "Unknown (Distribution)",
        "min_kv": 0,
        "max_kv": 0,
        "color": "#9b59b6",
        "line_width_factor": 1.2,
        "typical_capacity_mva": 0,
        "description": "Likely local distribution — voltage not in source data",
    },
}

# ---------------------------------------------------------------------------
# CEC Demand Calculations (Canadian Electrical Code Rule 8-200)
# ---------------------------------------------------------------------------

CEC_DEMAND_CALCULATIONS: dict[str, dict] = {
    "residential": {
        "standard_ref": "CEC Rule 8-200",
        "base_load_w": 5000,
        "area_factor_w_per_m2": 10,
        "first_area_threshold_m2": 90,
        "additional_area_factor": 10,
        "appliance_loads": {
            "electric_range": {"watts": 6000, "demand_factor": 0.40},
            "electric_dryer": {"watts": 5000, "demand_factor": 0.25},
            "electric_water_heater": {"watts": 4500, "demand_factor": 1.00},
            "air_conditioning": {"watts": 3500, "demand_factor": 1.00},
            "ev_charger_l2": {"watts": 7200, "demand_factor": 1.00},
            "electric_heating_per_m2": {"watts": 55, "demand_factor": 0.75},
        },
        "multi_unit_demand_factors": {
            1: 1.00, 2: 0.80, 3: 0.75, 4: 0.70, 5: 0.65,
            10: 0.55, 15: 0.50, 20: 0.45, 30: 0.40, 50: 0.35,
        },
    },
    "commercial": {
        "standard_ref": "CEC Rule 8-202",
        "w_per_m2_by_subtype": {
            "office": 50,
            "retail": 60,
            "restaurant": 100,
            "grocery": 80,
            "warehouse": 20,
            "medical": 70,
            "hotel": 55,
            "school": 45,
            "gym": 65,
            "mixed_use": 55,
        },
        "hvac_factor": 1.25,
        "lighting_factor": 1.10,
    },
    "industrial": {
        "standard_ref": "CEC Rule 8-204",
        "w_per_m2_by_subtype": {
            "light_manufacturing": 80,
            "heavy_manufacturing": 150,
            "data_center": 500,
            "cold_storage": 120,
            "workshop": 60,
        },
        "motor_load_factor": 1.25,
    },
}

# ---------------------------------------------------------------------------
# Toronto Hydro Service Ratings — typical by building category
# ---------------------------------------------------------------------------

TORONTO_HYDRO_SERVICE_RATINGS: dict[str, dict] = {
    "single_family": {
        "typical_amps": 200,
        "voltage": "120/240V",
        "phase": "single",
        "service_type": "overhead or underground",
    },
    "semi_detached": {
        "typical_amps": 200,
        "voltage": "120/240V",
        "phase": "single",
        "service_type": "overhead or underground",
    },
    "townhouse": {
        "typical_amps": 200,
        "voltage": "120/240V",
        "phase": "single",
        "service_type": "underground",
    },
    "low_rise_residential": {
        "typical_amps": 600,
        "voltage": "120/208V",
        "phase": "three",
        "service_type": "underground pad-mount transformer",
    },
    "mid_rise_residential": {
        "typical_amps": 1200,
        "voltage": "120/208V",
        "phase": "three",
        "service_type": "underground vault transformer",
    },
    "high_rise_residential": {
        "typical_amps": 2000,
        "voltage": "120/208V or 347/600V",
        "phase": "three",
        "service_type": "underground vault transformer",
    },
    "commercial_small": {
        "typical_amps": 400,
        "voltage": "120/208V",
        "phase": "three",
        "service_type": "underground pad-mount transformer",
    },
    "commercial_large": {
        "typical_amps": 1600,
        "voltage": "347/600V",
        "phase": "three",
        "service_type": "underground vault transformer",
    },
    "industrial": {
        "typical_amps": 3000,
        "voltage": "347/600V or 4.16 kV",
        "phase": "three",
        "service_type": "dedicated substation",
    },
}

# ---------------------------------------------------------------------------
# Pole Type Specifications (Toronto Topographic Mapping)
# ---------------------------------------------------------------------------

POLE_TYPE_SPECS: dict[str, dict] = {
    "circular_hydro_tower": {
        "label": "Circular Hydro Tower",
        "description": "High-voltage transmission/distribution tower",
        "typical_height_range_m": [15.0, 45.0],
        "min_setback_from_building_m": 5.0,
        "min_ground_clearance_m": 5.5,
        "voltage_range": "4.16 kV – 230 kV",
        "standards_ref": "Toronto Hydro, CSA C22.3 No.1",
    },
    "street_light_pole": {
        "label": "Street Light Pole",
        "description": "Municipal roadway illumination pole",
        "typical_height_range_m": [8.0, 15.0],
        "min_setback_from_building_m": 1.5,
        "min_ground_clearance_m": 5.5,
        "voltage_range": "120 V – 347 V",
        "standards_ref": "Toronto Street Lighting Standards, RP-8",
    },
    "pedestrian_light_pole": {
        "label": "Pedestrian Light Pole",
        "description": "Pedestrian-scale illumination (paths, parks)",
        "typical_height_range_m": [3.5, 5.0],
        "min_setback_from_building_m": 0.6,
        "min_ground_clearance_m": 2.5,
        "voltage_range": "120 V – 240 V",
        "standards_ref": "Toronto Pedestrian Lighting Standards",
    },
    "traffic_signal_pole": {
        "label": "Traffic Signal Pole",
        "description": "Traffic signal support structure",
        "typical_height_range_m": [5.0, 9.0],
        "min_setback_from_building_m": 2.0,
        "min_ground_clearance_m": 5.2,
        "voltage_range": "120 V – 240 V",
        "standards_ref": "MTO Traffic Signal Design Manual, OTM Book 12",
    },
}
