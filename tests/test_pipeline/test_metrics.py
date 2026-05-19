"""Tests for metrics calculation module."""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from run_intelligence.pipeline.metrics import (
    MetricCalculationError,
    StandardMetrics,
    calculate_standard_metrics,
    calculate_max_hr,
    calculate_hr_zone_distribution,
    calculate_elevation_gain_loss,
)
from run_intelligence.pipeline.fit_parser import RawRunData


class TestStandardMetricsModel:
    """Test StandardMetrics Pydantic model."""

    def test_valid_creation_all_fields(self):
        metrics = StandardMetrics(
            pace_avg_min_per_km=5.5,
            pace_max_min_per_km=5.0,
            pace_min_min_per_km=6.0,
            hr_zone_distribution={"z1": 600, "z2": 1200, "z3": 900, "z4": 600, "z5": 300},
            cadence_avg_rpm=170.0,
            cadence_max_rpm=185.0,
            elevation_gain_m=150.5,
            elevation_loss_m=120.3,
        )
        assert metrics.pace_avg_min_per_km == 5.5
        assert metrics.hr_zone_distribution["z2"] == 1200

    def test_valid_creation_minimal_fields(self):
        metrics = StandardMetrics()
        assert metrics.pace_avg_min_per_km is None
        assert metrics.hr_zone_distribution is None

    def test_pace_out_of_range_raises(self):
        with pytest.raises(ValueError, match="Pace must be between 0 and 60"):
            StandardMetrics(pace_avg_min_per_km=65.0)

    def test_pace_nan_raises(self):
        with pytest.raises(ValueError, match="finite"):
            StandardMetrics(pace_avg_min_per_km=float("nan"))

    def test_negative_cadence_raises(self):
        with pytest.raises(ValueError, match="Cadence must be between 0 and 300"):
            StandardMetrics(cadence_avg_rpm=-10.0)

    def test_cadence_over_300_raises(self):
        with pytest.raises(ValueError, match="Cadence must be between 0 and 300"):
            StandardMetrics(cadence_avg_rpm=350.0)

    def test_cadence_nan_raises(self):
        with pytest.raises(ValueError, match="finite"):
            StandardMetrics(cadence_avg_rpm=float("nan"))

    def test_negative_elevation_raises(self):
        with pytest.raises(ValueError, match="Elevation must be non-negative"):
            StandardMetrics(elevation_gain_m=-50.0)

    def test_elevation_nan_raises(self):
        with pytest.raises(ValueError, match="finite"):
            StandardMetrics(elevation_gain_m=float("nan"))

    def test_hr_zone_invalid_key_raises(self):
        with pytest.raises(ValueError, match="Invalid HR zone key"):
            StandardMetrics(hr_zone_distribution={"z6": 100})

    def test_hr_zone_negative_seconds_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            StandardMetrics(hr_zone_distribution={"z1": -100})

    def test_max_pace_slower_than_avg_raises(self):
        with pytest.raises(ValueError, match="pace_max_min_per_km cannot be slower"):
            StandardMetrics(
                pace_avg_min_per_km=5.0,
                pace_max_min_per_km=6.0,
            )

    def test_min_pace_faster_than_avg_raises(self):
        with pytest.raises(ValueError, match="pace_min_min_per_km cannot be faster"):
            StandardMetrics(
                pace_avg_min_per_km=5.0,
                pace_min_min_per_km=4.0,
            )


class TestStandardMetricsSerialization:
    """Test JSON serialization and deserialization."""

    def test_to_json(self):
        metrics = StandardMetrics(
            pace_avg_min_per_km=5.5,
            cadence_avg_rpm=170.0,
            elevation_gain_m=150.5,
        )
        json_str = metrics.to_json()
        parsed = json.loads(json_str)
        assert parsed["pace_avg_min_per_km"] == 5.5
        assert parsed["cadence_avg_rpm"] == 170.0
        assert parsed["elevation_gain_m"] == 150.5

    def test_json_roundtrip(self):
        original = StandardMetrics(
            pace_avg_min_per_km=5.5,
            hr_zone_distribution={"z1": 600, "z2": 1200},
            cadence_avg_rpm=170.0,
        )
        json_str = original.to_json()
        restored = StandardMetrics.from_json(json_str)
        assert restored.pace_avg_min_per_km == original.pace_avg_min_per_km
        assert restored.hr_zone_distribution["z2"] == original.hr_zone_distribution["z2"]

    def test_from_json_invalid_raises(self):
        with pytest.raises(ValidationError):
            StandardMetrics.from_json("invalid json")


class TestCalculateMaxHr:
    """Test max HR calculation."""

    def test_default_age_30(self):
        max_hr = calculate_max_hr()
        assert max_hr == 190

    def test_age_25(self):
        max_hr = calculate_max_hr(age=25)
        assert max_hr == 195

    def test_age_40(self):
        max_hr = calculate_max_hr(age=40)
        assert max_hr == 180

    def test_age_60(self):
        max_hr = calculate_max_hr(age=60)
        assert max_hr == 160

    def test_negative_age_raises(self):
        with pytest.raises(MetricCalculationError):
            calculate_max_hr(age=-1)

    def test_age_over_120_raises(self):
        with pytest.raises(MetricCalculationError):
            calculate_max_hr(age=150)

    def test_float_age_returns_int(self):
        max_hr = calculate_max_hr(age=30.5)
        assert isinstance(max_hr, int)


class TestCalculateHrZoneDistribution:
    """Test HR zone distribution calculation."""

    def test_zones_with_normal_hr(self):
        zones = calculate_hr_zone_distribution(
            hr_avg=145.0,
            hr_max=175.0,
            duration_seconds=3600.0,
            age=30,
        )
        assert zones["z1"] + zones["z2"] + zones["z3"] + zones["z4"] + zones["z5"] == 3600
        assert all(v >= 0 for v in zones.values())

    def test_zones_with_elevated_max_hr(self):
        zones = calculate_hr_zone_distribution(
            hr_avg=155.0,
            hr_max=200.0,
            duration_seconds=3600.0,
            age=25,
        )
        assert sum(zones.values()) == 3600

    def test_zones_with_missing_hr_data(self):
        zones = calculate_hr_zone_distribution(
            hr_avg=None,
            hr_max=175.0,
            duration_seconds=3600.0,
        )
        assert all(v == 0 for v in zones.values())

    def test_zones_zero_duration(self):
        zones = calculate_hr_zone_distribution(
            hr_avg=145.0,
            hr_max=175.0,
            duration_seconds=0.0,
        )
        assert sum(zones.values()) == 0

    def test_zones_with_nan_hr_avg(self):
        zones = calculate_hr_zone_distribution(
            hr_avg=float("nan"),
            hr_max=175.0,
            duration_seconds=3600.0,
        )
        assert all(v == 0 for v in zones.values())

    def test_zones_negative_duration_raises(self):
        with pytest.raises(MetricCalculationError):
            calculate_hr_zone_distribution(
                hr_avg=145.0,
                hr_max=175.0,
                duration_seconds=-100.0,
            )

    def test_zones_fractional_seconds_rounded(self):
        zones = calculate_hr_zone_distribution(
            hr_avg=145.0,
            hr_max=175.0,
            duration_seconds=3600.9,
            age=30,
        )
        assert sum(zones.values()) == 3601


class TestCalculateElevationGainLoss:
    """Test elevation gain/loss calculation."""

    def test_ascending_terrain(self):
        gps_elevation = [100.0, 102.0, 105.0, 108.0, 110.0]
        gain, loss = calculate_elevation_gain_loss(gps_elevation)
        assert gain is not None
        assert loss is not None
        assert gain > 0
        assert loss == 0

    def test_descending_terrain(self):
        gps_elevation = [110.0, 108.0, 105.0, 102.0, 100.0]
        gain, loss = calculate_elevation_gain_loss(gps_elevation)
        assert gain is not None
        assert loss is not None
        assert gain == 0
        assert loss > 0

    def test_mixed_terrain(self):
        gps_elevation = [100.0, 105.0, 98.0, 108.0, 101.0, 110.0]
        gain, loss = calculate_elevation_gain_loss(gps_elevation)
        assert gain is not None
        assert loss is not None
        assert gain > 0
        assert loss > 0

    def test_flat_terrain(self):
        gps_elevation = [100.0, 100.5, 100.3, 100.7, 100.2]
        gain, loss = calculate_elevation_gain_loss(gps_elevation)
        assert gain == 0
        assert loss == 0

    def test_noise_filter_2m(self):
        gps_elevation = [100.0, 102.0, 104.0, 106.0]
        gain, loss = calculate_elevation_gain_loss(gps_elevation)
        assert gain == 6.0

    def test_noise_filter_ignores_below_2m(self):
        gps_elevation = [100.0, 101.0, 102.0, 101.5, 103.0]
        gain, loss = calculate_elevation_gain_loss(gps_elevation)
        assert gain == 0.0
        assert loss == 0.0

    def test_none_elevation_returns_none(self):
        gain, loss = calculate_elevation_gain_loss(None)
        assert gain is None
        assert loss is None

    def test_empty_elevation_returns_none(self):
        gain, loss = calculate_elevation_gain_loss([])
        assert gain is None
        assert loss is None

    def test_single_point_returns_none(self):
        gain, loss = calculate_elevation_gain_loss([100.0])
        assert gain is None
        assert loss is None

    def test_elevation_with_none_values(self):
        gps_elevation = [100.0, None, 105.0, 102.0, None, 108.0]
        gain, loss = calculate_elevation_gain_loss(gps_elevation)
        assert gain is not None
        assert loss is not None

    def test_negative_elevation_allowed(self):
        gps_elevation = [-100.0, -98.0, -95.0]
        gain, loss = calculate_elevation_gain_loss(gps_elevation)
        assert gain == 5.0
        assert loss == 0.0

    def test_elevation_with_nan_values(self):
        gps_elevation = [100.0, float("nan"), 105.0, 102.0]
        gain, loss = calculate_elevation_gain_loss(gps_elevation)
        assert gain is not None
        assert loss is not None


class TestCalculateStandardMetrics:
    """Test main calculate_standard_metrics function."""

    def _create_raw_data(self, **kwargs):
        defaults = {
            "timestamp": datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            "duration_seconds": 3600.0,
            "distance_meters": 10000.0,
        }
        defaults.update(kwargs)
        return RawRunData(**defaults)

    def test_complete_data(self):
        raw = self._create_raw_data(
            pace_sec_per_km=360.0,
            hr_avg_bpm=145.0,
            hr_max_bpm=175.0,
            cadence_avg_rpm=170.0,
            cadence_max_rpm=185.0,
            gps_elevation=[100.0, 102.0, 105.0],
        )
        result = calculate_standard_metrics(raw)
        assert result.pace_avg_min_per_km == 6.0
        assert result.cadence_avg_rpm == 170.0
        assert result.elevation_gain_m is not None

    def test_minimal_data(self):
        raw = self._create_raw_data()
        result = calculate_standard_metrics(raw)
        assert result.pace_avg_min_per_km is None
        assert result.cadence_avg_rpm is None
        assert result.elevation_gain_m is None

    def test_no_hr_data(self):
        raw = self._create_raw_data(
            pace_sec_per_km=360.0,
            cadence_avg_rpm=170.0,
        )
        result = calculate_standard_metrics(raw)
        assert result.pace_avg_min_per_km == 6.0
        assert result.hr_zone_distribution is None

    def test_no_gps_elevation(self):
        raw = self._create_raw_data(
            pace_sec_per_km=360.0,
            hr_avg_bpm=145.0,
            hr_max_bpm=175.0,
        )
        result = calculate_standard_metrics(raw)
        assert result.elevation_gain_m is None
        assert result.elevation_loss_m is None

    def test_no_cadence_data(self):
        raw = self._create_raw_data(
            pace_sec_per_km=360.0,
            hr_avg_bpm=145.0,
            hr_max_bpm=175.0,
            gps_elevation=[100.0, 105.0],
        )
        result = calculate_standard_metrics(raw)
        assert result.cadence_avg_rpm is None
        assert result.cadence_max_rpm is None

    def test_zero_pace_returns_none(self):
        raw = self._create_raw_data(pace_sec_per_km=0.0)
        result = calculate_standard_metrics(raw)
        assert result.pace_avg_min_per_km is None

    def test_negative_pace_returns_none(self):
        raw = self._create_raw_data(pace_sec_per_km=-60.0)
        result = calculate_standard_metrics(raw)
        assert result.pace_avg_min_per_km is None

    def test_none_raw_data_raises(self):
        with pytest.raises(MetricCalculationError, match="cannot be None"):
            calculate_standard_metrics(None)


class TestDeterministicBehavior:
    """Test that metrics calculation is deterministic."""

    def _create_raw_data(self, **kwargs):
        defaults = {
            "timestamp": datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            "duration_seconds": 3600.0,
            "distance_meters": 10000.0,
            "pace_sec_per_km": 360.0,
            "hr_avg_bpm": 145.0,
            "hr_max_bpm": 175.0,
            "cadence_avg_rpm": 170.0,
            "cadence_max_rpm": 185.0,
            "gps_elevation": [100.0, 102.0, 105.0, 108.0, 110.0],
        }
        defaults.update(kwargs)
        return RawRunData(**defaults)

    def test_same_input_same_output(self):
        raw = self._create_raw_data()
        result1 = calculate_standard_metrics(raw)
        result2 = calculate_standard_metrics(raw)
        assert result1.pace_avg_min_per_km == result2.pace_avg_min_per_km
        assert result1.elevation_gain_m == result2.elevation_gain_m
        assert result1.hr_zone_distribution == result2.hr_zone_distribution

    def test_different_pace_same_session_values(self):
        raw1 = self._create_raw_data(pace_sec_per_km=300.0)
        raw2 = self._create_raw_data(pace_sec_per_km=420.0)
        result1 = calculate_standard_metrics(raw1)
        result2 = calculate_standard_metrics(raw2)
        assert result1.pace_avg_min_per_km != result2.pace_avg_min_per_km
        assert result1.cadence_avg_rpm == result2.cadence_avg_rpm


class TestMetricCalculationError:
    """Test MetricCalculationError exception."""

    def test_raises_with_message(self):
        with pytest.raises(MetricCalculationError) as exc_info:
            raise MetricCalculationError("Test error message")
        assert str(exc_info.value) == "Test error message"

    def test_from_validation_error_has_cause(self):
        try:
            try:
                raise ValueError("inner error")
            except ValueError as e:
                raise MetricCalculationError("outer error") from e
        except MetricCalculationError as exc:
            assert exc.__cause__ is not None


class TestHRZoneConstants:
    """Test HR zone constants from config."""

    def test_zones_defined(self):
        from run_intelligence.config import HR_ZONES
        assert "z1" in HR_ZONES
        assert "z2" in HR_ZONES
        assert "z3" in HR_ZONES
        assert "z4" in HR_ZONES
        assert "z5" in HR_ZONES

    def test_z1_is_recovery(self):
        from run_intelligence.config import HR_ZONES
        assert HR_ZONES["z1"] == (50, 60)

    def test_z5_is_vo2max(self):
        from run_intelligence.config import HR_ZONES
        assert HR_ZONES["z5"] == (90, 100)


class TestElevationNoiseFilter:
    """Test elevation noise filter constant."""

    def test_elevation_filter_defined(self):
        from run_intelligence.config import ELEVATION_NOISE_FILTER_METERS
        assert ELEVATION_NOISE_FILTER_METERS == 2.0


class TestDefaultAge:
    """Test default age constant."""

    def test_default_age_defined(self):
        from run_intelligence.config import DEFAULT_AGE
        assert DEFAULT_AGE == 30


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_fast_pace_rounds(self):
        raw = RawRunData(
            timestamp=datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            duration_seconds=3600.0,
            distance_meters=100000.0,
            pace_sec_per_km=36.0,
        )
        result = calculate_standard_metrics(raw)
        assert result.pace_avg_min_per_km == 0.6

    def test_pace_rounds_to_zero_raises(self):
        raw = RawRunData(
            timestamp=datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            duration_seconds=1.0,
            distance_meters=100000.0,
            pace_sec_per_km=0.2,
        )
        with pytest.raises(MetricCalculationError):
            calculate_standard_metrics(raw)

    def test_hr_avg_exactly_at_zone_boundary(self):
        zones = calculate_hr_zone_distribution(
            hr_avg=114.0,
            hr_max=175.0,
            duration_seconds=3600.0,
            age=30,
        )
        assert zones["z2"] == 3600

    def test_sustained_gradual_slope_sub_threshold(self):
        gps_elevation = [100.0, 101.5, 103.0, 104.5, 106.0]
        gain, loss = calculate_elevation_gain_loss(gps_elevation)
        assert gain == 0.0

    def test_negative_age_in_calculate_standard_metrics(self):
        with pytest.raises(MetricCalculationError):
            calculate_max_hr(age=-5)

    def test_nan_hr_avg_in_standard_metrics(self):
        raw = RawRunData(
            timestamp=datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            duration_seconds=3600.0,
            distance_meters=10000.0,
            hr_avg_bpm=float("nan"),
            hr_max_bpm=175.0,
        )
        result = calculate_standard_metrics(raw)
        assert result.hr_zone_distribution is None

    def test_none_input_raises(self):
        with pytest.raises(MetricCalculationError, match="cannot be None"):
            calculate_standard_metrics(None)
