#!/usr/bin/env python3
"""
ECG Axis Calculator
===================

Determines the frontal plane QRS axis from ECG limb lead amplitudes.

Quick axis determination (leads I and aVF):
    Lead I positive, aVF positive  → Normal axis (-30° to +90°)
    Lead I positive, aVF negative  → Left axis deviation (-30° to -90°)
    Lead I negative, aVF positive  → Right axis deviation (+90° to +180°)
    Lead I negative, aVF negative  → Extreme axis / northwest axis (-90° to -180°)

Precise axis calculation using the hexaxial reference system:
    Any two leads separated by 30° can be used. The standard approach
    uses leads I (0°) and aVF (+90°):
        axis = atan2(aVF_net, I_net) in degrees

    For any two leads with known angles:
        axis = atan2(lead2_net * sin(θ1) - lead1_net * sin(θ2),
                     lead1_net * cos(θ2) - lead2_net * cos(θ1))

    where θ1, θ2 are the angles of the two leads in the hexaxial system.

Hexaxial reference system (frontal plane):
    Lead I:   0°
    Lead II:  +60°
    Lead III: +120°
    aVR:      -150° (or +210°)
    aVL:      -30°  (or +330°)
    aVF:      +90°

Stdlib only — no external dependencies.
"""

import math

# ── Hexaxial reference system ────────────────────────────────────────

LEAD_ANGLES = {
    "I":   0.0,
    "II":  60.0,
    "III": 120.0,
    "aVR": -150.0,
    "AVR": -150.0,
    "aVL": -30.0,
    "AVL": -30.0,
    "aVF": 90.0,
    "AVF": 90.0,
}


def _normalize_lead_name(name):
    """Normalize a lead name to match LEAD_ANGLES keys.

    Handles: 'avf' -> 'aVF', 'AVF' -> 'AVF', 'I' -> 'I', etc.
    """
    upper = name.upper()
    # Direct match first
    if name in LEAD_ANGLES:
        return name
    if upper in LEAD_ANGLES:
        return upper
    # Try standard ECG notation: lowercase 'a' + uppercase rest
    if len(upper) >= 3 and upper[0] == "A":
        standard = "a" + upper[1:]
        if standard in LEAD_ANGLES:
            return standard
    return name  # Return as-is; caller will handle error


# ── Axis classification ──────────────────────────────────────────────

def classify_axis(degrees):
    """Classify a QRS axis in degrees.

    Returns one of:
        'normal'              : -30° to +90°
        'left_axis_deviation' : -30° to -90°
        'right_axis_deviation': +90° to +180°
        'extreme_axis'        : -90° to -180° (northwest axis)

    Boundaries:
        Normal:    -30 ≤ axis ≤ +90
        LAD:       -90 ≤ axis < -30
        RAD:       +90 < axis ≤ +180
        Extreme:   -180 ≤ axis < -90
    """
    # Normalize to -180 to +180 range
    d = degrees % 360
    if d > 180:
        d -= 360
    # Handle exact -180 boundary (180 % 360 = 180, which is RAD; but -180 should be extreme)
    if degrees == -180 or abs(degrees + 180) < 1e-9:
        return "extreme_axis"

    if -30 <= d <= 90:
        return "normal"
    elif -90 <= d < -30:
        return "left_axis_deviation"
    elif 90 < d <= 180:
        return "right_axis_deviation"
    else:  # -180 < d < -90
        return "extreme_axis"


# ── Quick axis determination (I + aVF) ──────────────────────────────

def quick_axis(lead_i_net, lead_avf_net):
    """Determine QRS axis quadrant from net QRS amplitudes of leads I and aVF.

    This is the standard bedside method for rapid axis determination.

    Parameters:
        lead_i_net:   net QRS amplitude in lead I (R - S, in mV or mm)
        lead_avf_net: net QRS amplitude in lead aVF (R - S, in mV or mm)

    Returns a dict with quadrant, approximate axis, and classification.
    """
    if lead_i_net > 0 and lead_avf_net > 0:
        quadrant = "normal"
    elif lead_i_net > 0 and lead_avf_net < 0:
        quadrant = "left_axis_deviation"
    elif lead_i_net < 0 and lead_avf_net > 0:
        quadrant = "right_axis_deviation"
    elif lead_i_net < 0 and lead_avf_net < 0:
        quadrant = "extreme_axis"
    else:
        # One or both are zero — indeterminate
        quadrant = "indeterminate"

    # Calculate precise axis using atan2
    axis_deg = _precise_axis_from_two_leads(
        lead_i_net, 0.0, lead_avf_net, 90.0
    )

    return {
        "lead_i_net": lead_i_net,
        "lead_avf_net": lead_avf_net,
        "axis_degrees": round(axis_deg, 1),
        "classification": classify_axis(axis_deg) if quadrant != "indeterminate" else "indeterminate",
        "quadrant": quadrant,
    }


# ── Precise axis calculation ─────────────────────────────────────────

def _precise_axis_from_two_leads(val1, angle1_deg, val2, angle2_deg):
    """Calculate frontal plane axis from two lead net amplitudes and their angles.

    Derived from Cramer's rule on the projection equations:
        A1 = |V| * cos(axis - θ1)
        A2 = |V| * cos(axis - θ2)

    Solving for axis:
        y = val2 * cos(θ1) - val1 * cos(θ2)
        x = val1 * sin(θ2) - val2 * sin(θ1)
        axis = atan2(y, x)
    """
    a1 = math.radians(angle1_deg)
    a2 = math.radians(angle2_deg)

    y = val2 * math.cos(a1) - val1 * math.cos(a2)
    x = val1 * math.sin(a2) - val2 * math.sin(a1)

    if abs(x) < 1e-12 and abs(y) < 1e-12:
        return float("nan")

    axis_rad = math.atan2(y, x)
    return math.degrees(axis_rad)


def calculate_axis(lead1_name, lead1_net, lead2_name, lead2_net):
    """Calculate QRS axis from any two limb leads.

    Parameters:
        lead1_name: name of first lead (e.g. 'I', 'II', 'aVF', etc.)
        lead1_net:  net QRS amplitude of first lead (R - S)
        lead2_name: name of second lead
        lead2_net:  net QRS amplitude of second lead (R - S)

    Returns a dict with the calculated axis and classification.
    """
    l1 = _normalize_lead_name(lead1_name)
    l2 = _normalize_lead_name(lead2_name)

    if l1 not in LEAD_ANGLES:
        raise ValueError(f"Unknown lead '{lead1_name}'. Valid: I, II, III, aVR, aVL, aVF")
    if l2 not in LEAD_ANGLES:
        raise ValueError(f"Unknown lead '{lead2_name}'. Valid: I, II, III, aVR, aVL, aVF")

    a1 = LEAD_ANGLES[l1]
    a2 = LEAD_ANGLES[l2]

    # Check that leads are not the same angle (would be indeterminate)
    if abs(a1 - a2) < 1e-6 or abs(abs(a1 - a2) - 360) < 1e-6:
        raise ValueError(f"Leads {l1} and {l2} have the same angle; need two different leads")

    axis_deg = _precise_axis_from_two_leads(lead1_net, a1, lead2_net, a2)

    if math.isnan(axis_deg):
        classification = "indeterminate"
    else:
        classification = classify_axis(axis_deg)

    return {
        "lead1": l1,
        "lead1_net": lead1_net,
        "lead2": l2,
        "lead2_net": lead2_net,
        "axis_degrees": round(axis_deg, 1) if not math.isnan(axis_deg) else None,
        "classification": classification,
    }


# ── Multi-lead axis estimation ───────────────────────────────────────

def calculate_axis_from_leads(leads_dict):
    """Estimate QRS axis from multiple limb lead net amplitudes.

    Parameters:
        leads_dict: dict mapping lead names to net QRS amplitudes,
                    e.g. {"I": 0.5, "II": 0.8, "aVF": 0.3}

    Uses a least-squares approach: for each pair of leads, compute
    the axis, then return the circular mean.

    Returns a dict with the estimated axis and all pairwise results.
    """
    valid_leads = {}
    for name, val in leads_dict.items():
        normalized = _normalize_lead_name(name)
        if normalized in LEAD_ANGLES:
            valid_leads[normalized] = float(val)

    if len(valid_leads) < 2:
        raise ValueError("Need at least 2 valid limb lead measurements")

    # Compute axis from all pairs and take circular mean
    names = sorted(valid_leads.keys())
    axes = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            l1, l2 = names[i], names[j]
            result = calculate_axis(l1, valid_leads[l1], l2, valid_leads[l2])
            if result["axis_degrees"] is not None:
                axes.append(result["axis_degrees"])

    if not axes:
        return {
            "axis_degrees": None,
            "classification": "indeterminate",
            "n_leads": len(valid_leads),
            "pairwise_axes": [],
        }

    # Circular mean (convert to radians, average sin and cos)
    sin_sum = sum(math.sin(math.radians(a)) for a in axes)
    cos_sum = sum(math.cos(math.radians(a)) for a in axes)
    mean_axis = math.degrees(math.atan2(sin_sum, cos_sum))

    return {
        "axis_degrees": round(mean_axis, 1),
        "classification": classify_axis(mean_axis),
        "n_leads": len(valid_leads),
        "pairwise_axes": [round(a, 1) for a in axes],
    }


# ── CSV batch processing ─────────────────────────────────────────────

def _validate_safe_path(path, param_name):
    """Validate that a file path is safe (no path traversal)."""
    import os
    # Reject paths with null bytes
    if "\x00" in path:
        raise ValueError(f"{param_name} contains null bytes")
    # Reject path traversal attempts
    normalized = os.path.normpath(path)
    if ".." in normalized.split(os.sep):
        raise ValueError(f"{param_name} contains path traversal sequences")
    return normalized


def process_csv(input_path, output_path):
    """Process a CSV file of ECG lead amplitudes and compute axes.

    Expected columns: at minimum lead_i_net and lead_avf_net for quick axis.
    Optionally any columns named after leads (I, II, III, aVR, aVL, aVF).
    """
    import csv
    import os

    # Validate paths
    input_path = _validate_safe_path(input_path, "input_path")
    output_path = _validate_safe_path(output_path, "output_path")

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    results = []
    for row in rows:
        try:
            # Try multi-lead if available
            lead_map = {}
            for key in row:
                normalized = _normalize_lead_name(key)
                if normalized in LEAD_ANGLES:
                    try:
                        lead_map[normalized] = float(row[key])
                    except (ValueError, TypeError):
                        pass

            if len(lead_map) >= 2:
                res = calculate_axis_from_leads(lead_map)
            elif "lead_i_net" in row and "lead_avf_net" in row:
                res = quick_axis(float(row["lead_i_net"]), float(row["lead_avf_net"]))
            else:
                res = {"error": "Need at least 2 lead measurements"}
        except (ValueError, TypeError, KeyError) as e:
            res = {"error": str(e)}

        merged = {**row, **{k: str(v) for k, v in res.items()}}
        results.append(merged)

    all_keys = set()
    for r in results:
        all_keys.update(r.keys())
    extra = sorted(k for k in all_keys if k not in fieldnames)
    out_fields = fieldnames + extra

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(results)

    return results
