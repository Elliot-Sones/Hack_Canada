"""DXF floor plan parsing using ezdxf.

Extracts walls, rooms, doors/windows, and floor groupings from DXF files.
All coordinates output in metres, centred at origin.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class WallSegment:
    start: tuple[float, float]
    end: tuple[float, float]
    thickness_m: float = 0.2
    type: str = "interior"


@dataclass
class Room:
    name: str
    type: str
    polygon: list[tuple[float, float]]
    area_m2: float


@dataclass
class Opening:
    position: tuple[float, float]
    width_m: float
    type: str  # "door" or "window"


@dataclass
class FloorPlan:
    floor_number: int
    floor_label: str
    walls: list[WallSegment] = field(default_factory=list)
    rooms: list[Room] = field(default_factory=list)
    openings: list[Opening] = field(default_factory=list)


def _polygon_area(pts: list[tuple[float, float]]) -> float:
    """Shoelace formula for polygon area."""
    n = len(pts)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1]
        area -= pts[j][0] * pts[i][1]
    return abs(area) / 2.0


def _classify_room(name: str) -> str:
    """Guess room type from label text."""
    lower = name.lower()
    for keyword, rtype in [
        ("bed", "bedroom"), ("bath", "bathroom"), ("wash", "bathroom"),
        ("wc", "bathroom"), ("toilet", "bathroom"), ("shower", "bathroom"),
        ("kitchen", "kitchen"), ("kit", "kitchen"),
        ("living", "living"), ("lounge", "living"), ("family", "living"),
        ("dining", "dining"), ("hall", "hallway"), ("corridor", "hallway"),
        ("foyer", "hallway"), ("entry", "hallway"), ("lobby", "hallway"),
        ("closet", "storage"), ("storage", "storage"), ("pantry", "storage"),
        ("laundry", "utility"), ("mechanical", "utility"), ("mech", "utility"),
        ("balcony", "balcony"), ("terrace", "balcony"), ("deck", "balcony"),
        ("garage", "garage"), ("parking", "garage"),
        ("office", "office"), ("study", "office"), ("den", "office"),
    ]:
        if keyword in lower:
            return rtype
    return "other"


def _detect_floor(layer_name: str) -> tuple[int, str]:
    """Extract floor number from layer name conventions."""
    import re
    lower = layer_name.lower()

    patterns = [
        (r"(?:floor|flr|level|lvl|storey)[_\s-]*(\d+)", None),
        (r"(?:f|l)(\d+)", None),
        (r"basement|bsmt", (-1, "Basement")),
        (r"ground|gf|gr", (0, "Ground")),
        (r"roof|rf", (99, "Roof")),
    ]

    for pattern, fixed in patterns:
        m = re.search(pattern, lower)
        if m:
            if fixed:
                return fixed
            num = int(m.group(1))
            return (num, f"Floor {num}")

    return (1, "Floor 1")


def _strip_xref_prefix(layer_name: str) -> str:
    """Strip xref prefixes like 'xref-Name$0$' from layer names."""
    if "$0$" in layer_name:
        return layer_name.split("$0$", 1)[-1]
    return layer_name


def _is_wall_layer(layer_name: str) -> bool:
    lower = _strip_xref_prefix(layer_name).lower()
    return any(kw in lower for kw in ("wall", "a-wall", "struc", "partition", "outline"))


def _is_room_layer(layer_name: str) -> bool:
    lower = _strip_xref_prefix(layer_name).lower()
    return any(kw in lower for kw in ("room", "area", "space", "hatch", "fill", "zone", "case", "footprint"))


def _is_door_window(block_name: str) -> str | None:
    lower = block_name.lower()
    if any(kw in lower for kw in ("door", "dr", "entry")):
        return "door"
    if any(kw in lower for kw in ("window", "win", "glazing")):
        return "window"
    return None


def _get_polyline_points(entity) -> list[tuple[float, float]]:
    """Extract 2D points from a polyline entity."""
    try:
        if hasattr(entity, "get_points"):
            return [(p[0], p[1]) for p in entity.get_points(format="xy")]
        if hasattr(entity, "vertices"):
            return [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
    except Exception:
        pass
    return []


def _centre_coords(
    plans: list[FloorPlan],
) -> tuple[list[FloorPlan], dict]:
    """Shift all coordinates so the centroid is at origin. Return (plans, bounds)."""
    all_x: list[float] = []
    all_y: list[float] = []

    for fp in plans:
        for w in fp.walls:
            all_x.extend([w.start[0], w.end[0]])
            all_y.extend([w.start[1], w.end[1]])
        for r in fp.rooms:
            for px, py in r.polygon:
                all_x.append(px)
                all_y.append(py)
        for o in fp.openings:
            all_x.append(o.position[0])
            all_y.append(o.position[1])

    if not all_x:
        return plans, {"min": [0, 0], "max": [0, 0]}

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2

    for fp in plans:
        for w in fp.walls:
            w.start = (w.start[0] - cx, w.start[1] - cy)
            w.end = (w.end[0] - cx, w.end[1] - cy)
        for r in fp.rooms:
            r.polygon = [(px - cx, py - cy) for px, py in r.polygon]
        for o in fp.openings:
            o.position = (o.position[0] - cx, o.position[1] - cy)

    bounds = {
        "min": [min_x - cx, min_y - cy],
        "max": [max_x - cx, max_y - cy],
    }
    return plans, bounds


def _nearest_room(rooms: list[Room], x: float, y: float) -> Room | None:
    """Find the room whose centroid is closest to (x, y)."""
    best = None
    best_dist = float("inf")
    for room in rooms:
        if not room.polygon:
            continue
        cx = sum(p[0] for p in room.polygon) / len(room.polygon)
        cy = sum(p[1] for p in room.polygon) / len(room.polygon)
        d = math.hypot(x - cx, y - cy)
        if d < best_dist:
            best_dist = d
            best = room
    return best


def parse_dxf(file_bytes: bytes) -> dict:
    """Parse a DXF file into structured floor plan data.

    Returns:
        {
            "floor_plans": [
                {
                    "floor_number": int,
                    "floor_label": str,
                    "walls": [{start, end, thickness_m, type}],
                    "rooms": [{name, type, polygon, area_m2}],
                    "openings": [{position, width_m, type}],
                }
            ],
            "units": "metres",
            "bounds": {"min": [x, y], "max": [x, y]},
        }
    """
    import tempfile

    import ezdxf

    # Write to temp file — ezdxf.readfile handles both ASCII and binary DXF
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        doc = ezdxf.readfile(tmp_path)
    finally:
        import os
        os.unlink(tmp_path)

    msp = doc.modelspace()

    # Group entities by detected floor
    floor_map: dict[int, FloorPlan] = {}
    labels: list[tuple[float, float, str, int]] = []  # x, y, text, floor_num

    def get_floor(layer: str) -> FloorPlan:
        num, label = _detect_floor(layer)
        if num not in floor_map:
            floor_map[num] = FloorPlan(floor_number=num, floor_label=label)
        return floor_map[num]

    for entity in msp:
        layer = entity.dxf.layer if hasattr(entity.dxf, "layer") else ""
        dxftype = entity.dxftype()
        fp = get_floor(layer)

        # Walls — LINE entities on wall layers
        if dxftype == "LINE" and _is_wall_layer(layer):
            start = entity.dxf.start
            end = entity.dxf.end
            fp.walls.append(WallSegment(
                start=(start.x, start.y),
                end=(end.x, end.y),
                type="exterior" if "ext" in layer.lower() else "interior",
            ))

        # Walls — LWPOLYLINE on wall layers
        elif dxftype == "LWPOLYLINE" and _is_wall_layer(layer):
            pts = _get_polyline_points(entity)
            for i in range(len(pts) - 1):
                fp.walls.append(WallSegment(
                    start=pts[i],
                    end=pts[i + 1],
                    type="exterior" if "ext" in layer.lower() else "interior",
                ))
            if entity.closed and len(pts) > 2:
                fp.walls.append(WallSegment(
                    start=pts[-1],
                    end=pts[0],
                    type="exterior" if "ext" in layer.lower() else "interior",
                ))

        # Rooms — closed LWPOLYLINE on room layers
        elif dxftype == "LWPOLYLINE" and _is_room_layer(layer):
            pts = _get_polyline_points(entity)
            if len(pts) >= 3:
                area = _polygon_area(pts)
                fp.rooms.append(Room(
                    name=layer,
                    type=_classify_room(layer),
                    polygon=pts,
                    area_m2=round(area, 2),
                ))

        # Rooms — HATCH entities (hatches are commonly used for room fills on any layer)
        elif dxftype == "HATCH":
            try:
                for path in entity.paths:
                    if hasattr(path, "vertices"):
                        pts = [(v[0], v[1]) for v in path.vertices]
                        if len(pts) >= 3:
                            area = _polygon_area(pts)
                            # Skip unrealistically large hatches (>500m2 likely borders/title blocks)
                            if area > 500:
                                continue
                            fp.rooms.append(Room(
                                name=layer,
                                type=_classify_room(layer),
                                polygon=pts,
                                area_m2=round(area, 2),
                            ))
            except Exception:
                pass

        # Text labels
        elif dxftype in ("TEXT", "MTEXT"):
            try:
                insert = entity.dxf.insert
                text = entity.dxf.text if dxftype == "TEXT" else entity.text
                if text and text.strip():
                    floor_num = _detect_floor(layer)[0]
                    labels.append((insert.x, insert.y, text.strip(), floor_num))
            except Exception:
                pass

        # Doors/windows — INSERT (block references)
        elif dxftype == "INSERT":
            block_name = entity.dxf.name if hasattr(entity.dxf, "name") else ""
            opening_type = _is_door_window(block_name)
            if opening_type:
                insert = entity.dxf.insert
                # Estimate width from block scale
                sx = getattr(entity.dxf, "xscale", 1.0)
                width = abs(sx) if abs(sx) > 0.1 else 0.9
                fp.openings.append(Opening(
                    position=(insert.x, insert.y),
                    width_m=round(width, 2),
                    type=opening_type,
                ))

    # If no floors detected, create a default floor 1
    if not floor_map:
        floor_map[1] = FloorPlan(floor_number=1, floor_label="Floor 1")

    # Match text labels to nearest rooms
    # Strip DXF formatting codes (%%u = underline, %%o = overline, etc.)
    import re
    for x, y, text, floor_num in labels:
        clean_text = re.sub(r"%%[a-zA-Z]", "", text).strip()
        if not clean_text or floor_num not in floor_map:
            continue
        # Only match room-like labels (skip dimension text, notes, etc.)
        if _classify_room(clean_text) == "other" and not any(
            kw in clean_text.lower() for kw in ("room", "hall", "closet", "porch", "garage", "foyer", "entry")
        ):
            continue
        room = _nearest_room(floor_map[floor_num].rooms, x, y)
        if room:
            room.name = clean_text
            room.type = _classify_room(clean_text)

    # Post-process: remove oversized rooms (likely border/title-block hatches)
    # Cap at 500 m2 — any real room above this is a data error
    for fp in floor_map.values():
        fp.rooms = [r for r in fp.rooms if r.area_m2 <= 500]

    plans = sorted(floor_map.values(), key=lambda fp: fp.floor_number)
    plans, bounds = _centre_coords(plans)

    # Serialize to dict
    def _serialize_plan(fp: FloorPlan) -> dict:
        return {
            "floor_number": fp.floor_number,
            "floor_label": fp.floor_label,
            "walls": [
                {"start": list(w.start), "end": list(w.end), "thickness_m": w.thickness_m, "type": w.type}
                for w in fp.walls
            ],
            "rooms": [
                {"name": r.name, "type": r.type, "polygon": [list(p) for p in r.polygon], "area_m2": r.area_m2}
                for r in fp.rooms
            ],
            "openings": [
                {"position": list(o.position), "width_m": o.width_m, "type": o.type}
                for o in fp.openings
            ],
        }

    return {
        "floor_plans": [_serialize_plan(fp) for fp in plans],
        "units": "metres",
        "bounds": bounds,
    }
