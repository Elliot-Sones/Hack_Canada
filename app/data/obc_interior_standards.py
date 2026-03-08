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
}
