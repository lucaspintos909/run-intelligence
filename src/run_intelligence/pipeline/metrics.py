"""Metrics calculation module for standard and asthma-aware running metrics."""

import math
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator

from run_intelligence.config import (
    DEFAULT_AGE,
    ELEVATION_NOISE_FILTER_METERS,
    HR_MAX_AGE_PREDICTED,
    HR_ZONES,
)

if TYPE_CHECKING:
    from run_intelligence.pipeline.fit_parser import RawRunData


class MetricCalculationError(Exception):
    """Custom exception raised when metrics calculation fails."""

    pass


class StandardMetrics(BaseModel):
    """Validated model for standard running metrics derived from RawRunData."""

    model_config = ConfigDict(by_alias=False, extra="forbid")

    pace_avg_min_per_km: Optional[float] = None
    pace_max_min_per_km: Optional[float] = None
    pace_min_min_per_km: Optional[float] = None
    hr_zone_distribution: Optional[dict[str, int]] = None
    cadence_avg_rpm: Optional[float] = None
    cadence_max_rpm: Optional[float] = None
    elevation_gain_m: Optional[float] = None
    elevation_loss_m: Optional[float] = None

    @field_validator(
        "pace_avg_min_per_km",
        "pace_max_min_per_km",
        "pace_min_min_per_km",
        mode="before",
    )
    @classmethod
    def validate_pace(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if math.isnan(v) or math.isinf(v):
                raise ValueError(f"Pace must be a finite number, got {v}")
            if v <= 0 or v > 60:
                raise ValueError(f"Pace must be between 0 and 60 min/km, got {v}")
        return v

    @field_validator("hr_zone_distribution", mode="before")
    @classmethod
    def validate_hr_zone_distribution(
        cls, v: Optional[dict[str, int]]
    ) -> Optional[dict[str, int]]:
        if v is not None:
            for zone, seconds in v.items():
                if zone not in {"z1", "z2", "z3", "z4", "z5"}:
                    raise ValueError(f"Invalid HR zone key: {zone}")
                if not isinstance(seconds, int) or seconds < 0:
                    raise ValueError(
                        f"HR zone seconds must be non-negative int, got {seconds}"
                    )
        return v

    @field_validator("cadence_avg_rpm", "cadence_max_rpm", mode="before")
    @classmethod
    def validate_cadence(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if math.isnan(v) or math.isinf(v):
                raise ValueError(f"Cadence must be a finite number, got {v}")
            if v < 0 or v > 300:
                raise ValueError(f"Cadence must be between 0 and 300 rpm, got {v}")
        return v

    @field_validator("elevation_gain_m", "elevation_loss_m", mode="before")
    @classmethod
    def validate_elevation(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if math.isnan(v) or math.isinf(v):
                raise ValueError(f"Elevation must be a finite number, got {v}")
            if v < 0:
                raise ValueError(f"Elevation must be non-negative, got {v}")
        return v

    @model_validator(mode="after")
    def validate_physiological_ranges(self) -> "StandardMetrics":
        if self.pace_avg_min_per_km is not None:
            if self.pace_max_min_per_km is not None:
                if self.pace_max_min_per_km > self.pace_avg_min_per_km:
                    raise ValueError(
                        "pace_max_min_per_km cannot be slower than pace_avg_min_per_km"
                    )
            if self.pace_min_min_per_km is not None:
                if self.pace_min_min_per_km < self.pace_avg_min_per_km:
                    raise ValueError(
                        "pace_min_min_per_km cannot be faster than pace_avg_min_per_km"
                    )
        return self

    def to_json(self) -> str:
        """Serialize to JSON for database storage using snake_case."""
        return self.model_dump_json(by_alias=False)

    @classmethod
    def from_json(cls, json_str: str) -> "StandardMetrics":
        """Deserialize from JSON string."""
        return cls.model_validate_json(json_str)


def calculate_max_hr(age: int = DEFAULT_AGE) -> int:
    """Calculate maximum heart rate using the 220-age formula.

    Args:
        age: Runner's age in years. Defaults to DEFAULT_AGE from config.

    Returns:
        Maximum heart rate in BPM.

    Raises:
        MetricCalculationError: If age is out of valid range.
    """
    if not (0 < age <= 120):
        raise MetricCalculationError(f"Age must be between 1 and 120, got {age}")
    return int(HR_MAX_AGE_PREDICTED - age)


def calculate_hr_zone_distribution(
    hr_avg: Optional[float],
    hr_max: float,
    duration_seconds: float,
    age: int = DEFAULT_AGE,
) -> dict[str, int]:
    """Estimate HR zone time distribution based on session-level HR statistics.

    This is an approximation since RawRunData only provides avg/max/min HR,
    not per-record HR time series. Accurate zone time requires per-record HR data.

    Args:
        hr_avg: Average heart rate in BPM.
        hr_max: Maximum heart rate in BPM.
        duration_seconds: Total run duration in seconds.
        age: Runner's age for max HR calculation. Defaults to DEFAULT_AGE.

    Returns:
        Dictionary with zone seconds (z1-z5) as keys and time in seconds as values.

    Raises:
        MetricCalculationError: If inputs are invalid.
    """
    if duration_seconds < 0:
        raise MetricCalculationError(
            f"duration_seconds must be non-negative, got {duration_seconds}"
        )

    max_hr = calculate_max_hr(age)
    zones = {f"z{i}": 0 for i in range(1, 6)}

    if hr_avg is None or (isinstance(hr_avg, float) and math.isnan(hr_avg)):
        return zones

    if hr_max > max_hr:
        hr_max = max_hr

    zone_boundaries = [
        (HR_ZONES["z1"][0], HR_ZONES["z1"][1], "z1"),
        (HR_ZONES["z2"][0], HR_ZONES["z2"][1], "z2"),
        (HR_ZONES["z3"][0], HR_ZONES["z3"][1], "z3"),
        (HR_ZONES["z4"][0], HR_ZONES["z4"][1], "z4"),
        (HR_ZONES["z5"][0], HR_ZONES["z5"][1], "z5"),
    ]

    hr_range = hr_max - (max_hr * 0.5)
    if hr_range <= 0:
        zones["z2"] = round(duration_seconds)
        return zones

    target_zone = None
    for lower_pct, upper_pct, zone_key in zone_boundaries:
        lower_hr = max_hr * (lower_pct / 100)
        upper_hr = max_hr * (upper_pct / 100)
        if hr_avg >= lower_hr and hr_avg < upper_hr:
            target_zone = zone_key
            break

    if target_zone is None:
        if hr_avg >= max_hr:
            target_zone = "z5"
        else:
            target_zone = "z2"

    zones[target_zone] = round(duration_seconds)

    return zones


def calculate_elevation_gain_loss(
    gps_elevation: Optional[list[Optional[float]]],
) -> tuple[Optional[float], Optional[float]]:
    """Calculate total elevation gain and loss from GPS elevation data.

    Args:
        gps_elevation: List of elevation values in meters (can contain None).

    Returns:
        Tuple of (elevation_gain_m, elevation_loss_m). Returns (None, None) if
        insufficient data.
    """
    if gps_elevation is None or len(gps_elevation) < 2:
        return None, None

    valid_points: list[float] = []
    for point in gps_elevation:
        if point is not None:
            try:
                val = float(point)
                if math.isnan(val) or math.isinf(val):
                    continue
                valid_points.append(val)
            except (TypeError, ValueError):
                continue

    if len(valid_points) < 2:
        return None, None

    gain = 0.0
    loss = 0.0
    noise_threshold = ELEVATION_NOISE_FILTER_METERS

    for i in range(1, len(valid_points)):
        delta = valid_points[i] - valid_points[i - 1]
        if delta >= noise_threshold:
            gain += delta
        elif delta <= -noise_threshold:
            loss += abs(delta)

    return round(gain, 2), round(loss, 2)


def calculate_standard_metrics(raw_data: "RawRunData") -> StandardMetrics:
    """Calculate standard running metrics from raw .fit file data.

    This function is DETERMINISTIC: same RawRunData input always produces
    identical StandardMetrics output. NO LLM calls, NO randomness.

    Args:
        raw_data: RawRunData instance from fit_parser.parse_fit_file()

    Returns:
        StandardMetrics Pydantic model with all calculated metrics.

    Raises:
        MetricCalculationError: If calculation fails due to invalid data.
    """
    if raw_data is None:
        raise MetricCalculationError("raw_data cannot be None")

    if raw_data.pace_sec_per_km is not None and raw_data.pace_sec_per_km > 0:
        pace_avg_min_per_km = round(raw_data.pace_sec_per_km / 60, 2)
        pace_max_min_per_km = pace_avg_min_per_km
        pace_min_min_per_km = pace_avg_min_per_km
    else:
        pace_avg_min_per_km = None
        pace_max_min_per_km = None
        pace_min_min_per_km = None

    hr_zone_seconds = None

    hr_avg_valid = (
        raw_data.hr_avg_bpm is not None
        and not (
            isinstance(raw_data.hr_avg_bpm, float) and math.isnan(raw_data.hr_avg_bpm)
        )
    )
    if (
        hr_avg_valid
        and raw_data.hr_max_bpm is not None
        and raw_data.duration_seconds is not None
    ):
        try:
            zone_dist = calculate_hr_zone_distribution(
                hr_avg=raw_data.hr_avg_bpm,
                hr_max=raw_data.hr_max_bpm,
                duration_seconds=raw_data.duration_seconds,
            )
            hr_zone_seconds = zone_dist
        except (ValueError, TypeError, ArithmeticError) as e:
            raise MetricCalculationError(
                "Failed to calculate HR zone distribution"
            ) from e

    elevation_gain, elevation_loss = calculate_elevation_gain_loss(raw_data.gps_elevation)

    try:
        return StandardMetrics(
            pace_avg_min_per_km=pace_avg_min_per_km,
            pace_max_min_per_km=pace_max_min_per_km,
            pace_min_min_per_km=pace_min_min_per_km,
            hr_zone_distribution=hr_zone_seconds,
            cadence_avg_rpm=raw_data.cadence_avg_rpm,
            cadence_max_rpm=raw_data.cadence_max_rpm,
            elevation_gain_m=elevation_gain,
            elevation_loss_m=elevation_loss,
        )
    except ValidationError as e:
        raise MetricCalculationError(
            f"Failed to calculate standard metrics: {e}"
        ) from e


__all__ = [
    "MetricCalculationError",
    "StandardMetrics",
    "calculate_standard_metrics",
    "calculate_max_hr",
    "calculate_hr_zone_distribution",
    "calculate_elevation_gain_loss",
]
