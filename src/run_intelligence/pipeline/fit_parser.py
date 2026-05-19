"""FIT file parser for extracting raw running metrics from Coros watch .fit files."""

import logging
import math
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator

from run_intelligence.config import FIT_PARSING

logger = logging.getLogger(__name__)


class FitParseError(Exception):
    """Custom exception raised when FIT file parsing fails."""

    pass


class RawRunData(BaseModel):
    """Validated model for raw running metrics from .fit files."""

    model_config = ConfigDict(by_alias=False, extra="forbid")

    timestamp: datetime
    duration_seconds: float
    distance_meters: float
    pace_sec_per_km: Optional[float] = None
    hr_avg_bpm: Optional[float] = None
    hr_max_bpm: Optional[float] = None
    hr_min_bpm: Optional[float] = None
    cadence_avg_rpm: Optional[float] = None
    cadence_max_rpm: Optional[float] = None
    gps_lat: Optional[list[float]] = None
    gps_lon: Optional[list[float]] = None
    gps_elevation: Optional[list[float]] = None

    @field_validator("duration_seconds", "distance_meters")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"{cls.__name__} must be positive, got {v}")
        return v

    @field_validator("hr_avg_bpm", "hr_max_bpm", "hr_min_bpm")
    @classmethod
    def validate_hr_bounds(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0 or v > 300):
            raise ValueError(f"Heart rate must be between 0 and 300 bpm, got {v}")
        return v

    @field_validator("cadence_avg_rpm", "cadence_max_rpm")
    @classmethod
    def validate_cadence_bounds(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0 or v > 300):
            raise ValueError(f"Cadence must be between 0 and 300 rpm, got {v}")
        return v

    @model_validator(mode="after")
    def validate_gps_bounds(self) -> "RawRunData":
        if self.gps_lat is not None:
            for lat in self.gps_lat:
                if lat < -91 or lat > 91:
                    raise ValueError(f"Latitude out of range: {lat}")
        if self.gps_lon is not None:
            for lon in self.gps_lon:
                if lon < -181 or lon > 181:
                    raise ValueError(f"Longitude out of range: {lon}")
        return self

    def to_json(self) -> str:
        """Serialize to JSON for database storage using snake_case."""
        return self.model_dump_json(by_alias=False)

    @classmethod
    def from_json(cls, json_str: str) -> "RawRunData":
        """Deserialize from JSON string."""
        return cls.model_validate_json(json_str)


def _semicircles_to_degrees(semicircles) -> float:
    """Convert FIT semicircles to degrees.

    FIT protocol stores lat/lon as 32-bit signed integers in semicircles.
    Conversion: degrees = semicircles * (180 / 2^31)
    """
    if not isinstance(semicircles, (int, float)):
        raise ValueError(
            f"Expected numeric semicircles, got {type(semicircles).__name__}"
        )
    return semicircles * (180.0 / 2**31)


def _is_valid_number(value) -> bool:
    """Check if value is a valid finite number (not None, NaN, or non-numeric)."""
    if value is None:
        return False
    try:
        num = float(value)
        return not math.isnan(num)
    except (TypeError, ValueError):
        return False


def parse_fit_file(file_path: str) -> RawRunData:
    """Parse a .fit file and extract raw running metrics.

    Args:
        file_path: Path to the .fit file to parse.

    Returns:
        RawRunData with all extracted metrics.

    Raises:
        FitParseError: If the file cannot be parsed or is invalid.
    """
    from fitparse import FitFile, FitParseError as _FitParseLibError

    try:
        fit_file = FitFile(file_path)
    except FileNotFoundError:
        logger.error("[PIPELINE_ERROR] fit_parser: File not found: %s", file_path)
        raise FitParseError(f"File not found: {file_path}")
    except PermissionError:
        logger.error("[PIPELINE_ERROR] fit_parser: Permission denied: %s", file_path)
        raise FitParseError(f"Permission denied: {file_path}")
    except _FitParseLibError as e:
        logger.error("[PIPELINE_ERROR] fit_parser: FIT library error: %s", str(e))
        raise FitParseError(f"FIT library error: {str(e)}")
    except Exception as e:
        logger.error("[PIPELINE_ERROR] fit_parser: Failed to open file: %s", str(e))
        raise FitParseError(f"Failed to open file: {str(e)}")

    timestamp = None
    duration_seconds = None
    distance_meters = None
    hr_values: list[float] = []
    cadence_values: list[float] = []
    gps_records: list[tuple[float, float, Optional[float]]] = []

    record_count = 0

    try:
        for message in fit_file.get_messages():
            message_type = message.name

            if message_type == "session":
                for field in message.fields:
                    if field.name == "timestamp" and field.value is not None:
                        timestamp = field.value
                    elif (
                        field.name == "total_timer_time"
                        and _is_valid_number(field.value)
                    ):
                        duration_seconds = float(field.value)
                    elif (
                        field.name == "elapsed_time"
                        and _is_valid_number(field.value)
                        and duration_seconds is None
                    ):
                        duration_seconds = float(field.value)
                    elif (
                        field.name == "total_distance"
                        and _is_valid_number(field.value)
                    ):
                        distance_meters = float(field.value)

            elif message_type == "record":
                record_count += 1
                if record_count > FIT_PARSING["max_records"]:
                    raise FitParseError(
                        f"Exceeded max records limit: {FIT_PARSING['max_records']}"
                    )

                record_lat = None
                record_lon = None
                record_alt = None
                record_cadence = None
                record_running_cadence = None

                for field in message.fields:
                    if field.name == "heart_rate" and _is_valid_number(field.value):
                        hr_values.append(float(field.value))
                    elif (
                        field.name == "running_cadence"
                        and _is_valid_number(field.value)
                    ):
                        record_running_cadence = float(field.value)
                    elif field.name == "cadence" and _is_valid_number(field.value):
                        record_cadence = float(field.value)
                    elif field.name == "position_lat" and _is_valid_number(
                        field.value
                    ):
                        record_lat = _semicircles_to_degrees(int(float(field.value)))
                    elif field.name == "position_long" and _is_valid_number(
                        field.value
                    ):
                        record_lon = _semicircles_to_degrees(int(float(field.value)))
                    elif field.name == "altitude" and _is_valid_number(field.value):
                        record_alt = float(field.value)

                if record_running_cadence is not None:
                    cadence_values.append(record_running_cadence)
                elif record_cadence is not None:
                    cadence_values.append(record_cadence)

                if record_lat is not None and record_lon is not None:
                    gps_records.append((record_lat, record_lon, record_alt))

            elif message_type == "activity":
                for field in message.fields:
                    if (
                        field.name == "timestamp"
                        and field.value is not None
                        and timestamp is None
                    ):
                        timestamp = field.value

    except Exception as e:
        if isinstance(e, FitParseError):
            raise
        logger.error("[PIPELINE_ERROR] fit_parser: Error parsing FIT file: %s", str(e))
        raise FitParseError(f"Error parsing FIT file: {str(e)}")

    if timestamp is None:
        logger.error(
            "[PIPELINE_ERROR] fit_parser: Missing required field: timestamp"
        )
        raise FitParseError("Missing required field: timestamp")

    if duration_seconds is None:
        logger.error(
            "[PIPELINE_ERROR] fit_parser: Missing required field: duration_seconds"
        )
        raise FitParseError("Missing required field: duration_seconds")

    if distance_meters is None:
        logger.error(
            "[PIPELINE_ERROR] fit_parser: Missing required field: distance_meters"
        )
        raise FitParseError("Missing required field: distance_meters")

    if duration_seconds > FIT_PARSING["max_duration_seconds"]:
        raise FitParseError(
            f"Duration {duration_seconds}s exceeds max allowed "
            f"{FIT_PARSING['max_duration_seconds']}s"
        )

    # Filter NaN values before aggregation
    hr_values = [v for v in hr_values if not math.isnan(v)]
    cadence_values = [v for v in cadence_values if not math.isnan(v)]

    hr_avg = round(sum(hr_values) / len(hr_values), 1) if hr_values else None
    hr_max = max(hr_values) if hr_values else None
    hr_min = min(hr_values) if hr_values else None

    cadence_avg = (
        round(sum(cadence_values) / len(cadence_values), 1) if cadence_values else None
    )
    cadence_max = max(cadence_values) if cadence_values else None

    pace_sec_per_km: Optional[float] = None
    min_distance_for_pace = 1.0  # 1 meter minimum to avoid absurd pace values
    if distance_meters >= min_distance_for_pace:
        pace_sec_per_km = round(duration_seconds / (distance_meters / 1000), 1)

    gps_lat = [r[0] for r in gps_records] if gps_records else None
    gps_lon = [r[1] for r in gps_records] if gps_records else None
    gps_elevation = (
        [r[2] for r in gps_records if r[2] is not None]
        if any(r[2] is not None for r in gps_records)
        else None
    )

    try:
        return RawRunData(
            timestamp=timestamp,
            duration_seconds=duration_seconds,
            distance_meters=distance_meters,
            pace_sec_per_km=pace_sec_per_km,
            hr_avg_bpm=hr_avg,
            hr_max_bpm=hr_max,
            hr_min_bpm=hr_min,
            cadence_avg_rpm=cadence_avg,
            cadence_max_rpm=cadence_max,
            gps_lat=gps_lat,
            gps_lon=gps_lon,
            gps_elevation=gps_elevation,
        )
    except ValidationError as e:
        logger.error("[PIPELINE_ERROR] fit_parser: Validation error: %s", str(e))
        raise FitParseError(f"Validation error: {str(e)}")
