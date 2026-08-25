# ECG Axis Calculator

Determines the frontal plane QRS axis from ECG limb lead amplitudes using the hexaxial reference system.

## Axis Classification

| Classification | Range | Common Causes |
|---------------|-------|---------------|
| **Normal** | -30° to +90° | Healthy adults |
| **Left Axis Deviation** | -30° to -90° | LAFB, LVH, inferior MI |
| **Right Axis Deviation** | +90° to +180° | RVH, LPFB, PE, lateral MI |
| **Extreme (NW) Axis** | -90° to -180° | VT, severe RVH |

## Quick Axis Determination (I + aVF)

| Lead I | Lead aVF | Interpretation |
|--------|----------|---------------|
| Positive | Positive | Normal axis |
| Positive | Negative | Left axis deviation |
| Negative | Positive | Right axis deviation |
| Negative | Negative | Extreme axis |

## Hexaxial Reference System

| Lead | Angle |
|------|-------|
| I | 0° |
| II | +60° |
| III | +120° |
| aVR | -150° |
| aVL | -30° |
| aVF | +90° |

## Quick Start

```bash
# Quick axis from leads I and aVF
python cli.py quick --lead-i 0.5 --lead-avf 0.3

# Precise axis from any two leads
python cli.py precise --lead1-name I --lead1-net 0.5 --lead2-name II --lead2-net 0.8

# Multi-lead estimation
python cli.py multi --leads '{"I": 0.5, "II": 0.8, "aVF": 0.3}'

# Batch CSV processing
python cli.py batch -i sample.csv -o results.csv
```

## Python API

```python
from ecg_axis import quick_axis, calculate_axis, classify_axis

# Quick bedside determination
result = quick_axis(lead_i_net=0.5, lead_avf_net=0.3)
# {'axis_degrees': 31.0, 'classification': 'normal', ...}

# Precise axis from two leads
result = calculate_axis("I", 0.5, "aVF", -0.3)
# {'axis_degrees': -31.0, 'classification': 'left_axis_deviation', ...}

# Classify any axis value
classify_axis(45)   # 'normal'
classify_axis(-60)  # 'left_axis_deviation'
```

## Dependencies

Python standard library only. No external packages required.

## License

MIT License.
