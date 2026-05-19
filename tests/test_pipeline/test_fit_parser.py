"""Tests for fit_parser module."""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from run_intelligence.pipeline.fit_parser import (
    FitParseError,
    RawRunData,
    parse_fit_file,
    _semicircles_to_degrees,
)


class TestSemicirclesConversion:
    """Test GPS semicircle to degrees conversion."""

    def test_zero_semicircles(self):
        assert _semicircles_to_degrees(0) == 0.0

    def test_known_conversion(self):
        result = _semicircles_to_degrees(1077952576)
        assert abs(result - 90.35) < 0.01

    def test_negative_semicircles(self):
        result = _semicircles_to_degrees(-1077952576)
        assert abs(result - -90.35) < 0.01

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Expected numeric semicircles"):
            _semicircles_to_degrees("not_a_number")


class TestRawRunDataModel:
    """Test RawRunData Pydantic model."""

    def test_valid_creation(self):
        data = RawRunData(
            timestamp=datetime.now(timezone.utc),
            duration_seconds=3600.0,
            distance_meters=10000.0,
        )
        assert data.timestamp is not None
        assert data.duration_seconds == 3600.0
        assert data.distance_meters == 10000.0

    def test_negative_duration_raises(self):
        with pytest.raises(ValueError):
            RawRunData(
                timestamp=datetime.now(timezone.utc),
                duration_seconds=-100.0,
                distance_meters=10000.0,
            )

    def test_zero_distance_raises(self):
        with pytest.raises(ValueError):
            RawRunData(
                timestamp=datetime.now(timezone.utc),
                duration_seconds=3600.0,
                distance_meters=0.0,
            )

    def test_optional_fields_default_to_none(self):
        data = RawRunData(
            timestamp=datetime.now(timezone.utc),
            duration_seconds=3600.0,
            distance_meters=10000.0,
        )
        assert data.pace_sec_per_km is None
        assert data.hr_avg_bpm is None
        assert data.hr_max_bpm is None
        assert data.hr_min_bpm is None
        assert data.cadence_avg_rpm is None
        assert data.cadence_max_rpm is None
        assert data.gps_lat is None
        assert data.gps_lon is None
        assert data.gps_elevation is None

    def test_hr_data_inclusion(self):
        data = RawRunData(
            timestamp=datetime.now(timezone.utc),
            duration_seconds=3600.0,
            distance_meters=10000.0,
            hr_avg_bpm=145.0,
            hr_max_bpm=175.0,
            hr_min_bpm=120.0,
        )
        assert data.hr_avg_bpm == 145.0
        assert data.hr_max_bpm == 175.0
        assert data.hr_min_bpm == 120.0

    def test_hr_out_of_range_raises(self):
        with pytest.raises(ValueError, match="Heart rate must be between 0 and 300"):
            RawRunData(
                timestamp=datetime.now(timezone.utc),
                duration_seconds=3600.0,
                distance_meters=10000.0,
                hr_avg_bpm=400.0,
            )

    def test_cadence_data_inclusion(self):
        data = RawRunData(
            timestamp=datetime.now(timezone.utc),
            duration_seconds=3600.0,
            distance_meters=10000.0,
            cadence_avg_rpm=170.0,
            cadence_max_rpm=185.0,
        )
        assert data.cadence_avg_rpm == 170.0
        assert data.cadence_max_rpm == 185.0

    def test_cadence_out_of_range_raises(self):
        with pytest.raises(ValueError, match="Cadence must be between 0 and 300"):
            RawRunData(
                timestamp=datetime.now(timezone.utc),
                duration_seconds=3600.0,
                distance_meters=10000.0,
                cadence_avg_rpm=400.0,
            )

    def test_gps_arrays(self):
        data = RawRunData(
            timestamp=datetime.now(timezone.utc),
            duration_seconds=3600.0,
            distance_meters=10000.0,
            gps_lat=[37.7749, 37.7750],
            gps_lon=[-122.4194, -122.4195],
            gps_elevation=[100.0, 101.0],
        )
        assert len(data.gps_lat) == 2
        assert len(data.gps_lon) == 2
        assert len(data.gps_elevation) == 2

    def test_gps_lat_out_of_range_raises(self):
        with pytest.raises(ValueError, match="Latitude out of range"):
            RawRunData(
                timestamp=datetime.now(timezone.utc),
                duration_seconds=3600.0,
                distance_meters=10000.0,
                gps_lat=[95.0],
                gps_lon=[-122.4194],
            )

    def test_gps_lon_out_of_range_raises(self):
        with pytest.raises(ValueError, match="Longitude out of range"):
            RawRunData(
                timestamp=datetime.now(timezone.utc),
                duration_seconds=3600.0,
                distance_meters=10000.0,
                gps_lat=[37.7749],
                gps_lon=[-190.0],
            )


class TestRawRunDataSerialization:
    """Test JSON serialization and deserialization."""

    def test_to_json(self):
        data = RawRunData(
            timestamp=datetime(2026, 5, 18, 10, 30, 0, tzinfo=timezone.utc),
            duration_seconds=3600.0,
            distance_meters=10000.0,
            pace_sec_per_km=360.0,
            hr_avg_bpm=145.0,
            hr_max_bpm=175.0,
            hr_min_bpm=120.0,
            cadence_avg_rpm=170.0,
            cadence_max_rpm=185.0,
            gps_lat=[37.7749],
            gps_lon=[-122.4194],
            gps_elevation=[100.0],
        )
        json_str = data.to_json()
        parsed = json.loads(json_str)
        assert parsed["timestamp"] == "2026-05-18T10:30:00Z"
        assert parsed["duration_seconds"] == 3600.0
        assert parsed["distance_meters"] == 10000.0
        assert parsed["pace_sec_per_km"] == 360.0
        assert parsed["hr_avg_bpm"] == 145.0
        assert parsed["cadence_avg_rpm"] == 170.0

    def test_json_roundtrip(self):
        original = RawRunData(
            timestamp=datetime(2026, 5, 18, 10, 30, 0, tzinfo=timezone.utc),
            duration_seconds=3600.0,
            distance_meters=10000.0,
            pace_sec_per_km=360.0,
            hr_avg_bpm=145.0,
            hr_max_bpm=175.0,
            hr_min_bpm=120.0,
        )
        json_str = original.to_json()
        restored = RawRunData.from_json(json_str)
        assert restored.duration_seconds == original.duration_seconds
        assert restored.distance_meters == original.distance_meters
        assert restored.hr_avg_bpm == original.hr_avg_bpm

    def test_from_json_invalid_raises(self):
        with pytest.raises(Exception):
            RawRunData.from_json("invalid json")


class TestFitParseError:
    """Test FitParseError exception."""

    def test_raises_with_message(self):
        with pytest.raises(FitParseError) as exc_info:
            raise FitParseError("Test error message")
        assert str(exc_info.value) == "Test error message"


class TestParseFitFile:
    """Test parse_fit_file function with mocked FitFile."""

    def _create_mock_message(self, msg_type, fields):
        mock_msg = MagicMock()
        mock_msg.name = msg_type

        mock_fields = []
        for f in fields:
            mock_field = MagicMock()
            mock_field.name = f["name"]
            mock_field.value = f["value"]
            mock_fields.append(mock_field)

        mock_msg.fields = mock_fields
        return mock_msg

    def test_file_not_found(self):
        with patch("builtins.open", side_effect=FileNotFoundError("No such file")):
            with pytest.raises(FitParseError) as exc_info:
                parse_fit_file("/nonexistent/file.fit")
            assert "File not found" in str(exc_info.value)

    def test_permission_denied(self):
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(FitParseError) as exc_info:
                parse_fit_file("/protected/file.fit")
            assert "Permission denied" in str(exc_info.value)

    def test_missing_timestamp(self):
        mock_fit_file = MagicMock()

        session_msg = self._create_mock_message("session", [
            {"name": "total_timer_time", "value": 3600.0},
            {"name": "total_distance", "value": 10000.0},
        ])
        record_msg = self._create_mock_message("record", [
            {"name": "heart_rate", "value": 145},
        ])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg, record_msg]
            return [session_msg] if name == "session" else [record_msg] if name == "record" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                with pytest.raises(FitParseError) as exc_info:
                    parse_fit_file("/test/file.fit")
                assert "timestamp" in str(exc_info.value).lower()

    def test_missing_duration(self):
        mock_fit_file = MagicMock()

        session_msg = self._create_mock_message("session", [
            {"name": "timestamp", "value": datetime.now(timezone.utc)},
            {"name": "total_distance", "value": 10000.0},
        ])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg]
            return [session_msg] if name == "session" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                with pytest.raises(FitParseError) as exc_info:
                    parse_fit_file("/test/file.fit")
                assert "duration" in str(exc_info.value).lower()

    def test_missing_distance(self):
        mock_fit_file = MagicMock()

        session_msg = self._create_mock_message("session", [
            {"name": "timestamp", "value": datetime.now(timezone.utc)},
            {"name": "total_timer_time", "value": 3600.0},
        ])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg]
            return [session_msg] if name == "session" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                with pytest.raises(FitParseError) as exc_info:
                    parse_fit_file("/test/file.fit")
                assert "distance" in str(exc_info.value).lower()

    def test_duration_fallback_to_elapsed_time(self):
        mock_fit_file = MagicMock()

        session_timestamp = datetime(2026, 5, 18, 10, 30, 0, tzinfo=timezone.utc)
        session_msg = self._create_mock_message("session", [
            {"name": "timestamp", "value": session_timestamp},
            {"name": "elapsed_time", "value": 1800.0},
            {"name": "total_distance", "value": 5000.0},
        ])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg]
            return [session_msg] if name == "session" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                result = parse_fit_file("/test/file.fit")

        assert result.duration_seconds == 1800.0

    def test_successful_parse(self):
        mock_fit_file = MagicMock()

        session_timestamp = datetime(2026, 5, 18, 10, 30, 0, tzinfo=timezone.utc)
        session_msg = self._create_mock_message("session", [
            {"name": "timestamp", "value": session_timestamp},
            {"name": "total_timer_time", "value": 3600.0},
            {"name": "total_distance", "value": 10000.0},
        ])
        record_msg = self._create_mock_message("record", [
            {"name": "heart_rate", "value": 145},
            {"name": "cadence", "value": 170},
            {"name": "position_lat", "value": 1077952576},
            {"name": "position_long", "value": -1077952576},
            {"name": "altitude", "value": 100.0},
        ])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg, record_msg]
            return [session_msg] if name == "session" else [record_msg] if name == "record" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                result = parse_fit_file("/test/file.fit")

        assert result.timestamp == session_timestamp
        assert result.duration_seconds == 3600.0
        assert result.distance_meters == 10000.0
        assert result.pace_sec_per_km == 360.0
        assert result.hr_avg_bpm == 145.0
        assert result.hr_max_bpm == 145.0
        assert result.hr_min_bpm == 145.0
        assert result.cadence_avg_rpm == 170.0
        assert result.cadence_max_rpm == 170.0

    def test_missing_optional_fields_no_error(self):
        mock_fit_file = MagicMock()

        session_timestamp = datetime(2026, 5, 18, 10, 30, 0, tzinfo=timezone.utc)
        session_msg = self._create_mock_message("session", [
            {"name": "timestamp", "value": session_timestamp},
            {"name": "total_timer_time", "value": 3600.0},
            {"name": "total_distance", "value": 10000.0},
        ])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg]
            return [session_msg] if name == "session" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                result = parse_fit_file("/test/file.fit")

        assert result.hr_avg_bpm is None
        assert result.cadence_avg_rpm is None
        assert result.gps_lat is None
        assert result.gps_lon is None
        assert result.gps_elevation is None

    def test_running_cadence_field(self):
        mock_fit_file = MagicMock()

        session_timestamp = datetime(2026, 5, 18, 10, 30, 0, tzinfo=timezone.utc)
        session_msg = self._create_mock_message("session", [
            {"name": "timestamp", "value": session_timestamp},
            {"name": "total_timer_time", "value": 3600.0},
            {"name": "total_distance", "value": 10000.0},
        ])
        record_msg = self._create_mock_message("record", [
            {"name": "running_cadence", "value": 175},
        ])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg, record_msg]
            return [session_msg] if name == "session" else [record_msg] if name == "record" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                result = parse_fit_file("/test/file.fit")

        assert result.cadence_avg_rpm == 175.0

    def test_duplicate_cadence_not_double_counted(self):
        mock_fit_file = MagicMock()

        session_timestamp = datetime(2026, 5, 18, 10, 30, 0, tzinfo=timezone.utc)
        session_msg = self._create_mock_message("session", [
            {"name": "timestamp", "value": session_timestamp},
            {"name": "total_timer_time", "value": 3600.0},
            {"name": "total_distance", "value": 10000.0},
        ])
        record_msg = self._create_mock_message("record", [
            {"name": "cadence", "value": 170},
            {"name": "running_cadence", "value": 175},
        ])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg, record_msg]
            return [session_msg] if name == "session" else [record_msg] if name == "record" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                result = parse_fit_file("/test/file.fit")

        # running_cadence takes precedence; only one value should be recorded
        assert result.cadence_avg_rpm == 175.0

    def test_gps_partial_fix_dropped(self):
        mock_fit_file = MagicMock()

        session_timestamp = datetime(2026, 5, 18, 10, 30, 0, tzinfo=timezone.utc)
        session_msg = self._create_mock_message("session", [
            {"name": "timestamp", "value": session_timestamp},
            {"name": "total_timer_time", "value": 3600.0},
            {"name": "total_distance", "value": 10000.0},
        ])
        record_lat_only = self._create_mock_message("record", [
            {"name": "position_lat", "value": 1077952576},
        ])
        record_full = self._create_mock_message("record", [
            {"name": "position_lat", "value": 1077952576},
            {"name": "position_long", "value": -1077952576},
        ])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg, record_lat_only, record_full]
            return [session_msg] if name == "session" else [record_lat_only, record_full] if name == "record" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                result = parse_fit_file("/test/file.fit")

        # Only the record with both lat and lon should be included
        assert result.gps_lat is not None
        assert len(result.gps_lat) == 1
        assert len(result.gps_lon) == 1

    def test_max_records_exceeded(self):
        mock_fit_file = MagicMock()

        session_timestamp = datetime(2026, 5, 18, 10, 30, 0, tzinfo=timezone.utc)
        session_msg = self._create_mock_message("session", [
            {"name": "timestamp", "value": session_timestamp},
            {"name": "total_timer_time", "value": 3600.0},
            {"name": "total_distance", "value": 10000.0},
        ])
        record_msg = self._create_mock_message("record", [])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg] + [record_msg] * 1001
            return [session_msg] if name == "session" else [record_msg] * 1001 if name == "record" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                with pytest.raises(FitParseError, match="Exceeded max records limit"):
                    parse_fit_file("/test/file.fit")

    def test_max_duration_exceeded(self):
        mock_fit_file = MagicMock()

        session_timestamp = datetime(2026, 5, 18, 10, 30, 0, tzinfo=timezone.utc)
        session_msg = self._create_mock_message("session", [
            {"name": "timestamp", "value": session_timestamp},
            {"name": "total_timer_time", "value": 99999.0},
            {"name": "total_distance", "value": 10000.0},
        ])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg]
            return [session_msg] if name == "session" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                with pytest.raises(FitParseError, match="exceeds max allowed"):
                    parse_fit_file("/test/file.fit")

    def test_pace_not_calculated_for_near_zero_distance(self):
        mock_fit_file = MagicMock()

        session_timestamp = datetime(2026, 5, 18, 10, 30, 0, tzinfo=timezone.utc)
        session_msg = self._create_mock_message("session", [
            {"name": "timestamp", "value": session_timestamp},
            {"name": "total_timer_time", "value": 3600.0},
            {"name": "total_distance", "value": 0.5},
        ])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg]
            return [session_msg] if name == "session" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                result = parse_fit_file("/test/file.fit")

        assert result.pace_sec_per_km is None

    def test_fitparse_error_wrapped(self):
        from fitparse import FitParseError as LibFitParseError

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", side_effect=LibFitParseError("corrupted")):
                with pytest.raises(FitParseError, match="FIT library error"):
                    parse_fit_file("/corrupted/file.fit")

    def test_validation_error_wrapped(self):
        mock_fit_file = MagicMock()

        session_msg = self._create_mock_message("session", [
            {"name": "timestamp", "value": "not_a_datetime"},
            {"name": "total_timer_time", "value": 3600.0},
            {"name": "total_distance", "value": 10000.0},
        ])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg]
            return [session_msg] if name == "session" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                with pytest.raises(FitParseError, match="Validation error"):
                    parse_fit_file("/test/file.fit")

    def test_nan_values_filtered(self):
        mock_fit_file = MagicMock()

        session_timestamp = datetime(2026, 5, 18, 10, 30, 0, tzinfo=timezone.utc)
        session_msg = self._create_mock_message("session", [
            {"name": "timestamp", "value": session_timestamp},
            {"name": "total_timer_time", "value": 3600.0},
            {"name": "total_distance", "value": 10000.0},
        ])
        record_msg = self._create_mock_message("record", [
            {"name": "heart_rate", "value": float("nan")},
            {"name": "heart_rate", "value": 145},
        ])

        def get_messages_side_effect(name=None):
            if name is None:
                return [session_msg, record_msg]
            return [session_msg] if name == "session" else [record_msg] if name == "record" else []

        mock_fit_file.get_messages.side_effect = get_messages_side_effect

        with patch("builtins.open", MagicMock()):
            with patch("fitparse.FitFile", return_value=mock_fit_file):
                result = parse_fit_file("/test/file.fit")

        assert result.hr_avg_bpm == 145.0


class TestErrorOutput:
    """Test error logging uses stderr with correct format."""

    def test_file_not_found_logs_correct_format(self, caplog):
        with patch("builtins.open", side_effect=FileNotFoundError("No such file")):
            with pytest.raises(FitParseError):
                parse_fit_file("/nonexistent/file.fit")

        assert any(
            "[PIPELINE_ERROR] fit_parser:" in record.message
            for record in caplog.records
        )
        error_records = [
            r for r in caplog.records
            if "[PIPELINE_ERROR] fit_parser:" in r.message
        ]
        assert len(error_records) > 0
