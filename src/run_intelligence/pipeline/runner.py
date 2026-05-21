"""Pipeline orchestration module for FIT file processing.

This module is DETERMINISTIC: same input always produces identical RunData.
NO LLM calls, NO randomness. Side effects are DB persistence (when dry_run=False)
and unconditional stdout/stderr output for summaries and warnings.
"""

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from run_intelligence.db.repository import AuditLogRepository, RunRepository
from run_intelligence.db.session import create_session, _get_engine
from run_intelligence.pipeline.fit_parser import FitParseError
from run_intelligence.pipeline.metrics import MetricCalculationError
from run_intelligence.pipeline.validation import RunData, validate_and_flag


def process_file(
    file_path: str,
    verbose: bool = False,
    dry_run: bool = False,
) -> RunData:
    """Process a .fit file through the complete pipeline.

    Orchestrates: parse → derive metrics → validate → persist to DB (if not dry_run).

    This function is DETERMINISTIC in computation: same input always produces
    identical RunData. The only side effect is DB persistence when dry_run=False.

    Args:
        file_path: Path to .fit file
        verbose: If True, print detailed processing output to stdout
        dry_run: If True, process but do not write to database

    Returns:
        RunData Pydantic model with all metrics and quality flags

    Raises:
        FitParseError: If file cannot be parsed
        MetricCalculationError: If metric calculation fails
    """
    start_time = time.time()

    run_data = validate_and_flag(file_path, verbose=verbose)

    if not dry_run:
        try:
            _persist_run(run_data, file_path)
            if verbose:
                print("[RUNNER] Database persistence successful")
        except Exception as e:
            sys.stderr.write(f"[PIPELINE_ERROR] runner: Failed to persist to database: {e}\n")
            raise MetricCalculationError(f"Database persistence failed: {e}") from e
    else:
        if verbose:
            print("[RUNNER] Dry-run: skipping database persistence")

    summary = _format_summary(run_data, file_path, dry_run)
    sys.stdout.write(summary)
    sys.stdout.write("\n")

    warnings = _format_warnings(run_data)
    if warnings:
        sys.stderr.write(warnings)
        sys.stderr.write("\n")

    if verbose:
        verbose_output = _format_verbose_output(run_data, file_path)
        sys.stdout.write(verbose_output)
        sys.stdout.write("\n")

    elapsed = time.time() - start_time

    if verbose:
        print(f"[RUNNER] Total processing time: {elapsed:.3f}s (NFR1: ≤5s)")
        nfr1_pass = elapsed <= 5.0
        print(f"[RUNNER] NFR1 compliance: {'PASS' if nfr1_pass else 'FAIL'}")

    return run_data


def _persist_run(run_data: RunData, file_path: str):
    """Persist RunData to database.

    Args:
        run_data: Validated RunData from pipeline
        file_path: Original .fit file path

    Returns:
        Created Run database record

    Raises:
        Exception: If database persistence fails
    """
    session = create_session()
    try:
        engine = _get_engine()
        audit_logger = AuditLogRepository(session, engine=engine)
        repo = RunRepository(session, audit_logger)

        raw_metrics_json = run_data.raw_data.model_dump_json(by_alias=False)

        derived = {}
        if run_data.standard_metrics:
            derived["standard_metrics"] = json.loads(
                run_data.standard_metrics.model_dump_json(by_alias=False)
            )
        if run_data.asthma_aware_metrics:
            derived["asthma_aware_metrics"] = json.loads(
                run_data.asthma_aware_metrics.model_dump_json(by_alias=False)
            )
        derived_metrics_json = json.dumps(derived)

        data_quality_flags_json = run_data.data_quality_flags.model_dump_json(by_alias=False)

        run = repo.create_run(
            file_path=file_path,
            raw_metrics_json=raw_metrics_json,
            derived_metrics_json=derived_metrics_json,
            data_quality_flags_json=data_quality_flags_json,
        )
        return run
    except Exception:
        try:
            session.rollback()
        except Exception:
            pass
        raise
    finally:
        session.close()


def _format_summary(run_data: RunData, file_path: str, dry_run: bool = False) -> str:
    """Format summary output for stdout.

    Args:
        run_data: Validated RunData from pipeline
        file_path: Original .fit file path
        dry_run: Whether this is a dry-run

    Returns:
        Summary string for stdout
    """
    lines = []

    if dry_run:
        lines.append(f"[DRY-RUN] Processed: {file_path}")
    else:
        lines.append(f"File processed: {file_path}")

    if run_data.standard_metrics:
        sm = run_data.standard_metrics
        lines.append("Metrics extracted:")
        if run_data.raw_data.distance_meters is not None:
            dist_km = run_data.raw_data.distance_meters / 1000.0
            lines.append(f"  - Distance: {dist_km:.2f} km")
        if run_data.raw_data.duration_seconds is not None:
            lines.append(f"  - Duration: {run_data.raw_data.duration_seconds:.0f}s")
        if sm.pace_avg_min_per_km is not None:
            lines.append(f"  - Avg pace: {sm.pace_avg_min_per_km:.2f} min/km")
        if sm.elevation_gain_m is not None:
            lines.append(f"  - Elevation gain: {sm.elevation_gain_m:.0f}m")

    flags = run_data.data_quality_flags
    flag_count = (
        len(flags.hr_artifacts)
        + len(flags.gps_drift_segments)
        + len(flags.cadence_inconsistencies)
    )

    if flag_count > 0 or flags.low_confidence_flag:
        lines.append(f"Flags raised: {flag_count}")
        if flags.hr_artifacts:
            lines.append(f"  - HR artifacts: {len(flags.hr_artifacts)}")
        if flags.gps_drift_segments:
            lines.append(f"  - GPS drift segments: {len(flags.gps_drift_segments)}")
        if flags.cadence_inconsistencies:
            lines.append(f"  - Cadence inconsistencies: {len(flags.cadence_inconsistencies)}")
        if flags.low_confidence_flag:
            lines.append("  - Low confidence flag: True")
    else:
        lines.append("Data quality: clean")

    return "\n".join(lines)


def _format_verbose_output(run_data: RunData, file_path: str) -> str:
    """Format detailed stage-by-stage output for verbose mode.

    Args:
        run_data: Validated RunData from pipeline
        file_path: Original .fit file path

    Returns:
        Detailed output string for stdout
    """
    lines = []

    lines.append(f"[VERBOSE] File: {file_path}")
    lines.append("[VERBOSE] Pipeline stages:")

    lines.append("  1. Parse: FIT file → RawRunData")
    raw = run_data.raw_data
    if raw.timestamp:
        lines.append(f"     - Timestamp: {raw.timestamp}")
    if raw.hr_avg_bpm is not None:
        lines.append(f"     - HR avg: {raw.hr_avg_bpm} bpm")
    if raw.hr_max_bpm is not None:
        lines.append(f"     - HR max: {raw.hr_max_bpm} bpm")

    lines.append("  2. Standard metrics: RawRunData → StandardMetrics")
    if run_data.standard_metrics:
        sm = run_data.standard_metrics
        if raw.distance_meters is not None:
            lines.append(f"     - Distance: {raw.distance_meters / 1000.0:.2f} km")
        else:
            lines.append("     - Distance: N/A")
        if raw.duration_seconds is not None:
            lines.append(f"     - Duration: {raw.duration_seconds:.0f}s")
        else:
            lines.append("     - Duration: N/A")
        if sm.pace_avg_min_per_km is not None:
            lines.append(f"     - Pace: {sm.pace_avg_min_per_km:.2f} min/km")
        else:
            lines.append("     - Pace: N/A")

    lines.append("  3. Asthma-aware metrics: StandardMetrics → AsthmaAwareMetrics")
    if run_data.asthma_aware_metrics:
        aam = run_data.asthma_aware_metrics
        if aam.hr_pace_drift_pct is not None:
            lines.append(f"     - HR/Pace drift: {aam.hr_pace_drift_pct:.1f}%")
        else:
            lines.append("     - HR/Pace drift: N/A")
        if aam.confidence_score is not None:
            lines.append(f"     - Confidence: {aam.confidence_score:.2f}")
        else:
            lines.append("     - Confidence: N/A")
        if aam.hr_zone_anomaly_flag is not None:
            lines.append(f"     - HR zone anomaly: {aam.hr_zone_anomaly_flag}")
        if aam.cadence_compensation_flag is not None:
            lines.append(f"     - Cadence compensation: {aam.cadence_compensation_flag}")

    lines.append("  4. Validation: quality flags → DataQualityFlags")
    flags = run_data.data_quality_flags
    lines.append(f"     - Confidence score: {flags.confidence_score:.2f}")
    lines.append(f"     - Low confidence flag: {flags.low_confidence_flag}")
    lines.append(f"     - HR artifacts: {len(flags.hr_artifacts)}")
    lines.append(f"     - GPS drift segments: {len(flags.gps_drift_segments)}")
    lines.append(f"     - Cadence inconsistencies: {len(flags.cadence_inconsistencies)}")

    lines.append("[VERBOSE] Validation complete")

    return "\n".join(lines)


def _format_warnings(run_data: RunData) -> str:
    """Format validation warnings for stderr.

    Args:
        run_data: Validated RunData from pipeline

    Returns:
        Warnings string for stderr, empty string if no warnings
    """
    warnings = []
    flags = run_data.data_quality_flags

    for artifact in flags.hr_artifacts:
        warnings.append(
            f"[VALIDATION_WARNING] HR artifact: index={artifact.get('index', 'N/A')}, "
            f"value={artifact.get('value_bpm', 'N/A')} bpm, type={artifact.get('type', 'N/A')}"
        )

    for segment in flags.gps_drift_segments:
        warnings.append(
            f"[VALIDATION_WARNING] GPS drift: start={segment.get('start_index', 'N/A')}, "
            f"end={segment.get('end_index', 'N/A')}, "
            f"distance={segment.get('distance_meters', 0):.1f}m, "
            f"duration={segment.get('duration_seconds', 0):.1f}s"
        )

    for inconsistency in flags.cadence_inconsistencies:
        warnings.append(
            f"[VALIDATION_WARNING] Cadence inconsistency: "
            f"change={inconsistency.get('change_pct', 0):.1f}%, "
            f"pace_explained={inconsistency.get('is_pace_explained', 'N/A')}"
        )

    return "\n".join(warnings)


@dataclass
class BatchResult:
    """Aggregate result from batch processing a directory of .fit files."""

    total_files: int
    success_count: int
    failure_count: int
    failed_files: list[str]
    total_elapsed_seconds: float
    dry_run: bool


def process_directory(
    directory_path: str,
    verbose: bool = False,
    dry_run: bool = False,
) -> BatchResult:
    """Process all .fit files in a directory independently.

    One corrupt file does not stop the batch. Each file is processed
    by calling process_file().

    Args:
        directory_path: Path to directory containing .fit files
        verbose: If True, print detailed per-file output
        dry_run: If True, process without writing to database

    Returns:
        BatchResult with aggregate statistics

    Raises:
        ValueError: If directory_path does not exist or is not a directory
    """
    path = Path(directory_path)
    if not path.exists():
        raise ValueError(f"Directory does not exist: {directory_path}")
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {directory_path}")

    fit_files = sorted(
        list(path.glob("*.fit")) + list(path.glob("*.FIT"))
    )

    total_files = len(fit_files)
    success_count = 0
    failure_count = 0
    failed_files: list[str] = []

    start_time = time.perf_counter()

    for fit_file in fit_files:
        try:
            process_file(str(fit_file), verbose=verbose, dry_run=dry_run)
            success_count += 1
        except (FitParseError, MetricCalculationError) as e:
            failure_count += 1
            failed_files.append(str(fit_file))
            sys.stderr.write(_format_batch_error(fit_file.name, e))
        except Exception as e:
            failure_count += 1
            failed_files.append(str(fit_file))
            sys.stderr.write(
                f"[BATCH_ERROR] {fit_file.name}: Unexpected error: {e}\n"
            )

    elapsed = time.perf_counter() - start_time

    return BatchResult(
        total_files=total_files,
        success_count=success_count,
        failure_count=failure_count,
        failed_files=failed_files,
        total_elapsed_seconds=elapsed,
        dry_run=dry_run,
    )


def _format_batch_summary(result: BatchResult) -> str:
    """Format batch result summary for stdout.

    Args:
        result: BatchResult from process_directory()

    Returns:
        Formatted summary string for stdout
    """
    lines = [
        "Batch Processing Summary",
        "========================",
        f"Total files: {result.total_files}",
        f"Successful: {result.success_count}",
        f"Failed: {result.failure_count}",
    ]
    if result.failed_files:
        failed_names = ", ".join(Path(f).name for f in result.failed_files)
        lines.append(f"Failed files: {failed_names}")
    lines.append(f"Total time: {result.total_elapsed_seconds:.1f}s")
    if result.dry_run:
        lines.append("[DRY RUN] No data was written to the database.")
    return "\n".join(lines) + "\n"


def _format_batch_error(file_name: str, error: Exception) -> str:
    """Format a per-file batch error for stderr.

    Args:
        file_name: Name of the file that failed
        error: Exception that was raised

    Returns:
        Formatted error string with [BATCH_ERROR] prefix
    """
    return f"[BATCH_ERROR] {file_name}: {type(error).__name__}: {error}\n"