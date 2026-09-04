# ECG Axis Calculator

> **Domain:** Cardiovascular Medicine & Hemodynamic Analytics
> **Reference Guidelines & Standards:** AHA/ACC Practice Guidelines & ESC Clinical Standards

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

ECG Axis Calculator determines the frontal plane QRS axis from ECG limb lead amplitudes.

### Quick axis determination (leads I and aVF):
- Lead I positive, aVF positive → Normal axis (-30° to +90°)
- Lead I positive, aVF negative → Left axis deviation (-30° to -90°)
- Lead I negative, aVF positive → Right axis deviation (+90° to +180°)
- Lead I negative, aVF negative → Extreme axis / northwest axis (-90° to -180°)

### Precise axis calculation using the hexaxial reference system:
Any two leads separated by 30° can be used. The standard approach uses leads I (0°) and aVF (+90°):
```
axis = atan2(aVF_net, I_net) in degrees
```

For any two leads with known angles:
```
axis = atan2(lead2_net * sin(θ1) - lead1_net * sin(θ2),
             lead1_net * cos(θ2) - lead2_net * cos(θ1))
```
where θ1, θ2 are the angles of the two leads in the hexaxial system.

### Hexaxial reference system (frontal plane):
| Lead | Angle |
|------|-------|
| I    | 0°    |
| II   | +60°  |
| III  | +120° |
| aVR  | -150° (or +210°) |
| aVL  | -30° (or +330°) |
| aVF  | +90°  |

Stdlib only for core calculations — no external dependencies required.

---

## Key Capabilities & Algorithmic Modules

### Analytical Functions

- **`classify_axis()`**: Classify a QRS axis in degrees.

Returns one of:
- `'normal'`: -30° to +90°
- `'left_axis_deviation'`: -30° to -90°
- `'right_axis_deviation'`: +90° to +180°
- `'extreme_axis'`: -90° to -180° (northwest axis)

- **`quick_axis()`**: Determine QRS axis quadrant from net QRS amplitudes of leads I and aVF.

This is the standard bedside method for rapid axis determination.

Parameters:
- `lead_i_net`: net QRS amplitude in lead I (R - S, in mV or mm)
- `lead_avf_net`: net QRS amplitude in lead aVF (R - S, in mV or mm)

Returns a dict with quadrant, approximate axis, and classification.

- **`calculate_axis()`**: Calculate QRS axis from any two limb leads.

Parameters:
- `lead1_name`: name of first lead (e.g. 'I', 'II', 'aVF', etc.)
- `lead1_net`: net QRS amplitude of first lead (R - S)
- `lead2_name`: name of second lead
- `lead2_net`: net QRS amplitude of second lead (R - S)

Returns a dict with the calculated axis and classification.

- **`calculate_axis_from_leads()`**: Estimate QRS axis from multiple limb lead net amplitudes.

Parameters:
- `leads_dict`: dict mapping lead names to net QRS amplitudes, e.g. `{"I": 0.5, "II": 0.8, "aVF": 0.3}`

Uses a least-squares approach: for each pair of leads, compute the axis, then return the circular mean.

Returns a dict with the estimated axis and all pairwise results.

- **`process_csv()`**: Process a CSV file of ECG lead amplitudes and compute axes.

Expected columns: at minimum `lead_i_net` and `lead_avf_net` for quick axis. Optionally any columns named after leads (I, II, III, aVR, aVL, aVF).

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/ecg-axis-calculator.git
cd ecg-axis-calculator

# No external dependencies required for core functionality
# For API server and development:
pip install fastapi uvicorn pydantic pytest
```

---

## CLI Quickstart & Usage

### 1. Quick Axis (I + aVF)
```bash
python cli.py quick --lead-i 0.5 --lead-avf 0.3
```

### 2. Precise Axis from Two Leads
```bash
python cli.py precise --lead1-name I --lead1-net 0.5 --lead2-name aVF --lead2-net 0.3
```

### 3. Multi-Lead Axis
```bash
python cli.py multi --leads '{"I": 0.5, "II": 0.8, "aVF": 0.3}'
```

### 4. Batch CSV Processing
```bash
python cli.py batch -i input.csv -o results.csv
```

### 5. Supervisor Audit
```bash
python cli.py audit --task-id TASK-001 --primary-metric 12.0 --status-descriptor NOMINAL
```

### 6. Chat Query
```bash
python cli.py chat "Explain axis deviation patterns"
```

### 7. Verify Audit Trail
```bash
python cli.py verify-audit
```

### 8. Start API Server
```bash
python cli.py serve --host 0.0.0.0 --port 8000
```

---

## API Endpoints

When running the server (`python cli.py serve`), the following endpoints are available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus-compatible metrics |
| `/api/audit` | POST | Process task payload through supervisor |
| `/api/chat` | POST | Query supervisory chat system |
| `/api/audit/logs` | GET | Retrieve audit trail |

---

## Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

Set the `AUDIT_SECRET_KEY` environment variable for persistent audit integrity:
```bash
export AUDIT_SECRET_KEY="your-secure-random-key"
```

If not set, a random session key will be generated (with a warning), which is suitable for development but not for production.

---

## Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Run specific test files:
```bash
pytest test_ecg_axis.py -v          # Core ECG calculations
pytest tests/test_ecg_axis_calculator.py -v  # Enterprise features
pytest tests/test_enrichment.py -v   # Enrichment modules
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000
```

---

## Container Deployment

```bash
docker build -t ecg-axis-calculator .
docker run -p 8000:8000 ecg-axis-calculator
```

Or using docker-compose:

```bash
docker-compose up
```

---

## Project Structure

```
ecg-axis-calculator/
├── ecg_axis.py          # Core ECG axis calculation functions
├── cli.py               # Command-line interface
├── enrichment.py        # Domain enrichment features
├── simulator.py         # High-throughput simulation
├── agents/              # Enterprise agent framework
│   ├── base.py          # Security, PHI guard, audit trail
│   ├── models.py        # Pydantic data models
│   ├── supervisor.py    # Supervisor orchestrator
│   ├── workers.py       # Specialized worker agents
│   ├── api.py           # FastAPI REST server
│   ├── metrics.py       # Prometheus metrics
│   ├── streamer.py      # WebSocket telemetry
│   ├── learning.py      # Bayesian calibration engine
│   └── llm_factory.py   # LLM provider factory
├── web/
│   └── index.html       # Operations console UI
├── tests/               # Test suites
├── test_ecg_axis.py     # Core calculation tests
├── sample.csv           # Sample input data
├── Dockerfile           # Container definition
└── docker-compose.yml   # Compose configuration
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
