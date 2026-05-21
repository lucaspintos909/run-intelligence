"""Tests for data validation and quality flagging module."""

import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from run_intelligence.config import (
    CONFIDENCE_DEDUCTION_CADENCE_INCONSISTENCY,
    CONFIDENCE_DEDUCTION_GPS_DRIFT,
    CONFIDENCE_DEDUCTION_SPIKE,
    CONFIDENCE_DEDUCTION_THRESHOLD_EXCEEDED,
)
from run_intelligence.pipeline.fit_parser import RawRunData
from run_intelligence.pipeline.metrics import (
    AsthmaAwareMetrics,
    MetricCalculationError,
    StandardMetrics,
)
from run_intelligence.pipeline.validation import (
    DataQualityFlags,
    RunData,
    calculate_confidence_score,
    detect_cadence_inconsistencies,
    detect_gps_drift,
    detect_hr_artifacts,
    validate_and_flag,
)


class TestDataQualityFlagsModel:
    """Test DataQualityFlags Pydantic model."""

    def test_valid_creation_minimal(self):
        flags = DataQualityFlags()
        assert flags.confidence_score == 1.0
        assert flags.low_confidence_flag is False
        assert flags.hr_artifacts == []
        assert flags.gps_drift_segments == []
        assert flags.cadence_inconsistencies == []

    def test_valid_creation_with_artifacts(self):
        flags = DataQualityFlags(
            hr_artifacts=[
                {
                    "index": 0,
                    "value_bpm": 225.0,
                    "type": "threshold_exceeded",
                    "timestamp": None,
                }
            ],
            confidence_score=0.85,
            low_confidence_flag=False,
        )
        assert len(flags.hr_artifacts) == 1
        assert flags.hr_artifacts[0]["value_bpm"] == 225.0

    def test_confidence_score_out_of_range_raises(self):
        with pytest.raises(
            ValueError, match="confidence_score must be between 0 and 1"
        ):
            DataQualityFlags(confidence_score=1.5)

    def test_confidence_score_negative_raises(self):
        with pytest.raises(
            ValueError, match="confidence_score must be between 0 and 1"
        ):
            DataQualityFlags(confidence_score=-0.1)

    def test_confidence_score_nan_raises(self):
        with pytest.raises(ValueError, match="finite"):
            DataQualityFlags(confidence_score=float("nan"))

    def test_low_confidence_mismatch_raises(self):
        with pytest.raises(ValueError, match="low_confidence_flag must be True"):
            DataQualityFlags(confidence_score=0.3, low_confidence_flag=False)

    def test_high_confidence_with_low_flag_raises(self):
        with pytest.raises(ValueError, match="low_confidence_flag must be False"):
            DataQualityFlags(confidence_score=0.8, low_confidence_flag=True)

    def test_hr_artifact_missing_index_raises(self):
        with pytest.raises(ValueError, match="hr_artifact must contain 'index' as int"):
            DataQualityFlags(
                hr_artifacts=[{"value_bpm": 225.0, "type": "threshold_exceeded"}]
            )

    def test_hr_artifact_invalid_type_raises(self):
        with pytest.raises(ValueError, match="hr_artifact must contain 'type'"):
            DataQualityFlags(
                hr_artifacts=[{"index": 0, "value_bpm": 225.0, "type": "invalid"}]
            )

    def test_gps_drift_missing_start_index_raises(self):
        with pytest.raises(
            ValueError, match="gps_drift_segment must contain 'start_index' as int"
        ):
            DataQualityFlags(
                gps_drift_segments=[
                    {
                        "end_index": 1,
                        "distance_meters": 100.0,
                        "duration_seconds": 1.0,
                        "expected_pace": 3.0,
                    }
                ]
            )

    def test_cadence_inconsistency_missing_is_pace_explained_raises(self):
        with pytest.raises(
            ValueError,
            match="cadence_inconsistency must contain 'is_pace_explained' as bool",
        ):
            DataQualityFlags(
                cadence_inconsistencies=[
                    {
                        "start_index": 0,
                        "end_index": 0,
                        "change_pct": 25.0,
                        "pace_change_pct": 0.0,
                    }
                ]
            )


class TestDataQualityFlagsSerialization:
    """Test JSON serialization for DataQualityFlags."""

    def test_to_json(self):
        flags = DataQualityFlags(
            hr_artifacts=[
                {
                    "index": 0,
                    "value_bpm": 225.0,
                    "type": "threshold_exceeded",
                    "timestamp": None,
                }
            ],
            confidence_score=0.85,
            low_confidence_flag=False,
        )
        json_str = flags.to_json()
        parsed = json.loads(json_str)
        assert parsed["hr_artifacts"][0]["value_bpm"] == 225.0
        assert parsed["confidence_score"] == 0.85
        assert parsed["low_confidence_flag"] is False

    def test_json_roundtrip(self):
        original = DataQualityFlags(
            gps_drift_segments=[
                {
                    "start_index": 0,
                    "end_index": 1,
                    "distance_meters": 100.0,
                    "duration_seconds": 1.0,
                    "expected_pace": 3.0,
                }
            ],
            confidence_score=0.9,
            low_confidence_flag=False,
        )
        json_str = original.to_json()
        restored = DataQualityFlags.from_json(json_str)
        assert restored.gps_drift_segments[0]["distance_meters"] == 100.0
        assert restored.confidence_score == original.confidence_score


class TestRunDataModel:
    """Test RunData Pydantic model."""

    def _create_raw_data(self, **kwargs):
        defaults = {
            "timestamp": datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            "duration_seconds": 3600.0,
            "distance_meters": 10000.0,
        }
        defaults.update(kwargs)
        return RawRunData(**defaults)

    def test_valid_creation(self):
        raw = self._create_raw_data()
        flags = DataQualityFlags(confidence_score=0.85, low_confidence_flag=False)
        run_data = RunData(raw_data=raw, data_quality_flags=flags)
        # RunData has its own confidence_score field (default 1.0), independent of flags
        assert run_data.confidence_score == 1.0
        assert run_data.low_confidence_flag is False
        assert run_data.data_quality_flags.confidence_score == 0.85

    def test_with_standard_and_asthma_metrics(self):
        raw = self._create_raw_data()
        standard = StandardMetrics(pace_avg_min_per_km=5.5)
        asthma = AsthmaAwareMetrics(confidence_score=0.8)
        flags = DataQualityFlags(confidence_score=0.75, low_confidence_flag=False)
        run_data = RunData(
            raw_data=raw,
            standard_metrics=standard,
            asthma_aware_metrics=asthma,
            data_quality_flags=flags,
            confidence_score=0.75,
            low_confidence_flag=False,
        )
        assert run_data.standard_metrics.pace_avg_min_per_km == 5.5
        assert run_data.asthma_aware_metrics.confidence_score == 0.8

    def test_confidence_score_out_of_range_raises(self):
        raw = self._create_raw_data()
        flags = DataQualityFlags(confidence_score=0.5, low_confidence_flag=False)
        with pytest.raises(
            ValueError, match="confidence_score must be between 0 and 1"
        ):
            RunData(raw_data=raw, data_quality_flags=flags, confidence_score=1.5)

    def test_low_confidence_mismatch_raises(self):
        raw = self._create_raw_data()
        flags = DataQualityFlags(confidence_score=0.3, low_confidence_flag=True)
        with pytest.raises(ValueError, match="low_confidence_flag must be True"):
            RunData(
                raw_data=raw,
                data_quality_flags=flags,
                confidence_score=0.3,
                low_confidence_flag=False,
            )

    def test_to_json(self):
        raw = self._create_raw_data(pace_sec_per_km=360.0)
        flags = DataQualityFlags(confidence_score=0.9, low_confidence_flag=False)
        run_data = RunData(raw_data=raw, data_quality_flags=flags)
        json_str = run_data.to_json()
        parsed = json.loads(json_str)
        assert parsed["raw_data"]["distance_meters"] == 10000.0
        assert parsed["data_quality_flags"]["confidence_score"] == 0.9

    def test_json_roundtrip(self):
        raw = self._create_raw_data(
            pace_sec_per_km=360.0, hr_avg_bpm=145.0, hr_max_bpm=175.0
        )
        standard = StandardMetrics(pace_avg_min_per_km=6.0)
        flags = DataQualityFlags(confidence_score=0.9, low_confidence_flag=False)
        original = RunData(
            raw_data=raw,
            standard_metrics=standard,
            data_quality_flags=flags,
            confidence_score=0.9,
            low_confidence_flag=False,
        )
        json_str = original.to_json()
        restored = RunData.from_json(json_str)
        assert restored.raw_data.distance_meters == original.raw_data.distance_meters
        assert restored.standard_metrics.pace_avg_min_per_km == 6.0
        assert restored.confidence_score == 0.9

    def test_from_json_invalid_raises(self):
        with pytest.raises(ValidationError):
            RunData.from_json("invalid json")


class TestDetectHrArtifacts:
    """Test HR artifact detection."""

    def _create_raw_data(self, **kwargs):
        defaults = {
            "timestamp": datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            "duration_seconds": 3600.0,
            "distance_meters": 10000.0,
        }
        defaults.update(kwargs)
        return RawRunData(**defaults)

    def test_no_hr_data(self):
        raw = self._create_raw_data()
        artifacts = detect_hr_artifacts(raw)
        assert artifacts == []

    def test_threshold_exceeded(self):
        raw = self._create_raw_data(hr_avg_bpm=145.0, hr_max_bpm=225.0)
        artifacts = detect_hr_artifacts(raw)
        assert len(artifacts) == 1
        assert artifacts[0]["type"] == "threshold_exceeded"
        assert artifacts[0]["value_bpm"] == 225.0

    def test_spike_detection(self):
        raw = self._create_raw_data(hr_avg_bpm=140.0, hr_max_bpm=180.0)
        artifacts = detect_hr_artifacts(raw)
        assert len(artifacts) == 1
        assert artifacts[0]["type"] == "spike"

    def test_both_threshold_and_spike(self):
        raw = self._create_raw_data(hr_avg_bpm=140.0, hr_max_bpm=225.0)
        artifacts = detect_hr_artifacts(raw)
        assert len(artifacts) == 1
        assert artifacts[0]["type"] == "threshold_exceeded"

    def test_normal_hr(self):
        raw = self._create_raw_data(hr_avg_bpm=145.0, hr_max_bpm=165.0)
        artifacts = detect_hr_artifacts(raw)
        assert artifacts == []

    def test_none_raw_data_raises(self):
        with pytest.raises(MetricCalculationError, match="cannot be None"):
            detect_hr_artifacts(None)

    def test_hr_max_at_threshold(self):
        raw = self._create_raw_data(hr_avg_bpm=145.0, hr_max_bpm=220.0)
        artifacts = detect_hr_artifacts(raw)
        assert artifacts == []

    def test_nan_hr_values(self):
        raw = self._create_raw_data(hr_avg_bpm=float("nan"), hr_max_bpm=225.0)
        artifacts = detect_hr_artifacts(raw)
        assert len(artifacts) == 1
        assert artifacts[0]["type"] == "threshold_exceeded"


class TestDetectGpsDrift:
    """Test GPS drift detection."""

    def _create_raw_data(self, **kwargs):
        defaults = {
            "timestamp": datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            "duration_seconds": 3600.0,
            "distance_meters": 10000.0,
        }
        defaults.update(kwargs)
        return RawRunData(**defaults)

    def test_no_gps_data(self):
        raw = self._create_raw_data()
        segments = detect_gps_drift(raw)
        assert segments == []

    def test_single_gps_point(self):
        raw = self._create_raw_data(gps_lat=[40.0], gps_lon=[-74.0])
        segments = detect_gps_drift(raw)
        assert segments == []

    def test_normal_gps_no_drift(self):
        raw = self._create_raw_data(
            gps_lat=[40.0, 40.0001, 40.0002],
            gps_lon=[-74.0, -74.0001, -74.0002],
            duration_seconds=3600.0,
            pace_sec_per_km=360.0,
        )
        segments = detect_gps_drift(raw)
        assert segments == []

    def test_gps_drift_detected(self):
        raw = self._create_raw_data(
            gps_lat=[40.0, 40.01, 40.02],
            gps_lon=[-74.0, -74.0, -74.0],
            duration_seconds=2.0,
            pace_sec_per_km=360.0,
        )
        segments = detect_gps_drift(raw)
        assert len(segments) >= 1
        assert segments[0]["start_index"] >= 0
        assert segments[0]["end_index"] > segments[0]["start_index"]
        assert "distance_meters" in segments[0]
        assert "duration_seconds" in segments[0]

    def test_pace_consistent_not_drift(self):
        raw = self._create_raw_data(
            gps_lat=[40.0, 40.0036, 40.0072],
            gps_lon=[-74.0, -74.0, -74.0],
            duration_seconds=72.0,
            pace_sec_per_km=36.0,
        )
        segments = detect_gps_drift(raw)
        assert segments == []

    def test_none_raw_data_raises(self):
        with pytest.raises(MetricCalculationError, match="cannot be None"):
            detect_gps_drift(None)

    def test_gps_with_none_values(self):
        raw = self._create_raw_data(
            gps_lat=[40.0, 40.0001],
            gps_lon=[-74.0, -74.0001],
            duration_seconds=3600.0,
        )
        segments = detect_gps_drift(raw)
        assert isinstance(segments, list)

    def test_nan_gps_values(self):
        raw = self._create_raw_data(
            gps_lat=[40.0, float("nan"), 40.0001],
            gps_lon=[-74.0, -74.0, -74.0001],
            duration_seconds=3600.0,
        )
        segments = detect_gps_drift(raw)
        assert isinstance(segments, list)


class TestDetectCadenceInconsistencies:
    """Test cadence inconsistency detection."""

    def _create_raw_data(self, **kwargs):
        defaults = {
            "timestamp": datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            "duration_seconds": 3600.0,
            "distance_meters": 10000.0,
        }
        defaults.update(kwargs)
        return RawRunData(**defaults)

    def test_no_cadence_data(self):
        raw = self._create_raw_data()
        inconsistencies = detect_cadence_inconsistencies(raw)
        assert inconsistencies == []

    def test_normal_cadence(self):
        raw = self._create_raw_data(cadence_avg_rpm=170.0, cadence_max_rpm=175.0)
        inconsistencies = detect_cadence_inconsistencies(raw)
        assert inconsistencies == []

    def test_high_cadence_change(self):
        raw = self._create_raw_data(cadence_avg_rpm=150.0, cadence_max_rpm=200.0)
        inconsistencies = detect_cadence_inconsistencies(raw)
        assert len(inconsistencies) == 1
        assert inconsistencies[0]["change_pct"] == pytest.approx(33.33, abs=0.1)

    def test_pace_explained(self):
        raw = self._create_raw_data(
            cadence_avg_rpm=150.0,
            cadence_max_rpm=200.0,
            pace_sec_per_km=180.0,
        )
        inconsistencies = detect_cadence_inconsistencies(raw)
        assert len(inconsistencies) == 1
        assert "is_pace_explained" in inconsistencies[0]

    def test_none_raw_data_raises(self):
        with pytest.raises(MetricCalculationError, match="cannot be None"):
            detect_cadence_inconsistencies(None)

    def test_nan_cadence(self):
        raw = self._create_raw_data(cadence_avg_rpm=float("nan"), cadence_max_rpm=200.0)
        inconsistencies = detect_cadence_inconsistencies(raw)
        assert inconsistencies == []

    def test_zero_cadence_avg(self):
        raw = self._create_raw_data(cadence_avg_rpm=0.0, cadence_max_rpm=200.0)
        inconsistencies = detect_cadence_inconsistencies(raw)
        assert inconsistencies == []


class TestCalculateConfidenceScore:
    """Test confidence score calculation."""

    def test_perfect_data(self):
        score, flag = calculate_confidence_score(
            asthma_aware_confidence=1.0,
            hr_artifacts=[],
            gps_drift_segments=[],
            cadence_inconsistencies=[],
        )
        assert score == 1.0
        assert flag is False

    def test_with_hr_artifacts(self):
        score, flag = calculate_confidence_score(
            asthma_aware_confidence=1.0,
            hr_artifacts=[{"type": "threshold_exceeded"}],
            gps_drift_segments=[],
            cadence_inconsistencies=[],
        )
        assert score == 1.0 - CONFIDENCE_DEDUCTION_THRESHOLD_EXCEEDED
        assert flag is False

    def test_with_gps_drift(self):
        score, flag = calculate_confidence_score(
            asthma_aware_confidence=1.0,
            hr_artifacts=[],
            gps_drift_segments=[{"start_index": 0, "end_index": 1}],
            cadence_inconsistencies=[],
        )
        assert score == 1.0 - CONFIDENCE_DEDUCTION_GPS_DRIFT
        assert flag is False

    def test_with_cadence_inconsistency(self):
        score, flag = calculate_confidence_score(
            asthma_aware_confidence=1.0,
            hr_artifacts=[],
            gps_drift_segments=[],
            cadence_inconsistencies=[{"is_pace_explained": False}],
        )
        assert score == 1.0 - CONFIDENCE_DEDUCTION_CADENCE_INCONSISTENCY
        assert flag is False

    def test_pace_explained_no_deduction(self):
        score, flag = calculate_confidence_score(
            asthma_aware_confidence=1.0,
            hr_artifacts=[],
            gps_drift_segments=[],
            cadence_inconsistencies=[{"is_pace_explained": True}],
        )
        assert score == 1.0
        assert flag is False

    def test_multiple_issues(self):
        score, flag = calculate_confidence_score(
            asthma_aware_confidence=0.8,
            hr_artifacts=[{"type": "threshold_exceeded"}, {"type": "spike"}],
            gps_drift_segments=[{"start_index": 0, "end_index": 1}],
            cadence_inconsistencies=[{"is_pace_explained": False}],
        )
        expected = (
            0.8
            - CONFIDENCE_DEDUCTION_THRESHOLD_EXCEEDED
            - CONFIDENCE_DEDUCTION_SPIKE
            - CONFIDENCE_DEDUCTION_GPS_DRIFT
            - CONFIDENCE_DEDUCTION_CADENCE_INCONSISTENCY
        )
        assert score == pytest.approx(expected)
        assert flag is True

    def test_no_asthma_confidence(self):
        score, flag = calculate_confidence_score(
            asthma_aware_confidence=None,
            hr_artifacts=[],
            gps_drift_segments=[],
            cadence_inconsistencies=[],
        )
        assert score == 1.0
        assert flag is False

    def test_nan_asthma_confidence(self):
        score, flag = calculate_confidence_score(
            asthma_aware_confidence=float("nan"),
            hr_artifacts=[],
            gps_drift_segments=[],
            cadence_inconsistencies=[],
        )
        assert score == 1.0
        assert flag is False

    def test_low_confidence_threshold(self):
        # Exactly at 0.5 should NOT trigger low confidence
        score, flag = calculate_confidence_score(
            asthma_aware_confidence=0.5,
            hr_artifacts=[],
            gps_drift_segments=[],
            cadence_inconsistencies=[],
        )
        assert score == 0.5
        assert flag is False

    def test_just_below_threshold(self):
        score, flag = calculate_confidence_score(
            asthma_aware_confidence=0.49,
            hr_artifacts=[],
            gps_drift_segments=[],
            cadence_inconsistencies=[],
        )
        assert score == 0.49
        assert flag is True

    def test_confidence_floor_at_zero(self):
        score, flag = calculate_confidence_score(
            asthma_aware_confidence=0.1,
            hr_artifacts=[{"type": "threshold_exceeded"}] * 10,
            gps_drift_segments=[{"start_index": 0, "end_index": 1}] * 10,
            cadence_inconsistencies=[],
        )
        assert score == 0.0
        assert flag is True


class TestValidateAndFlag:
    """Test the main validate_and_flag orchestrator."""

    def test_none_file_path_raises(self):
        with pytest.raises(Exception):
            validate_and_flag(None)

    def test_missing_file_raises(self):
        with pytest.raises(Exception):
            validate_and_flag("/nonexistent/path.fit")

    def test_orchestrates_full_pipeline(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        mock_raw = RawRunData(
            timestamp=datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            duration_seconds=3600.0,
            distance_meters=10000.0,
            hr_avg_bpm=145.0,
            hr_max_bpm=175.0,
        )
        mock_standard = StandardMetrics(pace_avg_min_per_km=6.0)
        mock_asthma = AsthmaAwareMetrics(confidence_score=0.9)

        with (
            patch(
                "run_intelligence.pipeline.fit_parser.parse_fit_file",
                return_value=mock_raw,
            ) as mock_parse,
            patch(
                "run_intelligence.pipeline.validation.calculate_standard_metrics",
                return_value=mock_standard,
            ) as mock_std,
            patch(
                "run_intelligence.pipeline.validation.calculate_asthma_aware_metrics",
                return_value=mock_asthma,
            ) as mock_asm,
        ):
            result = validate_and_flag(str(fit_file), verbose=False)

        mock_parse.assert_called_once_with(str(fit_file))
        mock_std.assert_called_once_with(mock_raw)
        mock_asm.assert_called_once_with(mock_raw, standard_metrics=mock_standard)

        assert isinstance(result, RunData)
        assert result.raw_data == mock_raw
        assert result.standard_metrics == mock_standard
        assert result.asthma_aware_metrics == mock_asthma
        assert isinstance(result.data_quality_flags, DataQualityFlags)
        assert 0 <= result.confidence_score <= 1.0
        assert isinstance(result.low_confidence_flag, bool)

    def test_deterministic_with_mocks(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        mock_raw = RawRunData(
            timestamp=datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            duration_seconds=3600.0,
            distance_meters=10000.0,
            hr_avg_bpm=145.0,
            hr_max_bpm=225.0,
        )
        mock_standard = StandardMetrics(pace_avg_min_per_km=6.0)
        mock_asthma = AsthmaAwareMetrics(confidence_score=0.8)

        with (
            patch(
                "run_intelligence.pipeline.fit_parser.parse_fit_file",
                return_value=mock_raw,
            ),
            patch(
                "run_intelligence.pipeline.validation.calculate_standard_metrics",
                return_value=mock_standard,
            ),
            patch(
                "run_intelligence.pipeline.validation.calculate_asthma_aware_metrics",
                return_value=mock_asthma,
            ),
        ):
            result1 = validate_and_flag(str(fit_file))

        with (
            patch(
                "run_intelligence.pipeline.fit_parser.parse_fit_file",
                return_value=mock_raw,
            ),
            patch(
                "run_intelligence.pipeline.validation.calculate_standard_metrics",
                return_value=mock_standard,
            ),
            patch(
                "run_intelligence.pipeline.validation.calculate_asthma_aware_metrics",
                return_value=mock_asthma,
            ),
        ):
            result2 = validate_and_flag(str(fit_file))

        assert result1.confidence_score == result2.confidence_score
        assert result1.low_confidence_flag == result2.low_confidence_flag
        assert (
            result1.data_quality_flags.hr_artifacts
            == result2.data_quality_flags.hr_artifacts
        )
        assert (
            result1.data_quality_flags.gps_drift_segments
            == result2.data_quality_flags.gps_drift_segments
        )

    def test_json_serialization_roundtrip(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        mock_raw = RawRunData(
            timestamp=datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            duration_seconds=3600.0,
            distance_meters=10000.0,
        )
        mock_standard = StandardMetrics(pace_avg_min_per_km=6.0)
        mock_asthma = AsthmaAwareMetrics(confidence_score=0.9)

        with (
            patch(
                "run_intelligence.pipeline.fit_parser.parse_fit_file",
                return_value=mock_raw,
            ),
            patch(
                "run_intelligence.pipeline.validation.calculate_standard_metrics",
                return_value=mock_standard,
            ),
            patch(
                "run_intelligence.pipeline.validation.calculate_asthma_aware_metrics",
                return_value=mock_asthma,
            ),
        ):
            result = validate_and_flag(str(fit_file))

        json_str = result.to_json()
        restored = RunData.from_json(json_str)
        assert restored.confidence_score == result.confidence_score
        assert restored.raw_data.distance_meters == 10000.0


class TestDeterministicBehavior:
    """Test that validation functions are deterministic."""

    def _create_raw_data(self, **kwargs):
        defaults = {
            "timestamp": datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            "duration_seconds": 3600.0,
            "distance_meters": 10000.0,
            "hr_avg_bpm": 145.0,
            "hr_max_bpm": 175.0,
            "cadence_avg_rpm": 170.0,
            "cadence_max_rpm": 185.0,
        }
        defaults.update(kwargs)
        return RawRunData(**defaults)

    def test_detect_hr_artifacts_deterministic(self):
        raw = self._create_raw_data()
        result1 = detect_hr_artifacts(raw)
        result2 = detect_hr_artifacts(raw)
        assert result1 == result2

    def test_detect_gps_drift_deterministic(self):
        raw = self._create_raw_data(
            gps_lat=[40.0, 40.0001, 40.0002],
            gps_lon=[-74.0, -74.0001, -74.0002],
        )
        result1 = detect_gps_drift(raw)
        result2 = detect_gps_drift(raw)
        assert result1 == result2

    def test_detect_cadence_inconsistencies_deterministic(self):
        raw = self._create_raw_data()
        result1 = detect_cadence_inconsistencies(raw)
        result2 = detect_cadence_inconsistencies(raw)
        assert result1 == result2

    def test_calculate_confidence_score_deterministic(self):
        result1 = calculate_confidence_score(0.8, [{"type": "spike"}], [], [])
        result2 = calculate_confidence_score(0.8, [{"type": "spike"}], [], [])
        assert result1 == result2


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def _create_raw_data(self, **kwargs):
        defaults = {
            "timestamp": datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            "duration_seconds": 3600.0,
            "distance_meters": 10000.0,
        }
        defaults.update(kwargs)
        return RawRunData(**defaults)

    def test_all_flags_empty(self):
        flags = DataQualityFlags(
            hr_artifacts=[],
            gps_drift_segments=[],
            cadence_inconsistencies=[],
            confidence_score=1.0,
            low_confidence_flag=False,
        )
        assert flags.confidence_score == 1.0
        assert flags.low_confidence_flag is False

    def test_all_flags_present(self):
        flags = DataQualityFlags(
            hr_artifacts=[
                {
                    "index": 0,
                    "value_bpm": 225.0,
                    "type": "threshold_exceeded",
                    "timestamp": None,
                }
            ],
            gps_drift_segments=[
                {
                    "start_index": 0,
                    "end_index": 1,
                    "distance_meters": 100.0,
                    "duration_seconds": 1.0,
                    "expected_pace": 3.0,
                }
            ],
            cadence_inconsistencies=[
                {
                    "start_index": 0,
                    "end_index": 0,
                    "change_pct": 25.0,
                    "pace_change_pct": 0.0,
                    "is_pace_explained": False,
                }
            ],
            confidence_score=0.3,
            low_confidence_flag=True,
        )
        assert flags.low_confidence_flag is True
        assert len(flags.hr_artifacts) == 1
        assert len(flags.gps_drift_segments) == 1
        assert len(flags.cadence_inconsistencies) == 1

    def test_run_data_with_all_metrics(self):
        raw = self._create_raw_data(
            pace_sec_per_km=360.0,
            hr_avg_bpm=145.0,
            hr_max_bpm=225.0,  # Will trigger artifact
            hr_min_bpm=115.0,
            cadence_avg_rpm=170.0,
            cadence_max_rpm=185.0,
        )
        standard = StandardMetrics(
            pace_avg_min_per_km=6.0,
            hr_zone_distribution={
                "z1": 600,
                "z2": 1200,
                "z3": 900,
                "z4": 600,
                "z5": 300,
            },
        )
        asthma = AsthmaAwareMetrics(
            hr_pace_drift_pct=5.5,
            confidence_score=0.8,
        )
        flags = DataQualityFlags(
            hr_artifacts=[
                {
                    "index": 0,
                    "value_bpm": 225.0,
                    "type": "threshold_exceeded",
                    "timestamp": None,
                }
            ],
            confidence_score=0.65,
            low_confidence_flag=False,
        )
        run_data = RunData(
            raw_data=raw,
            standard_metrics=standard,
            asthma_aware_metrics=asthma,
            data_quality_flags=flags,
            confidence_score=0.65,
            low_confidence_flag=False,
        )
        assert run_data.asthma_aware_metrics.confidence_score == 0.8
        assert run_data.data_quality_flags.hr_artifacts[0]["value_bpm"] == 225.0

    def test_extreme_hr_value(self):
        raw = self._create_raw_data(hr_avg_bpm=145.0, hr_max_bpm=300.0)
        artifacts = detect_hr_artifacts(raw)
        assert len(artifacts) == 1
        assert artifacts[0]["value_bpm"] == 300.0

    def test_empty_gps_lists(self):
        raw = self._create_raw_data(gps_lat=[], gps_lon=[])
        segments = detect_gps_drift(raw)
        assert segments == []

    def test_mismatched_gps_lengths(self):
        raw = self._create_raw_data(
            gps_lat=[40.0, 40.0001],
            gps_lon=[-74.0],
        )
        segments = detect_gps_drift(raw)
        assert isinstance(segments, list)

    def test_cadence_exactly_at_threshold(self):
        raw = self._create_raw_data(cadence_avg_rpm=100.0, cadence_max_rpm=120.0)
        inconsistencies = detect_cadence_inconsistencies(raw)
        assert inconsistencies == []

    def test_json_schema_matches_ac6(self):
        """Verify serialized data_quality_flags matches AC6 schema."""
        flags = DataQualityFlags(
            hr_artifacts=[
                {
                    "index": 0,
                    "value_bpm": 225.0,
                    "type": "threshold_exceeded",
                    "timestamp": "2026-05-18T10:00:00+00:00",
                }
            ],
            gps_drift_segments=[
                {
                    "start_index": 0,
                    "end_index": 1,
                    "distance_meters": 100.0,
                    "duration_seconds": 1.0,
                    "expected_pace": 3.33,
                }
            ],
            cadence_inconsistencies=[
                {
                    "start_index": 0,
                    "end_index": 0,
                    "change_pct": 25.0,
                    "pace_change_pct": 0.0,
                    "is_pace_explained": False,
                }
            ],
            low_confidence_flag=True,
            confidence_score=0.3,
        )
        json_str = flags.to_json()
        parsed = json.loads(json_str)

        # AC6 schema verification
        assert "hr_artifacts" in parsed
        assert parsed["hr_artifacts"][0]["index"] == 0
        assert parsed["hr_artifacts"][0]["value_bpm"] == 225.0
        assert parsed["hr_artifacts"][0]["type"] == "threshold_exceeded"
        assert "timestamp" in parsed["hr_artifacts"][0]

        assert "gps_drift_segments" in parsed
        assert parsed["gps_drift_segments"][0]["start_index"] == 0
        assert parsed["gps_drift_segments"][0]["end_index"] == 1
        assert parsed["gps_drift_segments"][0]["distance_meters"] == 100.0
        assert parsed["gps_drift_segments"][0]["duration_seconds"] == 1.0
        assert parsed["gps_drift_segments"][0]["expected_pace"] == 3.33

        assert "cadence_inconsistencies" in parsed
        assert parsed["cadence_inconsistencies"][0]["start_index"] == 0
        assert parsed["cadence_inconsistencies"][0]["end_index"] == 0
        assert parsed["cadence_inconsistencies"][0]["change_pct"] == 25.0
        assert parsed["cadence_inconsistencies"][0]["pace_change_pct"] == 0.0
        assert parsed["cadence_inconsistencies"][0]["is_pace_explained"] is False

        assert "low_confidence_flag" in parsed
        assert parsed["low_confidence_flag"] is True
        assert "confidence_score" in parsed
        assert parsed["confidence_score"] == 0.3
