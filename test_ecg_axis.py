"""Tests for ecg_axis.py — ECG Axis Calculator.

Run with: python -m pytest test_ecg_axis.py -v
"""
import math
import pytest
from ecg_axis import (
    classify_axis, quick_axis, calculate_axis,
    calculate_axis_from_leads, LEAD_ANGLES,
)


# ── Axis classification ─────────────────────────────────────────────

class TestClassifyAxis:
    def test_zero_degrees(self):
        assert classify_axis(0) == "normal"

    def test_positive_60(self):
        assert classify_axis(60) == "normal"

    def test_positive_90(self):
        assert classify_axis(90) == "normal"

    def test_negative_20(self):
        assert classify_axis(-20) == "normal"

    def test_negative_30_boundary(self):
        assert classify_axis(-30) == "normal"

    def test_left_axis_deviation(self):
        assert classify_axis(-45) == "left_axis_deviation"
        assert classify_axis(-60) == "left_axis_deviation"
        assert classify_axis(-89) == "left_axis_deviation"

    def test_right_axis_deviation(self):
        assert classify_axis(100) == "right_axis_deviation"
        assert classify_axis(150) == "right_axis_deviation"
        assert classify_axis(180) == "right_axis_deviation"

    def test_extreme_axis(self):
        assert classify_axis(-100) == "extreme_axis"
        assert classify_axis(-150) == "extreme_axis"
        assert classify_axis(-179) == "extreme_axis"

    def test_wrapping_360(self):
        # 270° should normalize to -90°
        assert classify_axis(270) == "left_axis_deviation"

    def test_wrapping_negative(self):
        # -180 should be extreme
        assert classify_axis(-180) == "extreme_axis"


# ── Quick axis (I + aVF) ────────────────────────────────────────────

class TestQuickAxis:
    def test_normal_both_positive(self):
        result = quick_axis(0.5, 0.3)
        assert result["quadrant"] == "normal"
        assert result["classification"] == "normal"

    def test_left_axis_i_pos_avf_neg(self):
        result = quick_axis(0.5, -0.3)
        assert result["quadrant"] == "left_axis_deviation"
        assert result["classification"] == "left_axis_deviation"

    def test_right_axis_i_neg_avf_pos(self):
        result = quick_axis(-0.5, 0.3)
        assert result["quadrant"] == "right_axis_deviation"
        assert result["classification"] == "right_axis_deviation"

    def test_extreme_both_negative(self):
        result = quick_axis(-0.5, -0.3)
        assert result["quadrant"] == "extreme_axis"
        assert result["classification"] == "extreme_axis"

    def test_axis_near_zero(self):
        # Lead I strongly positive, aVF near zero → axis near 0°
        result = quick_axis(1.0, 0.01)
        assert abs(result["axis_degrees"]) < 10

    def test_axis_near_90(self):
        # Lead I near zero, aVF strongly positive → axis near 90°
        result = quick_axis(0.01, 1.0)
        assert abs(result["axis_degrees"] - 90) < 10

    def test_axis_near_negative_90(self):
        # Lead I near zero, aVF strongly negative → axis near -90°
        result = quick_axis(0.01, -1.0)
        assert abs(result["axis_degrees"] + 90) < 10

    def test_indeterminate_both_zero(self):
        result = quick_axis(0, 0)
        assert result["quadrant"] == "indeterminate"


# ── Precise axis from two leads ─────────────────────────────────────

class TestPreciseAxis:
    def test_leads_i_and_ii(self):
        # Both positive → normal axis
        result = calculate_axis("I", 0.5, "II", 0.8)
        assert result["classification"] == "normal"

    def test_leads_i_and_avf(self):
        result = calculate_axis("I", 0.5, "aVF", 0.3)
        assert result["classification"] == "normal"

    def test_same_lead_raises(self):
        with pytest.raises(ValueError):
            calculate_axis("I", 0.5, "I", 0.3)

    def test_unknown_lead_raises(self):
        with pytest.raises(ValueError):
            calculate_axis("V1", 0.5, "I", 0.3)

    def test_case_insensitive(self):
        result = calculate_axis("i", 0.5, "avf", 0.3)
        assert result["lead1"] == "I"
        assert result["lead2"] == "aVF"

    def test_axis_45_degrees(self):
        # Equal positive amplitudes in I (0°) and aVF (90°) → ~45°
        result = calculate_axis("I", 1.0, "aVF", 1.0)
        assert abs(result["axis_degrees"] - 45) < 5


# ── Multi-lead axis ─────────────────────────────────────────────────

class TestMultiLeadAxis:
    def test_three_leads(self):
        result = calculate_axis_from_leads({"I": 0.5, "II": 0.8, "aVF": 0.3})
        assert result["n_leads"] == 3
        assert result["classification"] == "normal"
        assert len(result["pairwise_axes"]) == 3  # C(3,2) = 3 pairs

    def test_two_leads(self):
        result = calculate_axis_from_leads({"I": 0.5, "aVF": 0.3})
        assert result["n_leads"] == 2
        assert len(result["pairwise_axes"]) == 1

    def test_insufficient_leads(self):
        with pytest.raises(ValueError):
            calculate_axis_from_leads({"I": 0.5})

    def test_unknown_leads_ignored(self):
        result = calculate_axis_from_leads({"I": 0.5, "V1": 0.3, "aVF": 0.2})
        assert result["n_leads"] == 2  # V1 is not a limb lead


# ── Lead angles ─────────────────────────────────────────────────────

class TestLeadAngles:
    def test_all_six_leads_defined(self):
        # 6 standard leads + 3 uppercase aliases (AVR, AVL, AVF)
        assert len(LEAD_ANGLES) == 9
        for name in ["I", "II", "III", "aVR", "aVL", "aVF"]:
            assert name in LEAD_ANGLES

    def test_lead_i_is_zero(self):
        assert LEAD_ANGLES["I"] == 0.0

    def test_lead_avf_is_90(self):
        assert LEAD_ANGLES["aVF"] == 90.0


# ── Regression: order invariance, borderline quadrants, OLS ──────────

@pytest.mark.parametrize("a,b", [
    ("I", "aVF"), ("aVF", "I"),
    ("II", "aVL"), ("aVL", "II"),
    ("III", "aVR"), ("aVR", "III"),
])
def test_axis_independent_of_lead_order(a, b):
    target = math.radians(23.0)
    amp_a = math.cos(target - math.radians(LEAD_ANGLES[a]))
    amp_b = math.cos(target - math.radians(LEAD_ANGLES[b]))
    result = calculate_axis(a, amp_a, b, amp_b)
    assert result["axis_degrees"] == pytest.approx(23.0, abs=0.1)


def test_borderline_normal_quadrant():
    result = quick_axis(1.0, -0.1)
    assert result["quadrant"] == "left_axis_deviation"  # two-sign screening only
    assert result["classification"] == "normal"
    assert result["axis_degrees"] == pytest.approx(-5.7, abs=0.1)


def test_zero_vector_is_undefined():
    assert quick_axis(0, 0)["axis_degrees"] is None
    assert quick_axis(0, 0)["classification"] == "indeterminate"
    assert calculate_axis("I", 0, "aVF", 0)["axis_degrees"] is None
    assert calculate_axis_from_leads({"I": 0, "II": 0, "aVF": 0})["axis_degrees"] is None


@pytest.mark.parametrize("amplitude", [float("nan"), float("inf"), -float("inf"), "bad", None])
def test_invalid_amplitudes_rejected(amplitude):
    with pytest.raises(ValueError):
        quick_axis(amplitude, 0.5)
    with pytest.raises(ValueError):
        calculate_axis("I", 0.5, "II", amplitude)
    with pytest.raises(ValueError):
        calculate_axis_from_leads({"I": 1, "aVF": amplitude})


def test_multi_lead_ols_and_alias_deduplication():
    degrees = 37.0
    leads = {
        name: math.cos(math.radians(degrees - angle))
        for name, angle in [("I", 0), ("II", 60), ("aVF", 90), ("aVL", -30)]
    }
    leads["AVF"] = leads["aVF"]
    result = calculate_axis_from_leads(leads)
    assert result["axis_degrees"] == pytest.approx(degrees, abs=0.1)
    assert result["n_leads"] == 4
    assert len(result["pairwise_axes"]) == 6


def test_multi_lead_conflicting_aliases():
    with pytest.raises(ValueError, match="Conflicting"):
        calculate_axis_from_leads({"I": 1, "aVF": 0.5, "AVF": -0.5})


def test_multi_lead_uses_least_squares_not_pairwise_average():
    leads = {"I": 0.65, "II": 0.95, "III": 0.5, "aVF": 0.65}
    rows = [(math.cos(math.radians(LEAD_ANGLES[k])), math.sin(math.radians(LEAD_ANGLES[k])), v)
            for k, v in leads.items()]
    cc = sum(c*c for c, _, _ in rows)
    ss = sum(t*t for _, t, _ in rows)
    cs = sum(c*t for c, t, _ in rows)
    cb = sum(c*v for c, _, v in rows)
    sb = sum(t*v for _, t, v in rows)
    det = cc*ss - cs*cs
    expected = math.degrees(math.atan2((cc*sb-cs*cb)/det, (ss*cb-cs*sb)/det))
    assert calculate_axis_from_leads(leads)["axis_degrees"] == pytest.approx(expected, abs=0.05)


def test_csv_guards(tmp_path):
    from ecg_axis import process_csv
    source = tmp_path / "source.csv"
    source.write_text("lead_i_net,lead_avf_net\n1,-0.1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        process_csv(source, source)
    with pytest.raises(ValueError):
        process_csv("a/../source.csv", tmp_path / "out.csv")


def test_csv_batch_correctness(tmp_path):
    import csv
    from ecg_axis import process_csv
    source, output = tmp_path / "in.csv", tmp_path / "out.csv"
    source.write_text("lead_i_net,lead_avf_net\n1,-0.1\n0,0\n", encoding="utf-8")
    res = process_csv(source, output)
    assert res[0]["classification"] == "normal"
    assert res[1]["classification"] == "indeterminate"
    with output.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[1]["axis_degrees"] == "None"
