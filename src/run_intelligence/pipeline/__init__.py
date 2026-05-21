"""Pipeline module for FIT file processing and metric calculation."""

from run_intelligence.pipeline.fit_parser import (
    FitParseError,
    RawRunData,
    parse_fit_file,
)
from run_intelligence.pipeline.metrics import (
    AsthmaAwareMetrics,
    MetricCalculationError,
    StandardMetrics,
    calculate_asthma_aware_metrics,
    calculate_hr_pace_drift,
    calculate_hr_variability,
    calculate_standard_metrics,
    detect_cadence_compensation,
    detect_hr_zone_anomaly,
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
from run_intelligence.pipeline.runner import process_directory, process_file
from run_intelligence.pipeline.runner import BatchResult

__all__ = [
    "FitParseError",
    "RawRunData",
    "parse_fit_file",
    "MetricCalculationError",
    "StandardMetrics",
    "AsthmaAwareMetrics",
    "calculate_standard_metrics",
    "calculate_asthma_aware_metrics",
    "calculate_hr_pace_drift",
    "calculate_hr_variability",
    "detect_hr_zone_anomaly",
    "detect_cadence_compensation",
    "DataQualityFlags",
    "RunData",
    "validate_and_flag",
    "detect_hr_artifacts",
    "detect_gps_drift",
    "detect_cadence_inconsistencies",
    "calculate_confidence_score",
    "process_file",
    "process_directory",
    "BatchResult",
]
