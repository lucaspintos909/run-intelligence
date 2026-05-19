"""Metrics calculation module for standard and asthma-aware running metrics."""

import math
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator

from run_intelligence.config import (
    ASTHMA_METRICS,
    CADENCE_CHANGE_THRESHOLD_PCT,
    DEFAULT_AGE,
    ELEVATION_NOISE_FILTER_METERS,
    HR_MAX_AGE_PREDICTED,
    HR_ZONE_ANOMALY_THRESHOLD,
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


class AsthmaAwareMetrics(BaseModel):
    """Validated model for asthma-aware metrics derived from RawRunData."""

    model_config = ConfigDict(by_alias=False, extra="forbid")

    hr_pace_drift_pct: Optional[float] = None
    hr_pace_drift_confidence: Optional[float] = None
    hr_variability_rmssd: Optional[float] = None
    hr_variability_confidence: Optional[float] = None
    hr_zone_anomaly_flag: Optional[bool] = None
    hr_zone_anomaly_confidence: Optional[float] = None
    cadence_compensation_flag: Optional[bool] = None
    cadence_compensation_confidence: Optional[float] = None
    confidence_score: Optional[float] = None

    @field_validator("hr_pace_drift_pct", mode="before")
    @classmethod
    def validate_drift_finite(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if math.isnan(v) or math.isinf(v):
                raise ValueError(f"Metric must be a finite number, got {v}")
        return v

    @field_validator("hr_variability_rmssd", mode="before")
    @classmethod
    def validate_variability_finite(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if math.isnan(v) or math.isinf(v):
                raise ValueError(f"Metric must be a finite number, got {v}")
        return v

    @field_validator(
        "hr_pace_drift_confidence",
        "hr_variability_confidence",
        "hr_zone_anomaly_confidence",
        "cadence_compensation_confidence",
        "confidence_score",
        mode="before",
    )
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if math.isnan(v) or math.isinf(v):
                raise ValueError(f"Confidence must be a finite number, got {v}")
            if v < 0 or v > 1:
                raise ValueError(f"Confidence must be between 0 and 1, got {v}")
        return v

    @model_validator(mode="after")
    def validate_physiological_ranges(self) -> "AsthmaAwareMetrics":
        if self.hr_pace_drift_pct is not None:
            if abs(self.hr_pace_drift_pct) > 100:
                raise ValueError(
                    f"hr_pace_drift_pct must be between -100 and 100, got {self.hr_pace_drift_pct}"
                )
        if self.hr_variability_rmssd is not None:
            if self.hr_variability_rmssd < 0:
                raise ValueError(
                    f"hr_variability_rmssd must be non-negative, got {self.hr_variability_rmssd}"
                )
        return self

    def to_json(self) -> str:
        """Serialize to JSON for database storage using snake_case."""
        return self.model_dump_json(by_alias=False)

    @classmethod
    def from_json(cls, json_str: str) -> "AsthmaAwareMetrics":
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


def calculate_hr_pace_drift(
    hr_avg: Optional[float],
    hr_max: Optional[float],
    hr_min: Optional[float],
    pace_sec_per_km: Optional[float],
    duration_seconds: Optional[float],
) -> tuple[Optional[float], Optional[float]]:
    """Calculate HR/pace drift percentage and confidence.

    HR/pace drift quantifies how much pace decouples from HR as the run progresses.
    A positive drift percentage indicates pace slows relative to HR (possible bronchospasm
    indicator). Since RawRunData only provides session-level aggregates (not per-record
    time series), this is an estimation using available HR mins/maxes and avg pace.

    Args:
        hr_avg: Average heart rate in BPM.
        hr_max: Maximum heart rate in BPM.
        hr_min: Minimum heart rate in BPM.
        pace_sec_per_km: Average pace in seconds per km.
        duration_seconds: Total run duration in seconds.

    Returns:
        Tuple of (drift_percentage, confidence_score).
        Returns (None, None) if HR or pace data is unavailable.
    """
    if (
        hr_avg is None
        or hr_max is None
        or hr_min is None
        or pace_sec_per_km is None
        or duration_seconds is None
        or duration_seconds <= 0
    ):
        return None, None

    if isinstance(hr_avg, float) and math.isnan(hr_avg):
        return None, None
    if isinstance(hr_max, float) and math.isnan(hr_max):
        return None, None
    if isinstance(hr_min, float) and math.isnan(hr_min):
        return None, None
    if isinstance(pace_sec_per_km, float) and math.isnan(pace_sec_per_km):
        return None, None
    if isinstance(duration_seconds, float) and math.isnan(duration_seconds):
        return None, None

    if hr_min < 0 or hr_max < 0 or hr_avg < 0:
        return None, None

    if hr_min > hr_max:
        return None, None

    hr_range = hr_max - hr_min
    if hr_range < ASTHMA_METRICS["hr_pace_drift"]["min_hr_range_bpm"]:
        return None, None

    if pace_sec_per_km <= 0:
        return None, None

    duration_minutes = duration_seconds / 60.0

    try:
        # Estimate HR in first and second halves of the run
        estimated_first_half_hr = hr_min + (hr_range * 0.25)
        estimated_second_half_hr = hr_min + (hr_range * 0.75)
        hr_change_ratio = (estimated_first_half_hr - estimated_second_half_hr) / estimated_first_half_hr

        # Estimate pace degradation over duration
        # Heuristic: pace degrades ~5% per 30 minutes, capped at 20%
        pace_degradation_pct = min(duration_minutes / 30.0 * 0.05, 0.20)
        estimated_first_half_pace = pace_sec_per_km
        estimated_second_half_pace = pace_sec_per_km * (1.0 + pace_degradation_pct)
        pace_change_ratio = (estimated_first_half_pace - estimated_second_half_pace) / estimated_first_half_pace

        if abs(hr_change_ratio) < 0.01:
            return None, None

        # Per spec: product of pace and HR change ratios
        drift_pct = pace_change_ratio * hr_change_ratio * 100.0

        if abs(drift_pct) > 100:
            return None, None

    except (ValueError, ArithmeticError):
        return None, None

    # Confidence based on HR range and duration (longer runs = more data)
    confidence = min((hr_range / 50.0) * min(duration_minutes / 30.0, 1.0), 1.0)

    return round(drift_pct, 2), round(confidence, 2)


def calculate_hr_variability(
    hr_avg: Optional[float],
    hr_max: Optional[float],
    hr_min: Optional[float],
    duration_seconds: Optional[float],
) -> tuple[Optional[float], Optional[float]]:
    """Estimate HR variability from session-level HR statistics.

    Since RawRunData does not provide per-beat RR intervals, this estimates
    an RMSSD-like variability using hr_range / duration_minutes as a proxy.
    This has lower confidence than true RMSSD which requires per-beat data.

    Args:
        hr_avg: Average heart rate in BPM.
        hr_max: Maximum heart rate in BPM.
        hr_min: Minimum heart rate in BPM.
        duration_seconds: Total run duration in seconds.

    Returns:
        Tuple of (variability_estimate, confidence_score).
        Returns (None, None) if HR data is insufficient.
    """
    if (
        hr_avg is None
        or hr_max is None
        or hr_min is None
        or duration_seconds is None
        or duration_seconds <= 0
    ):
        return None, None

    if isinstance(hr_avg, float) and math.isnan(hr_avg):
        return None, None
    if isinstance(hr_max, float) and math.isnan(hr_max):
        return None, None
    if isinstance(hr_min, float) and math.isnan(hr_min):
        return None, None
    if isinstance(duration_seconds, float) and math.isnan(duration_seconds):
        return None, None

    if hr_min < 0 or hr_max < 0 or hr_avg < 0:
        return None, None

    if hr_min > hr_max:
        return None, None

    hr_range = hr_max - hr_min
    if hr_range < ASTHMA_METRICS["hr_variability"]["min_hr_range_bpm"]:
        return None, None

    duration_minutes = duration_seconds / 60.0
    if duration_minutes <= 0:
        return None, None

    # hr_avg informs the baseline but the primary estimate uses range/duration
    variability_estimate = hr_range / duration_minutes

    # Confidence based on HR range, duration, and data quality via hr_avg
    confidence = min(
        (hr_range / 40.0) * min(duration_minutes / 30.0, 1.0) * (hr_avg / 150.0 if hr_avg and hr_avg > 0 else 1.0),
        0.8,
    )

    return round(variability_estimate, 2), round(confidence, 2)


def detect_hr_zone_anomaly(
    hr_zone_distribution: Optional[dict[str, int]],
    duration_seconds: Optional[float],
) -> tuple[Optional[bool], Optional[float]]:
    """Detect unexpected HR zone distribution (excessive Z4/Z5 time).

    Compares Z4+Z5 proportion against configurable threshold from config.py.
    A run with excessive time in high zones may indicate bronchospasm episodes.

    Args:
        hr_zone_distribution: Dictionary with zone seconds (z1-z5) as keys.
        duration_seconds: Total run duration in seconds.

    Returns:
        Tuple of (anomaly_flag, confidence_score).
        Returns (None, None) if HR zone data is unavailable.
    """
    if hr_zone_distribution is None or duration_seconds is None or duration_seconds <= 0:
        return None, None

    if isinstance(duration_seconds, float) and math.isnan(duration_seconds):
        return None, None

    # Validate exactly the expected keys to prevent extra keys from skewing proportions
    expected_zones = {"z1", "z2", "z3", "z4", "z5"}
    if set(hr_zone_distribution.keys()) != expected_zones:
        return None, None

    for zone in expected_zones:
        value = hr_zone_distribution.get(zone)
        if value is None or not isinstance(value, (int, float)):
            return None, None
        if value < 0:
            return None, None

    total_time = sum(hr_zone_distribution.values())
    if total_time <= 0:
        return None, None

    z4_time = hr_zone_distribution.get("z4", 0)
    z5_time = hr_zone_distribution.get("z5", 0)
    high_zone_proportion = (z4_time + z5_time) / total_time

    anomaly_flag = high_zone_proportion > HR_ZONE_ANOMALY_THRESHOLD

    # Confidence based on actual run duration
    confidence = min(duration_seconds / 1800.0, 1.0)

    return anomaly_flag, round(confidence, 2)


def detect_cadence_compensation(
    cadence_avg: Optional[float],
    cadence_max: Optional[float],
    pace_sec_per_km: Optional[float],
    duration_seconds: Optional[float],
) -> tuple[Optional[bool], Optional[float]]:
    """Detect cadence compensation patterns.

    Detects sudden cadence changes not explained by pace changes. A runner
    experiencing breathing difficulty may alter cadence as a compensation
    mechanism. Per FR46, detects cadence changes >20% not attributable to pace.

    With session-level aggregates, we use pace as a baseline to adjust the
    expected cadence variation threshold.

    Args:
        cadence_avg: Average cadence in RPM.
        cadence_max: Maximum cadence in RPM.
        pace_sec_per_km: Average pace in seconds per km.
        duration_seconds: Total run duration in seconds.

    Returns:
        Tuple of (compensation_flag, confidence_score).
        Returns (None, None) if cadence or pace data is unavailable.
    """
    if (
        cadence_avg is None
        or cadence_max is None
        or pace_sec_per_km is None
        or duration_seconds is None
        or duration_seconds <= 0
    ):
        return None, None

    if isinstance(cadence_avg, float) and math.isnan(cadence_avg):
        return None, None
    if isinstance(cadence_max, float) and math.isnan(cadence_max):
        return None, None
    if isinstance(pace_sec_per_km, float) and math.isnan(pace_sec_per_km):
        return None, None
    if isinstance(duration_seconds, float) and math.isnan(duration_seconds):
        return None, None

    if cadence_avg <= 0 or pace_sec_per_km <= 0:
        return None, None

    cadence_range_pct = (cadence_max - cadence_avg) / cadence_avg

    # Adjust threshold by pace: faster pace allows slightly more natural cadence variation
    pace_baseline = 300.0  # 5:00/km reference
    pace_factor = min(max(pace_baseline / pace_sec_per_km, 0.5), 2.0)
    adjusted_threshold = CADENCE_CHANGE_THRESHOLD_PCT * pace_factor

    compensation_detected = cadence_range_pct > adjusted_threshold

    confidence = min((cadence_max - cadence_avg) / 30.0, 1.0) if cadence_max > cadence_avg else 0.5

    return compensation_detected, round(confidence, 2)


def calculate_asthma_aware_metrics(
    raw_data: "RawRunData",
    standard_metrics: Optional[StandardMetrics] = None,
) -> AsthmaAwareMetrics:
    """Calculate asthma-aware metrics from raw .fit data.

    This function is DETERMINISTIC: same RawRunData input always produces
    identical AsthmaAwareMetrics output. NO LLM calls, NO randomness.

    Args:
        raw_data: RawRunData instance from fit_parser.parse_fit_file()
        standard_metrics: Optional StandardMetrics for zone anomaly detection.
            If None, zone anomaly detection returns None.

    Returns:
        AsthmaAwareMetrics Pydantic model with all calculated metrics.

    Raises:
        MetricCalculationError: If calculation fails due to invalid data.
    """
    if raw_data is None:
        raise MetricCalculationError("raw_data cannot be None")

    hr_pace_drift_pct, hr_pace_drift_confidence = calculate_hr_pace_drift(
        hr_avg=raw_data.hr_avg_bpm,
        hr_max=raw_data.hr_max_bpm,
        hr_min=raw_data.hr_min_bpm,
        pace_sec_per_km=raw_data.pace_sec_per_km,
        duration_seconds=raw_data.duration_seconds,
    )

    hr_variability_rmssd, hr_variability_confidence = calculate_hr_variability(
        hr_avg=raw_data.hr_avg_bpm,
        hr_max=raw_data.hr_max_bpm,
        hr_min=raw_data.hr_min_bpm,
        duration_seconds=raw_data.duration_seconds,
    )

    hr_zone_anomaly_flag = None
    hr_zone_anomaly_confidence = None
    if standard_metrics is not None and standard_metrics.hr_zone_distribution is not None:
        hr_zone_anomaly_flag, hr_zone_anomaly_confidence = detect_hr_zone_anomaly(
            hr_zone_distribution=standard_metrics.hr_zone_distribution,
            duration_seconds=raw_data.duration_seconds,
        )

    cadence_compensation_flag, cadence_compensation_confidence = detect_cadence_compensation(
        cadence_avg=raw_data.cadence_avg_rpm,
        cadence_max=raw_data.cadence_max_rpm,
        pace_sec_per_km=raw_data.pace_sec_per_km,
        duration_seconds=raw_data.duration_seconds,
    )

    confidences = [
        c
        for c in [
            hr_pace_drift_confidence,
            hr_variability_confidence,
            hr_zone_anomaly_confidence,
            cadence_compensation_confidence,
        ]
        if c is not None
    ]
    confidence_score = min(confidences) if confidences else None

    try:
        return AsthmaAwareMetrics(
            hr_pace_drift_pct=hr_pace_drift_pct,
            hr_pace_drift_confidence=hr_pace_drift_confidence,
            hr_variability_rmssd=hr_variability_rmssd,
            hr_variability_confidence=hr_variability_confidence,
            hr_zone_anomaly_flag=hr_zone_anomaly_flag,
            hr_zone_anomaly_confidence=hr_zone_anomaly_confidence,
            cadence_compensation_flag=cadence_compensation_flag,
            cadence_compensation_confidence=cadence_compensation_confidence,
            confidence_score=confidence_score,
        )
    except ValidationError as e:
        raise MetricCalculationError(
            f"Failed to calculate asthma-aware metrics: {e}"
        ) from e


__all__ = [
    "MetricCalculationError",
    "StandardMetrics",
    "AsthmaAwareMetrics",
    "calculate_standard_metrics",
    "calculate_asthma_aware_metrics",
    "calculate_max_hr",
    "calculate_hr_zone_distribution",
    "calculate_elevation_gain_loss",
    "calculate_hr_pace_drift",
    "calculate_hr_variability",
    "detect_hr_zone_anomaly",
    "detect_cadence_compensation",
]
