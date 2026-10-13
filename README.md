# ECG Axis Calculator

Estimate the **frontal-plane mean QRS axis** from signed ECG limb-lead amplitudes. Includes a standalone browser calculator, dependency-free Python calculation functions and CLI, CSV batch processing, and a separate demonstration FastAPI supervisor.

## What works

- **Browser:** calculate from any two different frontal limb leads; fit multiple limb leads by ordinary least squares; visualize the calculated direction; process and download CSV results locally.
- **Python:** `quick_axis`, `calculate_axis`, `calculate_axis_from_leads`, and `process_csv` in `ecg_axis.py`.
- **CLI:** `quick`, `precise`, `multi`, `batch`, `audit`, `chat`, `verify-audit`, and `serve` commands.
- **Optional API:** synthetic task auditing and deterministic mock chat, separate from axis estimation. The demo's arbitrary alert thresholds **are not validated medical decision rules**.

### Interpretation

| QRS axis (adult conventional limits) | Classification |
| --- | --- |
| −30° through +90° | Normal |
| −90° through below −30° | Left axis deviation |
| Above +90° through +180° | Right axis deviation |
| Below −90° toward −180° | Extreme/northwest axis |

Angle endpoints near ±180° represent the same physical direction. The calculation uses `atan2` to recover both vector components, not a one-argument arctangent. The common positive-I/negative-aVF sign pattern includes **both** a normal borderline interval (0° to −30°) and left deviation; classification uses the calculated angle rather than only the sign quadrant. If both orthogonal components are zero, the result is *indeterminate*.

For any two lead directions θ₁, θ₂, we solve the measured projections of an unknown vector `(x, y)`:

```text
A1 = x cos(θ1) + y sin(θ1)
A2 = x cos(θ2) + y sin(θ2)
axis = atan2(y, x)
```

For three or more measured limb leads, `calculate_axis_from_leads` minimizes squared projection residuals with equal weights. All input amplitudes must be net, signed, finite values in the **same unit**. This simplified vector model may not reproduce the axis reported by an automated ECG interpretation system for complex morphologies.

## Use the browser calculator

The `web/` directory is an independent static HTML/CSS/JavaScript application. No installation, server-side Python, Pyodide, external model service, or backend API is needed. Open `web/index.html` directly or serve locally:

```bash
python -m http.server 8080 --directory web
# Visit http://localhost:8080/
```

Enter two signed amplitudes or choose *Multi-lead fit*. For batches, select a CSV with `lead_i_net,lead_avf_net` or at least two standard limb-lead columns (`I, II, III, aVR, aVL, aVF`), then select **Process & download CSV**. The browser limits files to 2 MB and 10,000 data rows. A corrected sample is in `sample.csv`.

**Privacy:** Browser input and CSV data are processed in your browser; the application does not send them to a server or store them persistently. Do not enter identifiable patient data into any deployed demo API. The server-side regular-expression identifier guard is only a limited heuristic, **not** a guarantee of de-identification or regulatory compliance.

## Python CLI

Requires Python **3.10–3.13** for the tested development configurations. The calculation module itself uses the Python standard library.

```bash
python cli.py quick --lead-i 1.0 --lead-avf -0.1
python cli.py precise --lead1-name aVF --lead1-net 0.5 --lead2-name I --lead2-net 0.87
python cli.py multi --leads '{"I":0.87,"II":0.87,"aVF":0.50}'
python cli.py batch --input sample.csv --output results.csv
```

To run the optional *demonstration* API:

```bash
python -m pip install -r requirements-api.txt
python cli.py serve  # localhost:8000; OpenAPI at /docs
```

The API provides `/health`, `/metrics` (JSON), `/api/audit`, `/api/chat` (mock only), and `/api/audit/logs`. The static `openapi_spec.json` is a summary; the dynamically generated `/openapi.json` reflects installed FastAPI/Pydantic versions. The audit chain uses HMAC-SHA256 verification but lives **only in process memory**. Supply an externally managed `AUDIT_SECRET_KEY` for a consistent key across runs; this alone does not persist the logs.

### Containers

```bash
docker build -t ecg-axis-calculator .
docker run --rm -p 127.0.0.1:8000:8000 -e AUDIT_SECRET_KEY="replace-with-long-random-secret" ecg-axis-calculator

# Or set AUDIT_SECRET_KEY securely in your shell, then:
docker compose up --build
```

Do not publish the demonstration API to the internet without real authentication, access controls, rate limiting, and an appropriate privacy assessment.

## Development and testing

```bash
python -m pip install -r requirements-api.txt "pytest>=8,<10"
python -m pytest -q
node --check web/calculator.js
node --test web/calculator.test.cjs
```

CI runs Python tests on four interpreter versions, JavaScript unit tests, a dependency vulnerability check, and a Docker build/health smoke test. The standalone application has no Node runtime dependencies and targets current desktop and mobile browsers supporting modern JavaScript, the File API, SVG, and Blob downloads.

## Scope and limitations

The repository also contains a synthetic supervisor, alert workers, generic enrichment stubs, and a traffic simulator. These are **demonstration scaffolding**, not validated 12-lead waveform streaming, echocardiographic strain analysis, clinician supervision, machine-learning inference, or clinical-grade decision support. No external model providers are implemented despite legacy provider labels. Clinical interpretation requires review of the original ECG and patient context.

The calculator is intended for **education and research**, not autonomous diagnosis or treatment.

## License

[MIT](LICENSE).
