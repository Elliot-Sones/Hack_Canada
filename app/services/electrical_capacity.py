"""Deterministic electrical capacity analysis engine.

Calculates building demand using CEC Rule 8-200 tables and scores
nearby grid infrastructure (substations, transformers, power lines)
to produce an adequacy verdict.

No AI involved — pure deterministic calculations from code standards.
"""

from __future__ import annotations

import math

from app.data.electrical_standards import (
    CEC_DEMAND_CALCULATIONS,
    TORONTO_HYDRO_SERVICE_RATINGS,
    VOLTAGE_TIERS,
)


# ---------------------------------------------------------------------------
# CEC demand calculation
# ---------------------------------------------------------------------------

def _get_multi_unit_factor(num_units: int) -> float:
    """Interpolate CEC multi-unit demand factor from the table."""
    table = CEC_DEMAND_CALCULATIONS["residential"]["multi_unit_demand_factors"]
    if num_units <= 1:
        return 1.0
    breakpoints = sorted(table.keys())
    for i, bp in enumerate(breakpoints):
        if num_units <= bp:
            if i == 0:
                return table[bp]
            prev_bp = breakpoints[i - 1]
            prev_val = table[prev_bp]
            curr_val = table[bp]
            ratio = (num_units - prev_bp) / (bp - prev_bp)
            return prev_val + ratio * (curr_val - prev_val)
    return table[breakpoints[-1]]


def calculate_demand(
    building_type: str,
    num_units: int = 1,
    total_area_m2: float | None = None,
    num_floors: int | None = None,
    building_subtype: str | None = None,
    has_ev_charging: bool = False,
    has_electric_heating: bool = False,
) -> dict:
    """Calculate estimated electrical demand in watts and amps.

    Returns dict with: demand_w, demand_kw, demand_amps, voltage, breakdown.
    """
    area = total_area_m2 or 150.0  # default modest house
    breakdown: list[str] = []

    if building_type == "residential":
        cfg = CEC_DEMAND_CALCULATIONS["residential"]
        base = cfg["base_load_w"]
        area_per_unit = area / max(num_units, 1)
        area_load = area_per_unit * cfg["area_factor_w_per_m2"]
        unit_demand = base + area_load
        breakdown.append(f"Base load: {base:,.0f} W")
        breakdown.append(f"Area load ({area_per_unit:.0f} m²): {area_load:,.0f} W")

        # Standard appliance loads
        appliances = cfg["appliance_loads"]
        for name in ("electric_range", "electric_dryer", "electric_water_heater"):
            app = appliances[name]
            load = app["watts"] * app["demand_factor"]
            unit_demand += load
            breakdown.append(f"{name.replace('_', ' ').title()}: {load:,.0f} W")

        if has_ev_charging:
            ev = appliances["ev_charger_l2"]
            load = ev["watts"] * ev["demand_factor"]
            unit_demand += load
            breakdown.append(f"EV Charger L2: {load:,.0f} W")

        if has_electric_heating:
            htg = appliances["electric_heating_per_m2"]
            load = area_per_unit * htg["watts"] * htg["demand_factor"]
            unit_demand += load
            breakdown.append(f"Electric heating: {load:,.0f} W")

        factor = _get_multi_unit_factor(num_units)
        total_w = unit_demand * num_units * factor
        breakdown.append(f"Multi-unit factor ({num_units} units): {factor:.2f}")
        voltage = 240 if num_units <= 2 else 208

    elif building_type == "commercial":
        cfg = CEC_DEMAND_CALCULATIONS["commercial"]
        subtype = building_subtype or "office"
        w_per_m2 = cfg["w_per_m2_by_subtype"].get(subtype, 55)
        base_load = area * w_per_m2
        total_w = base_load * cfg["hvac_factor"] * cfg["lighting_factor"]
        breakdown.append(f"Base ({subtype}): {area:.0f} m² × {w_per_m2} W/m² = {base_load:,.0f} W")
        breakdown.append(f"HVAC factor: ×{cfg['hvac_factor']}")
        breakdown.append(f"Lighting factor: ×{cfg['lighting_factor']}")
        voltage = 600 if total_w > 100_000 else 208

    elif building_type == "industrial":
        cfg = CEC_DEMAND_CALCULATIONS["industrial"]
        subtype = building_subtype or "light_manufacturing"
        w_per_m2 = cfg["w_per_m2_by_subtype"].get(subtype, 80)
        base_load = area * w_per_m2
        total_w = base_load * cfg["motor_load_factor"]
        breakdown.append(f"Base ({subtype}): {area:.0f} m² × {w_per_m2} W/m² = {base_load:,.0f} W")
        breakdown.append(f"Motor load factor: ×{cfg['motor_load_factor']}")
        voltage = 600

    else:
        total_w = area * 50
        voltage = 208
        breakdown.append(f"Default estimate: {area:.0f} m² × 50 W/m²")

    demand_kw = total_w / 1000
    demand_amps = total_w / (voltage * (math.sqrt(3) if voltage > 240 else 1))

    return {
        "demand_w": round(total_w, 0),
        "demand_kw": round(demand_kw, 1),
        "demand_amps": round(demand_amps, 1),
        "voltage": voltage,
        "breakdown": breakdown,
    }


# ---------------------------------------------------------------------------
# Infrastructure scoring — from nearby features
# ---------------------------------------------------------------------------

def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance in meters between two WGS84 points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _classify_voltage_kv(voltage_raw: str | None) -> float:
    """Parse a raw voltage string into kV (float)."""
    if not voltage_raw:
        return 0.0
    s = str(voltage_raw).strip().lower().replace(",", "")
    # Handle "115 kV", "27.6kV", "13800", "13.8 kv", "120 V" etc.
    s = s.replace("kv", "").replace("v", "").strip()
    try:
        val = float(s)
    except ValueError:
        # Try extracting first number
        import re
        m = re.search(r"[\d.]+", s)
        if m:
            val = float(m.group())
        else:
            return 0.0
    # If > 1000, assume volts → convert to kV
    if val > 1000:
        val /= 1000
    return val


def _voltage_score(kv: float) -> float:
    """Score 0–30 based on voltage level of nearest infrastructure."""
    if kv >= 100:
        return 30  # Transmission nearby
    if kv >= 20:
        return 25  # Primary distribution
    if kv >= 5:
        return 20  # Secondary distribution
    if kv > 0:
        return 10  # Local
    return 0


def score_infrastructure(
    lat: float,
    lng: float,
    features: list[dict],
) -> dict:
    """Score nearby electrical infrastructure (0–100).

    Breakdown: proximity (40 pts) + voltage level (30 pts) + density (30 pts).
    Returns dict with score, nearest_substation, nearest_power_line, details.
    """
    nearest_sub = None
    nearest_sub_dist = float("inf")
    nearest_line = None
    nearest_line_dist = float("inf")
    sub_count = 0
    line_count = 0
    transformer_count = 0
    max_voltage_kv = 0.0

    for feat in features:
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})
        layer = props.get("layer_type", "")

        # Get representative point for distance
        gtype = geom.get("type", "")
        coords = geom.get("coordinates", [])
        if gtype == "Point" and len(coords) >= 2:
            pt_lng, pt_lat = coords[0], coords[1]
        elif gtype in ("LineString", "MultiLineString"):
            # Use midpoint of first segment
            if gtype == "MultiLineString" and coords:
                line_coords = coords[0]
            else:
                line_coords = coords
            if line_coords and len(line_coords) >= 2:
                mid_idx = len(line_coords) // 2
                pt_lng, pt_lat = line_coords[mid_idx][0], line_coords[mid_idx][1]
            else:
                continue
        else:
            continue

        dist = _haversine_m(lat, lng, pt_lat, pt_lng)
        voltage_kv = _classify_voltage_kv(props.get("voltage"))
        max_voltage_kv = max(max_voltage_kv, voltage_kv)

        if layer == "electrical_substation":
            sub_count += 1
            if dist < nearest_sub_dist:
                nearest_sub_dist = dist
                nearest_sub = {
                    "name": props.get("name", "Substation"),
                    "distance_m": round(dist, 0),
                    "voltage": props.get("voltage"),
                    "operator": props.get("operator"),
                }
        elif layer == "power_line":
            line_count += 1
            if dist < nearest_line_dist:
                nearest_line_dist = dist
                nearest_line = {
                    "distance_m": round(dist, 0),
                    "voltage": props.get("voltage"),
                    "voltage_kv": voltage_kv,
                    "operator": props.get("operator"),
                    "cables": props.get("cables"),
                }
        elif "transformer" in (props.get("power_type", "") or "").lower():
            transformer_count += 1

    # --- Proximity score (40 pts) ---
    proximity_score = 0
    if nearest_sub_dist < 500:
        proximity_score += 20
    elif nearest_sub_dist < 1000:
        proximity_score += 15
    elif nearest_sub_dist < 2000:
        proximity_score += 10
    elif nearest_sub_dist < 5000:
        proximity_score += 5

    if nearest_line_dist < 100:
        proximity_score += 20
    elif nearest_line_dist < 250:
        proximity_score += 15
    elif nearest_line_dist < 500:
        proximity_score += 10
    elif nearest_line_dist < 1000:
        proximity_score += 5

    # --- Voltage score (30 pts) ---
    v_score = _voltage_score(max_voltage_kv)

    # --- Density score (30 pts) ---
    density_score = 0
    density_score += min(sub_count * 5, 10)
    density_score += min(line_count * 3, 10)
    density_score += min(transformer_count * 5, 10)

    total = min(proximity_score + v_score + density_score, 100)

    return {
        "score": total,
        "proximity_score": proximity_score,
        "voltage_score": v_score,
        "density_score": density_score,
        "nearest_substation": nearest_sub,
        "nearest_power_line": nearest_line,
        "substations_nearby": sub_count,
        "power_lines_nearby": line_count,
        "transformers_nearby": transformer_count,
        "max_voltage_kv": max_voltage_kv,
    }


# ---------------------------------------------------------------------------
# Public API — capacity check
# ---------------------------------------------------------------------------

def check_capacity(
    lat: float,
    lng: float,
    features: list[dict],
    building_type: str = "residential",
    building_subtype: str | None = None,
    requested_amps: float | None = None,
    num_units: int = 1,
    total_area_m2: float | None = None,
    num_floors: int | None = None,
    has_ev_charging: bool = False,
    has_electric_heating: bool = False,
) -> dict:
    """Run full capacity check: demand estimate + infrastructure scoring + verdict."""

    demand = calculate_demand(
        building_type=building_type,
        num_units=num_units,
        total_area_m2=total_area_m2,
        num_floors=num_floors,
        building_subtype=building_subtype,
        has_ev_charging=has_ev_charging,
        has_electric_heating=has_electric_heating,
    )

    infra = score_infrastructure(lat, lng, features)
    score = infra["score"]

    # Verdict
    if not features:
        verdict = "unknown"
        confidence = 0.3
    elif score >= 70:
        verdict = "adequate"
        confidence = min(0.6 + score / 200, 0.95)
    elif score >= 40:
        verdict = "marginal"
        confidence = 0.5 + score / 300
    else:
        verdict = "insufficient"
        confidence = 0.4 + score / 400

    # Recommendations
    recs: list[str] = []

    # Service rating recommendation
    if building_type == "residential":
        if num_units <= 2:
            cat = "single_family"
        elif num_floors and num_floors <= 4:
            cat = "low_rise_residential"
        elif num_floors and num_floors <= 8:
            cat = "mid_rise_residential"
        else:
            cat = "high_rise_residential"
    elif building_type == "commercial":
        cat = "commercial_large" if (total_area_m2 or 0) > 2000 else "commercial_small"
    else:
        cat = "industrial"

    svc = TORONTO_HYDRO_SERVICE_RATINGS.get(cat, {})
    if svc:
        recs.append(
            f"Typical service for {cat.replace('_', ' ')}: "
            f"{svc['typical_amps']}A {svc['voltage']} {svc['phase']}-phase "
            f"({svc['service_type']})"
        )

    if demand["demand_amps"] > svc.get("typical_amps", 200):
        recs.append(
            f"Estimated demand ({demand['demand_amps']:.0f}A) exceeds typical "
            f"service rating ({svc.get('typical_amps', 200)}A) — upgrade likely required"
        )

    if verdict == "marginal":
        recs.append("Contact Toronto Hydro for service availability confirmation")
    elif verdict == "insufficient":
        recs.append("Grid upgrade or dedicated infrastructure may be required")
        recs.append("Request Toronto Hydro system impact assessment")

    if has_ev_charging:
        recs.append("EV charging adds significant load — ensure panel capacity includes EV circuits")

    recs.append("ESA permit required for all new electrical service installations (O.Reg 164/99)")

    return {
        "verdict": verdict,
        "confidence": round(confidence, 2),
        "estimated_demand_kw": demand["demand_kw"],
        "estimated_demand_amps": demand["demand_amps"],
        "infrastructure_score": score,
        "nearest_substation": infra["nearest_substation"],
        "nearest_power_line": infra["nearest_power_line"],
        "recommendations": recs,
        "demand_breakdown": demand["breakdown"],
        "infra_detail": {
            "proximity_score": infra["proximity_score"],
            "voltage_score": infra["voltage_score"],
            "density_score": infra["density_score"],
            "substations_nearby": infra["substations_nearby"],
            "power_lines_nearby": infra["power_lines_nearby"],
            "transformers_nearby": infra["transformers_nearby"],
        },
    }
