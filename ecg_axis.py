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

    For any two nonparallel leads, solve the two projection equations:
        A1 = x cos(θ1) + y sin(θ1)
        A2 = x cos(θ2) + y sin(θ2)
        axis = atan2(y, x)

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
    """Normalize a standard frontal-plane limb lead to its canonical name."""
    if not isinstance(name, str):
        return ""
    canonical = {"I": "I", "II": "II", "III": "III",
                 "AVR": "aVR", "AVL": "aVL", "AVF": "aVF"}
    return canonical.get(name.strip().upper(), name.strip())


def _finite_amplitude(value, label):
    """Reject missing, nonnumeric, and nonfinite amplitudes."""
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{label} must be a finite number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result

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
    if not math.isfinite(degrees):
        raise ValueError("Axis must be finite")
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
    """Calculate the axis from I/aVF and report its sign-based quadrant.

    The positive-I/negative-aVF quadrant spans normal (-30° to 0°) and
    left deviation. The numeric angle determines the classification.
    """
    i = _finite_amplitude(lead_i_net, "lead_i_net")
    avf = _finite_amplitude(lead_avf_net, "lead_avf_net")
    if i > 0 and avf > 0:
        quadrant = "normal"
    elif i > 0 and avf < 0:
        quadrant = "left_axis_deviation"
    elif i < 0 and avf > 0:
        quadrant = "right_axis_deviation"
    elif i < 0 and avf < 0:
        quadrant = "extreme_axis"
    else:
        quadrant = "indeterminate"
    axis_deg = _precise_axis_from_two_leads(i, 0.0, avf, 90.0)
    return {
        "lead_i_net": i,
        "lead_avf_net": avf,
        "axis_degrees": round(axis_deg, 1) if math.isfinite(axis_deg) else None,
        "classification": classify_axis(axis_deg) if math.isfinite(axis_deg) else "indeterminate",
        "quadrant": quadrant,
    }

# ── Precise axis calculation ─────────────────────────────────────────

def _precise_axis_from_two_leads(val1, angle1_deg, val2, angle2_deg):
    """Recover the QRS vector from two nonparallel lead projections."""
    a1, a2 = math.radians(angle1_deg), math.radians(angle2_deg)
    determinant = math.sin(a2 - a1)
    if abs(determinant) < 1e-12:
        raise ValueError("Lead axes are parallel and cannot define a unique QRS axis")
    x = (val1 * math.sin(a2) - val2 * math.sin(a1)) / determinant
    y = (val2 * math.cos(a1) - val1 * math.cos(a2)) / determinant
    if math.hypot(x, y) < 1e-12:
        return float("nan")
    return math.degrees(math.atan2(y, x))

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

    lead1_net = _finite_amplitude(lead1_net, "lead1_net")
    lead2_net = _finite_amplitude(lead2_net, "lead2_net")
    a1 = LEAD_ANGLES[l1]
    a2 = LEAD_ANGLES[l2]

    if abs(math.sin(math.radians(a2 - a1))) < 1e-12:
        raise ValueError(f"Leads {l1} and {l2} do not give independent axes")

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
    """Fit the frontal QRS vector to available limb-lead projections by OLS.

    Pairwise axes are returned as diagnostics for compatibility, but are not
    averaged; inconsistent/noisy observations contribute to a least-squares fit.
    """
    if not hasattr(leads_dict, "items"):
        raise ValueError("leads_dict must map lead names to amplitudes")
    valid_leads = {}
    for name, value in leads_dict.items():
        lead = _normalize_lead_name(name)
        if lead not in LEAD_ANGLES:
            continue
        amplitude = _finite_amplitude(value, lead)
        if lead in valid_leads and valid_leads[lead] != amplitude:
            raise ValueError(f"Conflicting measurements for alias {lead}")
        valid_leads[lead] = amplitude
    if len(valid_leads) < 2:
        raise ValueError("Need at least 2 valid limb lead measurements")

    cc = ss = cs = cb = sb = 0.0
    for lead, amplitude in valid_leads.items():
        theta = math.radians(LEAD_ANGLES[lead])
        c, sin_t = math.cos(theta), math.sin(theta)
        cc += c * c
        ss += sin_t * sin_t
        cs += c * sin_t
        cb += c * amplitude
        sb += sin_t * amplitude
    determinant = cc * ss - cs * cs
    if determinant <= 1e-12:
        raise ValueError("Lead measurements do not span two independent axes")
    x = (ss * cb - cs * sb) / determinant
    y = (cc * sb - cs * cb) / determinant
    axis = math.degrees(math.atan2(y, x)) if math.hypot(x, y) >= 1e-12 else None

    names = sorted(valid_leads)
    pairwise = []
    for i, lead1 in enumerate(names):
        for lead2 in names[i + 1:]:
            angle = _precise_axis_from_two_leads(
                valid_leads[lead1], LEAD_ANGLES[lead1],
                valid_leads[lead2], LEAD_ANGLES[lead2])
            if math.isfinite(angle):
                pairwise.append(round(angle, 1))
    return {
        "axis_degrees": round(axis, 1) if axis is not None else None,
        "classification": classify_axis(axis) if axis is not None else "indeterminate",
        "n_leads": len(valid_leads),
        "pairwise_axes": pairwise,
    }

# ── CSV batch processing ─────────────────────────────────────────────

def _validate_safe_path(path, param_name):
    """Validate that a file path is safe (no path traversal)."""
    import os
    path = os.fspath(path)
    # Reject paths with null bytes
    if "\x00" in path:
        raise ValueError(f"{param_name} contains null bytes")
    # Reject path traversal attempts
    path = os.fspath(path)
    if not path.strip():
        raise ValueError(f"{param_name} must not be empty")
    if ".." in path.replace(chr(92), "/").split("/"):
        raise ValueError(f"{param_name} contains path traversal sequences")
    return os.path.normpath(path)


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

    if os.path.abspath(input_path) == os.path.abspath(output_path):
        raise ValueError("Input and output CSV paths must differ")
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
