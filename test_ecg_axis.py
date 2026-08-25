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
        assert result["lead2"] == "AVF"

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
