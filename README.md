# ECG Axis Calculator

> **Domain:** Cardiovascular Medicine & Hemodynamic Analytics  
> **Reference Guidelines & Standards:** `AHA/ACC Practice Guidelines & ESC Clinical Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

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

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`classify_axis()`**: Classify a QRS axis in degrees.

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
- **`quick_axis()`**: Determine QRS axis quadrant from net QRS amplitudes of leads I and aVF.

This is the standard bedside method for rapid axis determination.

Parameters:
    lead_i_net:   net QRS amplitude in lead I (R - S, in mV or mm)
    lead_avf_net: net QRS amplitude in lead aVF (R - S, in mV or mm)

Returns a dict with quadrant, approximate axis, and classification.
- **`calculate_axis()`**: Calculate QRS axis from any two limb leads.

Parameters:
    lead1_name: name of first lead (e.g. 'I', 'II', 'aVF', etc.)
    lead1_net:  net QRS amplitude of first lead (R - S)
    lead2_name: name of second lead
    lead2_net:  net QRS amplitude of second lead (R - S)

Returns a dict with the calculated axis and classification.
- **`calculate_axis_from_leads()`**: Estimate QRS axis from multiple limb lead net amplitudes.

Parameters:
    leads_dict: dict mapping lead names to net QRS amplitudes,
                e.g. {"I": 0.5, "II": 0.8, "aVF": 0.3}

Uses a least-squares approach: for each pair of leads, compute
the axis, then return the circular mean.

Returns a dict with the estimated axis and all pairwise results.
- **`process_csv()`**: Process a CSV file of ECG lead amplitudes and compute axes.

Expected columns: at minimum lead_i_net and lead_avf_net for quick axis.
Optionally any columns named after leads (I, II, III, aVR, aVL, aVF).

---

## 📐 Mathematical Formulation & Logic

```text
  Calculate precise axis using atan2
  """Calculate frontal plane axis from two lead net amplitudes and their angles.
  """Calculate QRS axis from any two limb leads.
  Returns a dict with the calculated axis and classification.
  result = calculate_axis(l1, valid_leads[l1], l2, valid_leads[l2])
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --lead-i <value> --lead-avf <value> --lead1-name <value> --lead1-net <value>
```

### Parameter Reference
- `--lead-i`: Specifies input measurement or parameter value.
- `--lead-avf`: Specifies input measurement or parameter value.
- `--lead1-name`: Specifies input measurement or parameter value.
- `--lead1-net`: Specifies input measurement or parameter value.
- `--lead2-name`: Specifies input measurement or parameter value.
- `--lead2-net`: Specifies input measurement or parameter value.
- `--leads`: Specifies input measurement or parameter value.
- `--input`: Specifies input measurement or parameter value.
- `--output`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `id` | Parameter / observation metric | Required |
| `value` | Parameter / observation metric | Required |
| `qty` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t ecg-axis-calculator .
docker run -p 8000:8000 ecg-axis-calculator
```
