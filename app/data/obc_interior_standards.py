"""Ontario Building Code interior standards — deterministic reference data.

All data from OBC (Ontario Building Code) Part 9 — Housing and Small Buildings.
No AI involved.
"""

OBC_INTERIOR_RULES: dict[str, float] = {
    "bedroom_min_area_m2": 7.0,            # OBC 9.5.7.1
    "bedroom_min_dimension_m": 2.4,         # OBC 9.5.7.1
    "bedroom_egress_window_m2": 0.35,       # OBC 9.9.10.1
    "hallway_min_width_m": 0.86,            # OBC 9.5.4.1
    "exit_door_min_width_m": 0.81,          # OBC 9.5.5.1
    "ceiling_min_height_m": 2.3,            # OBC 9.5.3.1
    "fire_travel_max_m": 45.0,              # OBC 9.9.9.3
    "fire_access_min_width_m": 0.9,         # OBC 9.10.1.4
}

# OBC section references for each rule
OBC_SECTIONS: dict[str, str] = {
    "bedroom_min_area": "OBC 9.5.7.1",
    "bedroom_min_dimension": "OBC 9.5.7.1",
    "bedroom_egress_window": "OBC 9.9.10.1",
    "hallway_min_width": "OBC 9.5.4.1",
    "exit_door_min_width": "OBC 9.5.5.1",
    "ceiling_min_height": "OBC 9.5.3.1",
    "fire_travel_distance": "OBC 9.9.9.3",
    "fire_access_width": "OBC 9.10.1.4",
    "bathroom_ventilation": "OBC 9.32.3.3",
    "kitchen_ventilation": "OBC 9.32.3.3",
    "load_bearing_wall": "OBC 9.23",
    "room_enclosure": "OBC 9.5.1",
}

# Human-readable policy descriptions for each rule
OBC_DESCRIPTIONS: dict[str, str] = {
    "bedroom_min_area": (
        "Every bedroom must have a floor area of at least 7.0 m². "
        "This ensures adequate living space for occupants as required by OBC Part 9."
    ),
    "bedroom_min_dimension": (
        "No bedroom dimension (wall-to-wall) may be less than 2.4 m. "
        "This prevents excessively narrow rooms that would be impractical for furniture placement and occupant comfort."
    ),
    "bedroom_egress_window": (
        "Each bedroom must have at least one openable window with a minimum unobstructed area of 0.35 m² "
        "to serve as an emergency escape route in case of fire."
    ),
    "hallway_min_width": (
        "Hallways and corridors must be at least 860 mm (0.86 m) wide to allow safe passage "
        "and emergency egress for occupants."
    ),
    "exit_door_min_width": (
        "Exit doors must have a clear opening width of at least 810 mm (0.81 m) "
        "to permit safe evacuation during emergencies."
    ),
    "ceiling_min_height": (
        "Habitable rooms must have a minimum ceiling height of 2.3 m. "
        "Lower ceilings are only permitted in non-habitable spaces such as storage or utility rooms."
    ),
    "fire_travel_distance": (
        "The travel distance from any point in a room to the nearest exit must not exceed 45 m. "
        "This is a life-safety requirement ensuring occupants can evacuate quickly during a fire."
    ),
    "fire_access_width": (
        "Fire access routes must maintain a minimum clear width of 0.9 m "
        "to allow firefighter access with equipment."
    ),
    "bathroom_ventilation": (
        "Bathrooms without an openable window require mechanical exhaust ventilation "
        "to control moisture and maintain air quality per OBC 9.32.3.3."
    ),
    "kitchen_ventilation": (
        "Kitchens without an openable window require a range hood or mechanical exhaust "
        "to remove cooking fumes and moisture per OBC 9.32.3.3."
    ),
    "load_bearing_wall": (
        "Removing or modifying a load-bearing wall requires a structural engineer's review "
        "and may need an Alternative Solution submission to the Chief Building Official."
    ),
    "room_enclosure": (
        "Every habitable room must be fully enclosed by walls. "
        "A missing wall means the room boundary is incomplete, which affects fire separation, "
        "sound transmission, and overall building code compliance."
    ),
}
