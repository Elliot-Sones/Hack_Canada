"""Deterministic OBC interior compliance engine.

Checks floor plan elements against Ontario Building Code Part 9 standards.
All checks are pure math — no AI.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from app.data.obc_interior_standards import OBC_INTERIOR_RULES, OBC_SECTIONS


@dataclass(frozen=True)
class InteriorComplianceRule:
    """A single OBC interior compliance check result."""

    id: str
    parameter: str
    obc_section: str
    required: float | None
    actual: float | None
    unit: str
    compliant: bool
    element_id: str | None = None
    element_type: str | None = None
    severity: str = "error"  # "error", "warning", "blocker"
    note: str = ""


@dataclass
class InteriorComplianceResult:
    """Full interior compliance check result."""

    rules: list[InteriorComplianceRule] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    overall_compliant: bool = True
    load_bearing_warnings: list[str] = field(default_factory=list)


def _check_min_area(
    room: dict[str, Any],
    min_area: float,
    obc_section: str,
    rule_id: str,
) -> InteriorComplianceRule:
    """Check that a room meets the minimum area requirement."""
    actual_area = room.get("area_m2")
    element_id = room.get("id") or room.get("name", "unknown")
    element_type = room.get("type", "room")

    if actual_area is None:
        return InteriorComplianceRule(
            id=rule_id,
            parameter="Minimum Room Area",
            obc_section=obc_section,
            required=min_area,
            actual=None,
            unit="m\u00b2",
            compliant=True,
            element_id=element_id,
            element_type=element_type,
            note="Area not available \u2014 manual verification required",
        )

    compliant = actual_area >= min_area
    return InteriorComplianceRule(
        id=rule_id,
        parameter="Minimum Room Area",
        obc_section=obc_section,
        required=min_area,
        actual=round(actual_area, 2),
        unit="m\u00b2",
        compliant=compliant,
        element_id=element_id,
        element_type=element_type,
        severity="error" if not compliant else "error",
        note=f"Bedroom '{element_id}' area {actual_area:.1f} m\u00b2 < {min_area} m\u00b2" if not compliant else "",
    )


def _compute_min_dimension(polygon: list[list[float]]) -> float | None:
    """Compute the minimum dimension (shortest side) of a polygon.

    Takes a list of [x, y] coordinate pairs defining the polygon boundary.
    Returns the shortest edge length, or None if polygon is invalid.
    """
    if not polygon or len(polygon) < 3:
        return None

    min_dim = float("inf")
    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]
        edge_len = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        if edge_len > 0:
            min_dim = min(min_dim, edge_len)

    return min_dim if min_dim != float("inf") else None


def _check_min_dimension(
    room: dict[str, Any],
    min_dim: float,
    obc_section: str,
    rule_id: str,
) -> InteriorComplianceRule:
    """Check that a room meets the minimum dimension requirement."""
    element_id = room.get("id") or room.get("name", "unknown")
    element_type = room.get("type", "room")

    # Try explicit min_dimension first, then compute from polygon
    actual_dim = room.get("min_dimension_m")
    if actual_dim is None:
        polygon = room.get("polygon")
        if polygon:
            actual_dim = _compute_min_dimension(polygon)

    if actual_dim is None:
        return InteriorComplianceRule(
            id=rule_id,
            parameter="Minimum Room Dimension",
            obc_section=obc_section,
            required=min_dim,
            actual=None,
            unit="m",
            compliant=True,
            element_id=element_id,
            element_type=element_type,
            note="Dimension not available \u2014 manual verification required",
        )

    compliant = actual_dim >= min_dim
    return InteriorComplianceRule(
        id=rule_id,
        parameter="Minimum Room Dimension",
        obc_section=obc_section,
        required=min_dim,
        actual=round(actual_dim, 2),
        unit="m",
        compliant=compliant,
        element_id=element_id,
        element_type=element_type,
        severity="error" if not compliant else "error",
        note=f"Bedroom '{element_id}' shortest side {actual_dim:.2f}m < {min_dim}m" if not compliant else "",
    )


def _find_openings_in_room(
    room: dict[str, Any],
    openings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Find windows/doors that belong to a room based on room_id or spatial containment."""
    room_id = room.get("id") or room.get("name")
    matched = []
    for opening in openings:
        if opening.get("room_id") == room_id:
            matched.append(opening)
    return matched


def _check_egress(
    room: dict[str, Any],
    openings: list[dict[str, Any]],
    min_window_area: float,
    obc_section: str,
    rule_id: str,
) -> InteriorComplianceRule:
    """Check that a bedroom has an egress window meeting minimum area."""
    element_id = room.get("id") or room.get("name", "unknown")
    room_openings = _find_openings_in_room(room, openings)

    # Find windows (not doors) in this room
    windows = [o for o in room_openings if o.get("type") in ("window", "egress_window")]

    if not windows:
        return InteriorComplianceRule(
            id=rule_id,
            parameter="Bedroom Egress Window",
            obc_section=obc_section,
            required=min_window_area,
            actual=0.0,
            unit="m\u00b2",
            compliant=False,
            element_id=element_id,
            element_type="bedroom",
            severity="error",
            note=f"Bedroom '{element_id}' has no egress window",
        )

    # Check if any window meets the minimum area
    max_window_area = max(w.get("area_m2", 0.0) for w in windows)
    compliant = max_window_area >= min_window_area

    return InteriorComplianceRule(
        id=rule_id,
        parameter="Bedroom Egress Window",
        obc_section=obc_section,
        required=min_window_area,
        actual=round(max_window_area, 2),
        unit="m\u00b2",
        compliant=compliant,
        element_id=element_id,
        element_type="bedroom",
        severity="error" if not compliant else "error",
        note=f"Bedroom '{element_id}' largest window {max_window_area:.2f} m\u00b2 < {min_window_area} m\u00b2" if not compliant else "",
    )


def _check_hallway_width(
    hallway: dict[str, Any],
    min_width: float,
    obc_section: str,
    rule_id: str,
) -> InteriorComplianceRule:
    """Check that a hallway meets minimum width."""
    element_id = hallway.get("id") or hallway.get("name", "unknown")
    actual_width = hallway.get("width_m") or hallway.get("min_dimension_m")

    if actual_width is None:
        polygon = hallway.get("polygon")
        if polygon:
            actual_width = _compute_min_dimension(polygon)

    if actual_width is None:
        return InteriorComplianceRule(
            id=rule_id,
            parameter="Minimum Hallway Width",
            obc_section=obc_section,
            required=min_width,
            actual=None,
            unit="m",
            compliant=True,
            element_id=element_id,
            element_type="hallway",
            note="Width not available \u2014 manual verification required",
        )

    compliant = actual_width >= min_width
    return InteriorComplianceRule(
        id=rule_id,
        parameter="Minimum Hallway Width",
        obc_section=obc_section,
        required=min_width,
        actual=round(actual_width, 2),
        unit="m",
        compliant=compliant,
        element_id=element_id,
        element_type="hallway",
        severity="error" if not compliant else "error",
        note=f"Hallway '{element_id}' width {actual_width:.2f}m < {min_width}m" if not compliant else "",
    )


def _check_door_width(
    door: dict[str, Any],
    min_width: float,
    obc_section: str,
    rule_id: str,
) -> InteriorComplianceRule:
    """Check that an exit door meets minimum width."""
    element_id = door.get("id") or door.get("name", "unknown")
    actual_width = door.get("width_m")

    if actual_width is None:
        return InteriorComplianceRule(
            id=rule_id,
            parameter="Minimum Exit Door Width",
            obc_section=obc_section,
            required=min_width,
            actual=None,
            unit="m",
            compliant=True,
            element_id=element_id,
            element_type="door",
            note="Width not available \u2014 manual verification required",
        )

    compliant = actual_width >= min_width
    return InteriorComplianceRule(
        id=rule_id,
        parameter="Minimum Exit Door Width",
        obc_section=obc_section,
        required=min_width,
        actual=round(actual_width, 2),
        unit="m",
        compliant=compliant,
        element_id=element_id,
        element_type="door",
        severity="error" if not compliant else "error",
        note=f"Door '{element_id}' width {actual_width:.2f}m < {min_width}m" if not compliant else "",
    )


def _check_fire_travel(
    room: dict[str, Any],
    exits: list[dict[str, Any]],
    max_travel: float,
    obc_section: str,
    rule_id: str,
) -> InteriorComplianceRule:
    """Check straight-line distance from room centroid to nearest exit <= max_travel."""
    element_id = room.get("id") or room.get("name", "unknown")
    room_center = room.get("center")

    if not room_center or not exits:
        return InteriorComplianceRule(
            id=rule_id,
            parameter="Fire Travel Distance",
            obc_section=obc_section,
            required=max_travel,
            actual=None,
            unit="m",
            compliant=True,
            element_id=element_id,
            element_type=room.get("type", "room"),
            note="Exit locations not available \u2014 manual verification required",
        )

    # Find nearest exit (straight-line)
    min_dist = float("inf")
    rx, ry = room_center[0], room_center[1]
    for ex in exits:
        ex_pos = ex.get("position") or ex.get("center")
        if ex_pos:
            dist = math.sqrt((ex_pos[0] - rx) ** 2 + (ex_pos[1] - ry) ** 2)
            min_dist = min(min_dist, dist)

    if min_dist == float("inf"):
        return InteriorComplianceRule(
            id=rule_id,
            parameter="Fire Travel Distance",
            obc_section=obc_section,
            required=max_travel,
            actual=None,
            unit="m",
            compliant=True,
            element_id=element_id,
            element_type=room.get("type", "room"),
            note="Exit positions not available \u2014 manual verification required",
        )

    compliant = min_dist <= max_travel
    return InteriorComplianceRule(
        id=rule_id,
        parameter="Fire Travel Distance",
        obc_section=obc_section,
        required=max_travel,
        actual=round(min_dist, 2),
        unit="m",
        compliant=compliant,
        element_id=element_id,
        element_type=room.get("type", "room"),
        severity="blocker" if not compliant else "error",
        note=f"Room '{element_id}' is {min_dist:.1f}m from nearest exit (max {max_travel}m)" if not compliant else "",
    )


def check_interior_compliance(
    floor_plan: dict[str, Any],
    ceiling_height_m: float = 2.7,
    original_floor_plan: dict[str, Any] | None = None,
) -> InteriorComplianceResult:
    """Run deterministic OBC interior compliance checks on a floor plan.

    Args:
        floor_plan: Floor plan dict with keys: rooms, openings, exits.
            rooms: list of dicts with id, type, area_m2, polygon, center, min_dimension_m, width_m.
            openings: list of dicts with id, type (window/door/egress_window), room_id, area_m2, width_m.
            exits: list of dicts with id, position/center coordinates.
        ceiling_height_m: Proposed ceiling height (default 2.7m).
        original_floor_plan: Original floor plan for load-bearing wall detection.

    Returns:
        InteriorComplianceResult with all check results.
    """
    rules: list[InteriorComplianceRule] = []
    errors: list[str] = []
    warnings: list[str] = []
    load_bearing_warnings: list[str] = []

    rooms = floor_plan.get("rooms", [])
    openings = floor_plan.get("openings", [])
    exits = floor_plan.get("exits", [])
    rule_counter = 0

    # --- Ceiling height check (global) ---
    rule_counter += 1
    min_ceiling = OBC_INTERIOR_RULES["ceiling_min_height_m"]
    ceiling_compliant = ceiling_height_m >= min_ceiling
    rules.append(InteriorComplianceRule(
        id=f"obc-{rule_counter}",
        parameter="Minimum Ceiling Height",
        obc_section=OBC_SECTIONS["ceiling_min_height"],
        required=min_ceiling,
        actual=ceiling_height_m,
        unit="m",
        compliant=ceiling_compliant,
        severity="error" if not ceiling_compliant else "error",
        note=f"Ceiling height {ceiling_height_m}m < {min_ceiling}m minimum" if not ceiling_compliant else "",
    ))
    if not ceiling_compliant:
        errors.append(f"Ceiling height {ceiling_height_m}m below OBC minimum {min_ceiling}m")

    # --- Per-room checks ---
    for room in rooms:
        room_type = (room.get("type") or "").lower()

        # Bedroom checks
        if room_type in ("bedroom", "master_bedroom", "bed"):
            # Min area
            rule_counter += 1
            area_rule = _check_min_area(
                room,
                OBC_INTERIOR_RULES["bedroom_min_area_m2"],
                OBC_SECTIONS["bedroom_min_area"],
                f"obc-{rule_counter}",
            )
            rules.append(area_rule)
            if not area_rule.compliant and area_rule.note:
                errors.append(area_rule.note)

            # Min dimension
            rule_counter += 1
            dim_rule = _check_min_dimension(
                room,
                OBC_INTERIOR_RULES["bedroom_min_dimension_m"],
                OBC_SECTIONS["bedroom_min_dimension"],
                f"obc-{rule_counter}",
            )
            rules.append(dim_rule)
            if not dim_rule.compliant and dim_rule.note:
                errors.append(dim_rule.note)

            # Egress window
            rule_counter += 1
            egress_rule = _check_egress(
                room,
                openings,
                OBC_INTERIOR_RULES["bedroom_egress_window_m2"],
                OBC_SECTIONS["bedroom_egress_window"],
                f"obc-{rule_counter}",
            )
            rules.append(egress_rule)
            if not egress_rule.compliant and egress_rule.note:
                errors.append(egress_rule.note)

        # Hallway checks
        if room_type in ("hallway", "corridor", "hall"):
            rule_counter += 1
            hall_rule = _check_hallway_width(
                room,
                OBC_INTERIOR_RULES["hallway_min_width_m"],
                OBC_SECTIONS["hallway_min_width"],
                f"obc-{rule_counter}",
            )
            rules.append(hall_rule)
            if not hall_rule.compliant and hall_rule.note:
                errors.append(hall_rule.note)

        # Bathroom ventilation (warning)
        if room_type in ("bathroom", "washroom", "ensuite", "bath"):
            room_id = room.get("id") or room.get("name", "unknown")
            room_openings = _find_openings_in_room(room, openings)
            has_window = any(o.get("type") in ("window", "egress_window") for o in room_openings)
            rule_counter += 1
            rules.append(InteriorComplianceRule(
                id=f"obc-{rule_counter}",
                parameter="Bathroom Ventilation",
                obc_section=OBC_SECTIONS["bathroom_ventilation"],
                required=None,
                actual=None,
                unit="",
                compliant=True,  # warning only
                element_id=room_id,
                element_type="bathroom",
                severity="warning",
                note="" if has_window else f"Bathroom '{room_id}' has no window \u2014 mechanical exhaust fan required",
            ))
            if not has_window:
                warnings.append(f"Bathroom '{room_id}' has no window \u2014 mechanical exhaust fan required")

        # Kitchen ventilation (warning)
        if room_type in ("kitchen", "kitchenette"):
            room_id = room.get("id") or room.get("name", "unknown")
            room_openings = _find_openings_in_room(room, openings)
            has_window = any(o.get("type") in ("window", "egress_window") for o in room_openings)
            rule_counter += 1
            rules.append(InteriorComplianceRule(
                id=f"obc-{rule_counter}",
                parameter="Kitchen Ventilation",
                obc_section=OBC_SECTIONS["kitchen_ventilation"],
                required=None,
                actual=None,
                unit="",
                compliant=True,  # warning only
                element_id=room_id,
                element_type="kitchen",
                severity="warning",
                note="" if has_window else f"Kitchen '{room_id}' has no window \u2014 range hood exhaust required",
            ))
            if not has_window:
                warnings.append(f"Kitchen '{room_id}' has no window \u2014 range hood exhaust required")

        # Fire travel distance (all rooms)
        if exits:
            rule_counter += 1
            fire_rule = _check_fire_travel(
                room,
                exits,
                OBC_INTERIOR_RULES["fire_travel_max_m"],
                OBC_SECTIONS["fire_travel_distance"],
                f"obc-{rule_counter}",
            )
            rules.append(fire_rule)
            if not fire_rule.compliant and fire_rule.note:
                errors.append(fire_rule.note)

    # --- Exit door width checks ---
    exit_doors = [o for o in openings if o.get("type") in ("exit_door", "door") and o.get("is_exit")]
    for door in exit_doors:
        rule_counter += 1
        door_rule = _check_door_width(
            door,
            OBC_INTERIOR_RULES["exit_door_min_width_m"],
            OBC_SECTIONS["exit_door_min_width"],
            f"obc-{rule_counter}",
        )
        rules.append(door_rule)
        if not door_rule.compliant and door_rule.note:
            errors.append(door_rule.note)

    # --- Load-bearing wall modification detection ---
    if original_floor_plan is not None:
        original_walls = {
            w.get("id") or w.get("name")
            for w in original_floor_plan.get("walls", [])
            if w.get("load_bearing")
        }
        current_walls = {
            w.get("id") or w.get("name")
            for w in floor_plan.get("walls", [])
        }
        removed_lb = original_walls - current_walls
        for wall_id in removed_lb:
            rule_counter += 1
            rules.append(InteriorComplianceRule(
                id=f"obc-{rule_counter}",
                parameter="Load-Bearing Wall Modification",
                obc_section=OBC_SECTIONS["load_bearing_wall"],
                required=None,
                actual=None,
                unit="",
                compliant=False,
                element_id=wall_id,
                element_type="wall",
                severity="blocker",
                note=f"Load-bearing wall '{wall_id}' removed \u2014 structural engineer review required",
            ))
            load_bearing_warnings.append(
                f"Load-bearing wall '{wall_id}' removed \u2014 structural engineer review required"
            )

    # Determine overall compliance
    overall_compliant = all(
        r.compliant for r in rules if r.severity in ("error", "blocker")
    )

    return InteriorComplianceResult(
        rules=rules,
        errors=errors,
        warnings=warnings,
        overall_compliant=overall_compliant,
        load_bearing_warnings=load_bearing_warnings,
    )
