"""Data validation and quality flagging module for pipeline output.

This module is DETERMINISTIC: same input always produces identical output.
NO LLM calls, NO randomness.
"""

import math
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    field_validator,
    model_validator,
)

from run_intelligence.config import (
    CADENCE_CHANGE_THRESHOLD_PCT,
    CADENCE_PACE_BASELINE_SPK,
    CADENCE_PACE_FACTOR_MAX,
    CADENCE_PACE_FACTOR_MIN,
    CADENCE_PACE_MARGIN,
    CONFIDENCE_DEDUCTION_CADENCE_INCONSISTENCY,
    CONFIDENCE_DEDUCTION_GPS_DRIFT,
    CONFIDENCE_DEDUCTION_SPIKE,
    CONFIDENCE_DEDUCTION_THRESHOLD_EXCEEDED,
    GPS_DRIFT_PACE_FACTOR,
    HR_LIMITS,
    HR_SPIKE_THRESHOLD_BPM,
    LOW_CONFIDENCE_THRESHOLD,
)
from run_intelligence.pipeline.metrics import (
    AsthmaAwareMetrics,
    MetricCalculationError,
    StandardMetrics,
    calculate_asthma_aware_metrics,
    calculate_standard_metrics,
)

if TYPE_CHECKING:
    from run_intelligence.pipeline.fit_parser import RawRunData


class DataQualityFlags(BaseModel):
    """Validated model for data quality flags detected during pipeline processing."""

    model_config = ConfigDict(by_alias=False, extra="forbid")

    hr_artifacts: list[dict] = []
    gps_drift_segments: list[dict] = []
    cadence_inconsistencies: list[dict] = []
    low_confidence_flag: bool = False
    confidence_score: float = 1.0

    @field_validator("confidence_score", mode="before")
    @classmethod
    def validate_confidence_score(cls, v: float) -> float:
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            raise ValueError(f"confidence_score must be a finite number, got {v}")
        if v < 0 or v > 1:
            raise ValueError(f"confidence_score must be between 0 and 1, got {v}")
        return v

    @field_validator("hr_artifacts", mode="before")
    @classmethod
    def validate_hr_artifacts(cls, v: list[dict]) -> list[dict]:
        for item in v:
            if not isinstance(item, dict):
                raise ValueError(f"Each hr_artifact must be a dict, got {type(item)}")
            if "index" not in item or not isinstance(item["index"], int):
                raise ValueError("hr_artifact must contain 'index' as int")
            if "value_bpm" not in item or not isinstance(
                item["value_bpm"], (int, float)
            ):
                raise ValueError("hr_artifact must contain 'value_bpm' as numeric")
            if isinstance(item["value_bpm"], float) and (
                math.isnan(item["value_bpm"]) or math.isinf(item["value_bpm"])
            ):
                raise ValueError(
                    f"hr_artifact value_bpm must be finite, got {item['value_bpm']}"
                )
            if "type" not in item or item["type"] not in {
                "threshold_exceeded",
                "spike",
            }:
                raise ValueError(
                    "hr_artifact must contain 'type' as 'threshold_exceeded' or 'spike'"
                )
        return v

    @field_validator("gps_drift_segments", mode="before")
    @classmethod
    def validate_gps_drift_segments(cls, v: list[dict]) -> list[dict]:
        for item in v:
            if not isinstance(item, dict):
                raise ValueError(
                    f"Each gps_drift_segment must be a dict, got {type(item)}"
                )
            for key in ("start_index", "end_index"):
                if key not in item or not isinstance(item[key], int):
                    raise ValueError(f"gps_drift_segment must contain '{key}' as int")
            for key in ("distance_meters", "duration_seconds", "expected_pace"):
                if key not in item or not isinstance(item[key], (int, float)):
                    raise ValueError(
                        f"gps_drift_segment must contain '{key}' as numeric"
                    )
                if isinstance(item[key], float) and (
                    math.isnan(item[key]) or math.isinf(item[key])
                ):
                    raise ValueError(f"gps_drift_segment {key} must be finite")
        return v

    @field_validator("cadence_inconsistencies", mode="before")
    @classmethod
    def validate_cadence_inconsistencies(cls, v: list[dict]) -> list[dict]:
        for item in v:
            if not isinstance(item, dict):
                raise ValueError(
                    f"Each cadence_inconsistency must be a dict, got {type(item)}"
                )
            for key in ("start_index", "end_index"):
                if key not in item or not isinstance(item[key], int):
                    raise ValueError(
                        f"cadence_inconsistency must contain '{key}' as int"
                    )
            for key in ("change_pct", "pace_change_pct"):
                if key not in item or not isinstance(item[key], (int, float)):
                    raise ValueError(
                        f"cadence_inconsistency must contain '{key}' as numeric"
                    )
                if isinstance(item[key], float) and (
                    math.isnan(item[key]) or math.isinf(item[key])
                ):
                    raise ValueError(f"cadence_inconsistency {key} must be finite")
            if "is_pace_explained" not in item or not isinstance(
                item["is_pace_explained"], bool
            ):
                raise ValueError(
                    "cadence_inconsistency must contain 'is_pace_explained' as bool"
                )
        return v

    @model_validator(mode="after")
    def validate_confidence_consistency(self) -> "DataQualityFlags":
        if (
            self.confidence_score < LOW_CONFIDENCE_THRESHOLD
            and not self.low_confidence_flag
        ):
            raise ValueError(
                f"low_confidence_flag must be True when confidence_score ({self.confidence_score}) < {LOW_CONFIDENCE_THRESHOLD}"
            )
        if (
            self.confidence_score >= LOW_CONFIDENCE_THRESHOLD
            and self.low_confidence_flag
        ):
            raise ValueError(
                f"low_confidence_flag must be False when confidence_score ({self.confidence_score}) >= {LOW_CONFIDENCE_THRESHOLD}"
            )
        return self

    def to_json(self) -> str:
        """Serialize to JSON for database storage using snake_case."""
        return self.model_dump_json(by_alias=False)

    @classmethod
    def from_json(cls, json_str: str) -> "DataQualityFlags":
        """Deserialize from JSON string."""
        return cls.model_validate_json(json_str)


class RunData(BaseModel):
    """Central validated model combining all pipeline outputs.

    This is the primary output of the entire pipeline, combining raw data,
    standard metrics, asthma-aware metrics, and quality flags.
    """

    model_config = ConfigDict(by_alias=False, extra="forbid")

    raw_data: "RawRunData"
    standard_metrics: Optional[StandardMetrics] = None
    asthma_aware_metrics: Optional[AsthmaAwareMetrics] = None
    data_quality_flags: DataQualityFlags
    confidence_score: float = 1.0
    low_confidence_flag: bool = False

    @field_validator("confidence_score", mode="before")
    @classmethod
    def validate_confidence_score(cls, v: float) -> float:
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            raise ValueError(f"confidence_score must be a finite number, got {v}")
        if v < 0 or v > 1:
            raise ValueError(f"confidence_score must be between 0 and 1, got {v}")
        return v

    @model_validator(mode="after")
    def validate_confidence_consistency(self) -> "RunData":
        if (
            self.confidence_score < LOW_CONFIDENCE_THRESHOLD
            and not self.low_confidence_flag
        ):
            raise ValueError(
                f"low_confidence_flag must be True when confidence_score ({self.confidence_score}) < {LOW_CONFIDENCE_THRESHOLD}"
            )
        if (
            self.confidence_score >= LOW_CONFIDENCE_THRESHOLD
            and self.low_confidence_flag
        ):
            raise ValueError(
                f"low_confidence_flag must be False when confidence_score ({self.confidence_score}) >= {LOW_CONFIDENCE_THRESHOLD}"
            )
        return self

    def to_json(self) -> str:
        """Serialize to JSON for database storage using snake_case."""
        return self.model_dump_json(by_alias=False)

    @classmethod
    def from_json(cls, json_str: str) -> "RunData":
        """Deserialize from JSON string."""
        return cls.model_validate_json(json_str)


# Forward reference resolution for Pydantic
from run_intelligence.pipeline.fit_parser import RawRunData  # noqa: E402

RunData.model_rebuild()


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in meters.

    Uses the haversine formula for spherical Earth approximation.
    """
    import math

    R = 6_371_000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def detect_hr_artifacts(raw_data: "RawRunData") -> list[dict]:
    """Detect HR artifacts in raw data.

    With session-level aggregates (no per-record HR time series), detection
    uses hr_max_bpm and hr_avg_bpm as proxies:
    - threshold_exceeded: hr_max_bpm > artifact_threshold_bpm
    - spike: hr_max_bpm significantly exceeds hr_avg_bpm (> HR_SPIKE_THRESHOLD_BPM)

    Args:
        raw_data: RawRunData instance from fit_parser.parse_fit_file()

    Returns:
        List of artifact records.
    """
    artifacts: list[dict] = []

    if raw_data is None:
        raise MetricCalculationError("raw_data cannot be None")

    hr_max = raw_data.hr_max_bpm
    hr_avg = raw_data.hr_avg_bpm
    timestamp = raw_data.timestamp
    ts_str = timestamp.isoformat() if isinstance(timestamp, datetime) else None

    artifact_threshold = HR_LIMITS.get("artifact_threshold_bpm", 220)

    if hr_max is not None and not (isinstance(hr_max, float) and math.isnan(hr_max)):
        if hr_max > artifact_threshold:
            artifacts.append(
                {
                    "index": 0,
                    "value_bpm": float(hr_max),
                    "type": "threshold_exceeded",
                    "timestamp": ts_str,
                }
            )

    if (
        hr_max is not None
        and hr_max < artifact_threshold
        and hr_avg is not None
        and not (isinstance(hr_max, float) and math.isnan(hr_max))
        and not (isinstance(hr_avg, float) and math.isnan(hr_avg))
    ):
        if hr_max - hr_avg > HR_SPIKE_THRESHOLD_BPM:
            artifacts.append(
                {
                    "index": 0,
                    "value_bpm": float(hr_max),
                    "type": "spike",
                    "timestamp": ts_str,
                }
            )

    return artifacts


def detect_gps_drift(raw_data: "RawRunData") -> list[dict]:
    """Detect GPS drift anomalies.

    Compares consecutive GPS points to detect position jumps inconsistent
    with expected running pace.

    Args:
        raw_data: RawRunData instance from fit_parser.parse_fit_file()

    Returns:
        List of drift segment records.
    """
    segments: list[dict] = []

    if raw_data is None:
        raise MetricCalculationError("raw_data cannot be None")

    gps_lat = raw_data.gps_lat
    gps_lon = raw_data.gps_lon
    duration_seconds = raw_data.duration_seconds
    pace_sec_per_km = raw_data.pace_sec_per_km

    if gps_lat is None or gps_lon is None or len(gps_lat) < 2 or len(gps_lon) < 2:
        return segments

    n_points = min(len(gps_lat), len(gps_lon))
    if duration_seconds is None or duration_seconds <= 0:
        return segments

    drift_threshold_mps = HR_LIMITS.get("gps_drift_mps", 50.0)
    expected_pace_mps = None
    if pace_sec_per_km is not None and pace_sec_per_km > 0:
        expected_pace_mps = 1000.0 / pace_sec_per_km

    interval_seconds = duration_seconds / max(n_points - 1, 1)

    in_drift = False
    drift_start = 0
    drift_distance = 0.0
    drift_duration = 0.0

    def _close_segment(start: int, end: int, dist: float, dur: float) -> dict:
        return {
            "start_index": start,
            "end_index": end,
            "distance_meters": round(dist, 2),
            "duration_seconds": round(dur, 2),
            "expected_pace": round(expected_pace_mps, 2) if expected_pace_mps else 0.0,
        }

    for i in range(1, n_points):
        lat1, lon1 = gps_lat[i - 1], gps_lon[i - 1]
        lat2, lon2 = gps_lat[i], gps_lon[i]

        if any(
            coord is None or (isinstance(coord, float) and math.isnan(coord))
            for coord in (lat1, lon1, lat2, lon2)
        ):
            if in_drift:
                segments.append(
                    _close_segment(drift_start, i - 1, drift_distance, drift_duration)
                )
                in_drift = False
                drift_distance = 0.0
                drift_duration = 0.0
            continue

        distance = _haversine_distance(lat1, lon1, lat2, lon2)
        speed = distance / interval_seconds if interval_seconds > 0 else 0.0

        is_drift = speed > drift_threshold_mps
        if is_drift and expected_pace_mps is not None:
            if speed <= expected_pace_mps * GPS_DRIFT_PACE_FACTOR:
                is_drift = False

        if is_drift:
            if not in_drift:
                in_drift = True
                drift_start = i - 1
            drift_distance += distance
            drift_duration += interval_seconds
        else:
            if in_drift:
                segments.append(
                    _close_segment(drift_start, i - 1, drift_distance, drift_duration)
                )
                in_drift = False
                drift_distance = 0.0
                drift_duration = 0.0

    if in_drift:
        segments.append(
            _close_segment(drift_start, n_points - 1, drift_distance, drift_duration)
        )

    return segments


def detect_cadence_inconsistencies(raw_data: "RawRunData") -> list[dict]:
    """Detect cadence inconsistencies >20% not explained by pace.

    With session-level aggregates (no per-record cadence time series),
    detection uses cadence_avg_rpm and cadence_max_rpm. A large range
    between max and avg may indicate inconsistency.

    Args:
        raw_data: RawRunData instance from fit_parser.parse_fit_file()

    Returns:
        List of inconsistency records.
    """
    inconsistencies: list[dict] = []

    if raw_data is None:
        raise MetricCalculationError("raw_data cannot be None")

    cadence_avg = raw_data.cadence_avg_rpm
    cadence_max = raw_data.cadence_max_rpm
    pace_sec_per_km = raw_data.pace_sec_per_km

    if cadence_avg is None or cadence_max is None:
        return inconsistencies

    if isinstance(cadence_avg, float) and math.isnan(cadence_avg):
        return inconsistencies
    if isinstance(cadence_max, float) and math.isnan(cadence_max):
        return inconsistencies

    if cadence_avg <= 0:
        return inconsistencies

    change_pct = (cadence_max - cadence_avg) / cadence_avg * 100.0
    threshold_pct = CADENCE_CHANGE_THRESHOLD_PCT * 100.0

    if change_pct > threshold_pct:
        pace_factor = 1.0
        if pace_sec_per_km is not None and pace_sec_per_km > 0:
            pace_factor = min(
                max(
                    CADENCE_PACE_BASELINE_SPK / pace_sec_per_km, CADENCE_PACE_FACTOR_MIN
                ),
                CADENCE_PACE_FACTOR_MAX,
            )

        adjusted_threshold = threshold_pct * pace_factor
        is_pace_explained = change_pct <= adjusted_threshold * CADENCE_PACE_MARGIN

        inconsistencies.append(
            {
                "start_index": 0,
                "end_index": 0,
                "change_pct": round(change_pct, 2),
                "pace_change_pct": 0.0,
                "is_pace_explained": is_pace_explained,
            }
        )

    return inconsistencies


def calculate_confidence_score(
    asthma_aware_confidence: Optional[float],
    hr_artifacts: list[dict],
    gps_drift_segments: list[dict],
    cadence_inconsistencies: list[dict],
) -> tuple[float, bool]:
    """Calculate overall confidence score and low_confidence_flag.

    Starts with the asthma-aware confidence score (if available) and deducts
    for each detected data quality issue.

    Args:
        asthma_aware_confidence: Confidence score from AsthmaAwareMetrics.
        hr_artifacts: List of detected HR artifacts.
        gps_drift_segments: List of detected GPS drift segments.
        cadence_inconsistencies: List of detected cadence inconsistencies.

    Returns:
        Tuple of (confidence_score, low_confidence_flag).
    """
    confidence = asthma_aware_confidence if asthma_aware_confidence is not None else 1.0

    if isinstance(confidence, float) and (
        math.isnan(confidence) or math.isinf(confidence)
    ):
        confidence = 1.0

    # Deduct for HR artifacts
    for artifact in hr_artifacts:
        if artifact.get("type") == "threshold_exceeded":
            confidence -= CONFIDENCE_DEDUCTION_THRESHOLD_EXCEEDED
        elif artifact.get("type") == "spike":
            confidence -= CONFIDENCE_DEDUCTION_SPIKE

    # Deduct for GPS drift segments
    confidence -= len(gps_drift_segments) * CONFIDENCE_DEDUCTION_GPS_DRIFT

    # Deduct for cadence inconsistencies that are NOT pace-explained
    for inconsistency in cadence_inconsistencies:
        if not inconsistency.get("is_pace_explained", False):
            confidence -= CONFIDENCE_DEDUCTION_CADENCE_INCONSISTENCY

    confidence = max(0.0, min(1.0, round(confidence, 2)))
    low_confidence = confidence < LOW_CONFIDENCE_THRESHOLD

    return confidence, low_confidence


def validate_and_flag(
    fit_file_path: str,
    verbose: bool = False,
) -> RunData:
    """Validate .fit file and produce RunData with quality flags.

    This function is DETERMINISTIC: same input always produces
    identical RunData output. NO LLM calls, NO randomness.

    Orchestrates the full pipeline: parse → derive standard metrics →
    derive asthma-aware metrics → detect quality issues → assemble RunData.

    Args:
        fit_file_path: Path to .fit file
        verbose: If True, print detailed processing output

    Returns:
        RunData Pydantic model with all metrics and quality flags

    Raises:
        FitParseError: If file cannot be parsed
        MetricCalculationError: If metric calculation fails
    """
    from run_intelligence.pipeline.fit_parser import FitParseError, parse_fit_file

    if verbose:
        print(f"[PIPELINE] Parsing {fit_file_path}")

    try:
        raw_data = parse_fit_file(fit_file_path)
    except Exception as e:
        if isinstance(e, FitParseError):
            raise
        raise MetricCalculationError(f"Failed to parse FIT file: {e}") from e

    if verbose:
        print("[PIPELINE] Calculating standard metrics")

    try:
        standard_metrics = calculate_standard_metrics(raw_data)
    except MetricCalculationError:
        raise
    except Exception as e:
        raise MetricCalculationError(
            f"Failed to calculate standard metrics: {e}"
        ) from e

    if verbose:
        print("[PIPELINE] Calculating asthma-aware metrics")

    try:
        asthma_aware_metrics = calculate_asthma_aware_metrics(
            raw_data, standard_metrics=standard_metrics
        )
    except MetricCalculationError:
        raise
    except Exception as e:
        raise MetricCalculationError(
            f"Failed to calculate asthma-aware metrics: {e}"
        ) from e

    if verbose:
        print("[PIPELINE] Detecting data quality issues")

    hr_artifacts = detect_hr_artifacts(raw_data)
    gps_drift_segments = detect_gps_drift(raw_data)
    cadence_inconsistencies = detect_cadence_inconsistencies(raw_data)

    asthma_confidence = (
        asthma_aware_metrics.confidence_score
        if asthma_aware_metrics and asthma_aware_metrics.confidence_score is not None
        else None
    )

    confidence_score, low_confidence_flag = calculate_confidence_score(
        asthma_aware_confidence=asthma_confidence,
        hr_artifacts=hr_artifacts,
        gps_drift_segments=gps_drift_segments,
        cadence_inconsistencies=cadence_inconsistencies,
    )

    data_quality_flags = DataQualityFlags(
        hr_artifacts=hr_artifacts,
        gps_drift_segments=gps_drift_segments,
        cadence_inconsistencies=cadence_inconsistencies,
        low_confidence_flag=low_confidence_flag,
        confidence_score=confidence_score,
    )

    if verbose:
        print(f"[PIPELINE] Confidence score: {confidence_score}")
        print(f"[PIPELINE] Low confidence: {low_confidence_flag}")

    try:
        return RunData(
            raw_data=raw_data,
            standard_metrics=standard_metrics,
            asthma_aware_metrics=asthma_aware_metrics,
            data_quality_flags=data_quality_flags,
            confidence_score=confidence_score,
            low_confidence_flag=low_confidence_flag,
        )
    except ValidationError as e:
        raise MetricCalculationError(f"Failed to construct RunData: {e}") from e
