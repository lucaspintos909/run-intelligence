"""Tests for pipeline orchestration module (runner.py)."""

import time
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import MagicMock, patch

import typer

import pytest

from run_intelligence.pipeline.fit_parser import FitParseError, RawRunData
from run_intelligence.pipeline.metrics import (
    AsthmaAwareMetrics,
    MetricCalculationError,
    StandardMetrics,
)
from run_intelligence.pipeline.runner import (
    BatchResult,
    _format_batch_error,
    _format_batch_summary,
    _format_summary,
    _format_verbose_output,
    _format_warnings,
    _persist_run,
    process_directory,
    process_file,
)
from run_intelligence.pipeline.validation import DataQualityFlags, RunData


def _create_mock_run_data(**kwargs) -> RunData:
    """Helper to create mock RunData for testing."""
    defaults = {
        "raw_data": RawRunData(
            timestamp=datetime(2026, 5, 18, 10, 0, 0, tzinfo=timezone.utc),
            duration_seconds=3600.0,
            distance_meters=10000.0,
        ),
        "standard_metrics": StandardMetrics(
            pace_avg_min_per_km=6.0,
        ),
        "asthma_aware_metrics": AsthmaAwareMetrics(
            hr_pace_drift_pct=5.0,
            confidence_score=0.85,
        ),
        "data_quality_flags": DataQualityFlags(confidence_score=0.85),
    }
    defaults.update(kwargs)
    return RunData(**defaults)


class TestFormatSummary:
    """Test _format_summary function."""

    def test_basic_summary(self):
        run_data = _create_mock_run_data()
        summary = _format_summary(run_data, "/path/to/test.fit")
        assert "File processed: /path/to/test.fit" in summary
        assert "Metrics extracted:" in summary
        assert "Distance: 10.00 km" in summary

    def test_dry_run_summary(self):
        run_data = _create_mock_run_data()
        summary = _format_summary(run_data, "/path/to/test.fit", dry_run=True)
        assert "[DRY-RUN] Processed: /path/to/test.fit" in summary

    def test_summary_with_no_flags(self):
        run_data = _create_mock_run_data(
            data_quality_flags=DataQualityFlags(
                hr_artifacts=[],
                gps_drift_segments=[],
                cadence_inconsistencies=[],
                confidence_score=1.0,
                low_confidence_flag=False,
            )
        )
        summary = _format_summary(run_data, "/path/to/test.fit")
        assert "Data quality: clean" in summary

    def test_summary_with_flags(self):
        run_data = _create_mock_run_data(
            data_quality_flags=DataQualityFlags(
                hr_artifacts=[{"index": 0, "value_bpm": 225.0, "type": "threshold_exceeded"}],
                gps_drift_segments=[],
                cadence_inconsistencies=[],
                confidence_score=0.85,
                low_confidence_flag=False,
            )
        )
        summary = _format_summary(run_data, "/path/to/test.fit")
        assert "Flags raised: 1" in summary
        assert "HR artifacts: 1" in summary

    def test_summary_with_low_confidence_flag(self):
        run_data = _create_mock_run_data(
            data_quality_flags=DataQualityFlags(
                hr_artifacts=[],
                gps_drift_segments=[],
                cadence_inconsistencies=[],
                confidence_score=0.3,
                low_confidence_flag=True,
            )
        )
        summary = _format_summary(run_data, "/path/to/test.fit")
        assert "Low confidence flag: True" in summary


class TestFormatWarnings:
    """Test _format_warnings function."""

    def test_no_warnings_empty_string(self):
        run_data = _create_mock_run_data(
            data_quality_flags=DataQualityFlags(
                hr_artifacts=[],
                gps_drift_segments=[],
                cadence_inconsistencies=[],
            )
        )
        warnings = _format_warnings(run_data)
        assert warnings == ""

    def test_hr_artifact_warning(self):
        run_data = _create_mock_run_data(
            data_quality_flags=DataQualityFlags(
                hr_artifacts=[{"index": 0, "value_bpm": 225.0, "type": "threshold_exceeded"}],
                gps_drift_segments=[],
                cadence_inconsistencies=[],
            )
        )
        warnings = _format_warnings(run_data)
        assert "[VALIDATION_WARNING]" in warnings
        assert "HR artifact" in warnings
        assert "225.0" in warnings

    def test_gps_drift_warning(self):
        run_data = _create_mock_run_data(
            data_quality_flags=DataQualityFlags(
                hr_artifacts=[],
                gps_drift_segments=[{
                    "start_index": 0,
                    "end_index": 5,
                    "distance_meters": 150.0,
                    "duration_seconds": 30.0,
                    "expected_pace": 3.5,
                }],
                cadence_inconsistencies=[],
            )
        )
        warnings = _format_warnings(run_data)
        assert "[VALIDATION_WARNING]" in warnings
        assert "GPS drift" in warnings

    def test_cadence_inconsistency_warning(self):
        run_data = _create_mock_run_data(
            data_quality_flags=DataQualityFlags(
                hr_artifacts=[],
                gps_drift_segments=[],
                cadence_inconsistencies=[{
                    "start_index": 0,
                    "end_index": 0,
                    "change_pct": 33.33,
                    "pace_change_pct": 0.0,
                    "is_pace_explained": False,
                }],
            )
        )
        warnings = _format_warnings(run_data)
        assert "[VALIDATION_WARNING]" in warnings
        assert "Cadence inconsistency" in warnings

    def test_warnings_with_missing_keys(self):
        """Gracefully handle dicts missing expected keys."""
        mock_flags = MagicMock()
        mock_flags.hr_artifacts = [{"value_bpm": 200.0}]
        mock_flags.gps_drift_segments = [{"distance_meters": 100.0}]
        mock_flags.cadence_inconsistencies = [{"is_pace_explained": True}]
        run_data = MagicMock()
        run_data.data_quality_flags = mock_flags
        warnings = _format_warnings(run_data)
        assert "[VALIDATION_WARNING]" in warnings
        assert "N/A" in warnings


class TestFormatVerboseOutput:
    """Test _format_verbose_output function."""

    def test_verbose_output_contains_stages(self):
        run_data = _create_mock_run_data()
        output = _format_verbose_output(run_data, "/path/to/test.fit")
        assert "[VERBOSE] File: /path/to/test.fit" in output
        assert "1. Parse:" in output
        assert "2. Standard metrics:" in output
        assert "3. Asthma-aware metrics:" in output
        assert "4. Validation:" in output

    def test_verbose_output_contains_confidence(self):
        run_data = _create_mock_run_data()
        output = _format_verbose_output(run_data, "/path/to/test.fit")
        assert "Confidence score:" in output


class TestPersistRun:
    """Test _persist_run function with mocked DB."""

    def test_persist_run_serializes_all_fields(self, test_session, test_engine):
        run_data = _create_mock_run_data()

        with patch("run_intelligence.pipeline.runner.create_session") as mock_session, \
             patch("run_intelligence.pipeline.runner._get_engine") as mock_engine:

            mock_session.return_value = test_session
            mock_engine.return_value = test_engine

            with patch("run_intelligence.pipeline.runner.RunRepository") as MockRepo, \
                 patch("run_intelligence.pipeline.runner.AuditLogRepository") as MockAudit:

                mock_audit_instance = MagicMock()
                MockAudit.return_value = mock_audit_instance
                mock_repo_instance = MagicMock()
                MockRepo.return_value = mock_repo_instance

                _persist_run(run_data, "/path/to/test.fit")

                mock_repo_instance.create_run.assert_called_once()
                call_kwargs = mock_repo_instance.create_run.call_args.kwargs

                assert "file_path" in call_kwargs
                assert call_kwargs["file_path"] == "/path/to/test.fit"
                assert "raw_metrics_json" in call_kwargs
                assert "derived_metrics_json" in call_kwargs
                assert "data_quality_flags_json" in call_kwargs


class TestProcessFile:
    """Test process_file function."""

    def test_process_file_returns_run_data(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        mock_run_data = _create_mock_run_data()

        with patch("run_intelligence.pipeline.runner.validate_and_flag") as mock_validate:
            mock_validate.return_value = mock_run_data

            with patch("run_intelligence.pipeline.runner._persist_run"):
                result = process_file(str(fit_file), verbose=False, dry_run=True)

                assert isinstance(result, RunData)
                mock_validate.assert_called_once_with(str(fit_file), verbose=False)

    def test_process_file_dry_run_skips_persist(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        mock_run_data = _create_mock_run_data()

        with patch("run_intelligence.pipeline.runner.validate_and_flag") as mock_validate:
            mock_validate.return_value = mock_run_data

            with patch("run_intelligence.pipeline.runner._persist_run") as mock_persist:
                process_file(str(fit_file), verbose=False, dry_run=True)

                mock_persist.assert_not_called()

    def test_process_file_non_dry_run_calls_persist(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        mock_run_data = _create_mock_run_data()

        with patch("run_intelligence.pipeline.runner.validate_and_flag") as mock_validate:
            mock_validate.return_value = mock_run_data

            with patch("run_intelligence.pipeline.runner._persist_run") as mock_persist:
                process_file(str(fit_file), verbose=False, dry_run=False)

                mock_persist.assert_called_once()

    def test_process_file_invalid_file_raises_fit_parse_error(self, tmp_path):
        fit_file = tmp_path / "invalid.fit"
        fit_file.write_bytes(b"corrupt data")

        with patch("run_intelligence.pipeline.runner.validate_and_flag") as mock_validate:
            mock_validate.side_effect = FitParseError("Invalid FIT file")

            with pytest.raises(FitParseError):
                process_file(str(fit_file), verbose=False, dry_run=False)

    def test_process_file_metric_error_raises(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        with patch("run_intelligence.pipeline.runner.validate_and_flag") as mock_validate:
            mock_validate.side_effect = MetricCalculationError("Calculation failed")

            with pytest.raises(MetricCalculationError):
                process_file(str(fit_file), verbose=False, dry_run=False)

    def test_process_file_stdout_output(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        mock_run_data = _create_mock_run_data()

        captured_stdout = StringIO()

        with patch("run_intelligence.pipeline.runner.validate_and_flag") as mock_validate:
            mock_validate.return_value = mock_run_data

            with patch("run_intelligence.pipeline.runner._persist_run"):
                with patch("sys.stdout", captured_stdout):
                    process_file(str(fit_file), verbose=False, dry_run=True)

        output = captured_stdout.getvalue()
        assert "File processed:" in output or "[DRY-RUN]" in output

    def test_process_file_stderr_warnings(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        run_data_with_flags = _create_mock_run_data(
            data_quality_flags=DataQualityFlags(
                hr_artifacts=[{"index": 0, "value_bpm": 225.0, "type": "threshold_exceeded"}],
                gps_drift_segments=[],
                cadence_inconsistencies=[],
            )
        )

        captured_stderr = StringIO()

        with patch("run_intelligence.pipeline.runner.validate_and_flag") as mock_validate:
            mock_validate.return_value = run_data_with_flags

            with patch("run_intelligence.pipeline.runner._persist_run"):
                with patch("sys.stderr", captured_stderr):
                    process_file(str(fit_file), verbose=False, dry_run=True)

        output = captured_stderr.getvalue()
        assert "[VALIDATION_WARNING]" in output

    def test_process_file_timing_in_verbose_mode(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        mock_run_data = _create_mock_run_data()

        captured_stdout = StringIO()

        with patch("run_intelligence.pipeline.runner.validate_and_flag") as mock_validate:
            mock_validate.return_value = mock_run_data

            with patch("run_intelligence.pipeline.runner._persist_run"):
                with patch("sys.stdout", captured_stdout):
                    process_file(str(fit_file), verbose=True, dry_run=True)

        output = captured_stdout.getvalue()
        assert "[VERBOSE]" in output or "[RUNNER]" in output


class TestProcessFileNFR1:
    """Test NFR1: runner overhead remains low."""

    def test_nfr1_overhead_acceptable(self, tmp_path):
        """Ensure runner wrapper overhead is well under NFR1 limit."""
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        mock_run_data = _create_mock_run_data()

        with patch("run_intelligence.pipeline.runner.validate_and_flag") as mock_validate:
            mock_validate.return_value = mock_run_data

            with patch("run_intelligence.pipeline.runner._persist_run"):
                start = time.time()
                process_file(str(fit_file), verbose=False, dry_run=True)
                elapsed = time.time() - start

                assert elapsed <= 1.0, f"Runner overhead took {elapsed:.3f}s, exceeds 1s budget"


class TestProcessFileErrorHandling:
    """Test error handling in process_file."""

    def test_fit_parse_error_propagates(self, tmp_path):
        fit_file = tmp_path / "invalid.fit"
        fit_file.write_bytes(b"corrupt")

        with patch("run_intelligence.pipeline.runner.validate_and_flag") as mock_validate:
            mock_validate.side_effect = FitParseError("Invalid FIT file")

            with pytest.raises(FitParseError):
                process_file(str(fit_file), verbose=False, dry_run=False)

    def test_persist_failure_goes_to_stderr(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        mock_run_data = _create_mock_run_data()

        with patch("run_intelligence.pipeline.runner.validate_and_flag") as mock_validate:
            mock_validate.return_value = mock_run_data

            with patch("run_intelligence.pipeline.runner._persist_run") as mock_persist:
                mock_persist.side_effect = Exception("DB error")

                captured_stderr = StringIO()
                with patch("sys.stderr", captured_stderr):
                    with pytest.raises(MetricCalculationError):
                        process_file(str(fit_file), verbose=False, dry_run=False)

                output = captured_stderr.getvalue()
                assert "[PIPELINE_ERROR]" in output


class TestProcessFileIntegration:
    """Integration-style tests using mocks to simulate full pipeline."""

    def test_full_pipeline_returns_valid_rundata(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"fake fit content")

        mock_run_data = _create_mock_run_data(
            standard_metrics=StandardMetrics(
                pace_avg_min_per_km=5.5,
            ),
            asthma_aware_metrics=AsthmaAwareMetrics(
                hr_pace_drift_pct=3.0,
                confidence_score=0.9,
            ),
            data_quality_flags=DataQualityFlags(
                confidence_score=0.9,
                low_confidence_flag=False,
            ),
        )

        with patch("run_intelligence.pipeline.runner.validate_and_flag") as mock_validate:
            mock_validate.return_value = mock_run_data

            with patch("run_intelligence.pipeline.runner._persist_run"):
                result = process_file(str(fit_file), verbose=False, dry_run=True)

                assert result.raw_data is not None
                assert result.standard_metrics is not None
                assert result.asthma_aware_metrics is not None
                assert result.data_quality_flags is not None

    def test_verbose_mode_includes_timing(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        mock_run_data = _create_mock_run_data()

        captured_stdout = StringIO()

        with patch("run_intelligence.pipeline.runner.validate_and_flag") as mock_validate:
            mock_validate.return_value = mock_run_data

            with patch("run_intelligence.pipeline.runner._persist_run"):
                with patch("sys.stdout", captured_stdout):
                    process_file(str(fit_file), verbose=True, dry_run=True)

        output = captured_stdout.getvalue()
        assert "Processing completed" in output or "NFR1" in output


class TestBatchResult:
    """Test BatchResult dataclass."""

    def test_batch_result_creation(self):
        result = BatchResult(
            total_files=5,
            success_count=4,
            failure_count=1,
            failed_files=["/path/to/corrupt.fit"],
            total_elapsed_seconds=12.3,
            dry_run=False,
        )
        assert result.total_files == 5
        assert result.success_count == 4
        assert result.failure_count == 1
        assert result.failed_files == ["/path/to/corrupt.fit"]
        assert result.total_elapsed_seconds == 12.3
        assert result.dry_run is False


class TestFormatBatchSummary:
    """Test _format_batch_summary function."""

    def test_basic_summary(self):
        result = BatchResult(
            total_files=3,
            success_count=3,
            failure_count=0,
            failed_files=[],
            total_elapsed_seconds=5.5,
            dry_run=False,
        )
        summary = _format_batch_summary(result)
        assert "Batch Processing Summary" in summary
        assert "Total files: 3" in summary
        assert "Successful: 3" in summary
        assert "Failed: 0" in summary
        assert "Total time: 5.5s" in summary

    def test_summary_with_failed_files(self):
        result = BatchResult(
            total_files=5,
            success_count=4,
            failure_count=1,
            failed_files=["/path/to/corrupt.fit"],
            total_elapsed_seconds=10.0,
            dry_run=False,
        )
        summary = _format_batch_summary(result)
        assert "Failed files: corrupt.fit" in summary

    def test_summary_dry_run_note(self):
        result = BatchResult(
            total_files=2,
            success_count=2,
            failure_count=0,
            failed_files=[],
            total_elapsed_seconds=3.0,
            dry_run=True,
        )
        summary = _format_batch_summary(result)
        assert "[DRY RUN] No data was written to the database." in summary

    def test_summary_no_failed_files_omits_line(self):
        result = BatchResult(
            total_files=1,
            success_count=1,
            failure_count=0,
            failed_files=[],
            total_elapsed_seconds=1.2,
            dry_run=False,
        )
        summary = _format_batch_summary(result)
        assert "Failed files:" not in summary


class TestFormatBatchError:
    """Test _format_batch_error function."""

    def test_format_fit_parse_error(self):
        error = FitParseError("File is truncated")
        formatted = _format_batch_error("corrupt.fit", error)
        assert formatted == "[BATCH_ERROR] corrupt.fit: FitParseError: File is truncated\n"

    def test_format_metric_calculation_error(self):
        error = MetricCalculationError("Division by zero")
        formatted = _format_batch_error("bad.fit", error)
        assert formatted == "[BATCH_ERROR] bad.fit: MetricCalculationError: Division by zero\n"

    def test_format_generic_exception(self):
        error = Exception("Something broke")
        formatted = _format_batch_error("weird.fit", error)
        assert formatted == "[BATCH_ERROR] weird.fit: Exception: Something broke\n"


class TestProcessDirectory:
    """Test process_directory function."""

    def test_all_valid_files(self, tmp_path):
        (tmp_path / "a.fit").write_bytes(b"")
        (tmp_path / "b.fit").write_bytes(b"")

        with patch("run_intelligence.pipeline.runner.process_file") as mock_process:
            result = process_directory(str(tmp_path), verbose=False, dry_run=False)

            assert result.total_files == 2
            assert result.success_count == 2
            assert result.failure_count == 0
            assert result.failed_files == []
            assert mock_process.call_count == 2

    def test_one_corrupt_file_continues(self, tmp_path):
        (tmp_path / "aaa_corrupt.fit").write_bytes(b"")
        (tmp_path / "valid.fit").write_bytes(b"")

        with patch("run_intelligence.pipeline.runner.process_file") as mock_process:
            mock_process.side_effect = [
                FitParseError("Invalid header"),
                _create_mock_run_data(),
            ]

            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                result = process_directory(str(tmp_path), verbose=False, dry_run=False)

            assert result.total_files == 2
            assert result.success_count == 1
            assert result.failure_count == 1
            assert result.failed_files == [str(tmp_path / "aaa_corrupt.fit")]

            stderr_output = captured_stderr.getvalue()
            assert "[BATCH_ERROR] aaa_corrupt.fit:" in stderr_output

    def test_all_corrupt_files(self, tmp_path):
        (tmp_path / "a.fit").write_bytes(b"")
        (tmp_path / "b.fit").write_bytes(b"")

        with patch("run_intelligence.pipeline.runner.process_file") as mock_process:
            mock_process.side_effect = FitParseError("All bad")

            result = process_directory(str(tmp_path), verbose=False, dry_run=False)

            assert result.total_files == 2
            assert result.success_count == 0
            assert result.failure_count == 2
            assert len(result.failed_files) == 2

    def test_dry_run_no_db_writes(self, tmp_path):
        (tmp_path / "test.fit").write_bytes(b"")

        with patch("run_intelligence.pipeline.runner.process_file") as mock_process:
            mock_process.return_value = _create_mock_run_data()

            result = process_directory(str(tmp_path), verbose=False, dry_run=True)

            assert result.dry_run is True
            mock_process.assert_called_once_with(
                str(tmp_path / "test.fit"), verbose=False, dry_run=True
            )

    def test_verbose_passed_to_process_file(self, tmp_path):
        (tmp_path / "test.fit").write_bytes(b"")

        with patch("run_intelligence.pipeline.runner.process_file") as mock_process:
            mock_process.return_value = _create_mock_run_data()

            process_directory(str(tmp_path), verbose=True, dry_run=False)

            mock_process.assert_called_once_with(
                str(tmp_path / "test.fit"), verbose=True, dry_run=False
            )

    def test_empty_directory(self, tmp_path):
        result = process_directory(str(tmp_path), verbose=False, dry_run=False)

        assert result.total_files == 0
        assert result.success_count == 0
        assert result.failure_count == 0
        assert result.failed_files == []

    def test_no_fit_files(self, tmp_path):
        (tmp_path / "readme.txt").write_bytes(b"not a fit file")
        (tmp_path / "image.png").write_bytes(b"not a fit file")

        result = process_directory(str(tmp_path), verbose=False, dry_run=False)

        assert result.total_files == 0
        assert result.success_count == 0
        assert result.failure_count == 0
        assert result.failed_files == []

    def test_nonexistent_directory_raises(self, tmp_path):
        bad_path = tmp_path / "does_not_exist"

        with pytest.raises(ValueError, match="Directory does not exist"):
            process_directory(str(bad_path))

    def test_file_path_raises(self, tmp_path):
        fit_file = tmp_path / "test.fit"
        fit_file.write_bytes(b"")

        with pytest.raises(ValueError, match="Path is not a directory"):
            process_directory(str(fit_file))

    def test_stderr_output_on_failure(self, tmp_path):
        (tmp_path / "bad.fit").write_bytes(b"")

        with patch("run_intelligence.pipeline.runner.process_file") as mock_process:
            mock_process.side_effect = MetricCalculationError("Calc failed")

            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                process_directory(str(tmp_path))

            output = captured_stderr.getvalue()
            assert "[BATCH_ERROR] bad.fit:" in output
            assert "MetricCalculationError" in output

    def test_nfr4_failure_does_not_stop_batch(self, tmp_path):
        (tmp_path / "first.fit").write_bytes(b"")
        (tmp_path / "second.fit").write_bytes(b"")
        (tmp_path / "third.fit").write_bytes(b"")

        with patch("run_intelligence.pipeline.runner.process_file") as mock_process:
            mock_process.side_effect = [
                FitParseError("Bad first"),
                _create_mock_run_data(),
                _create_mock_run_data(),
            ]

            result = process_directory(str(tmp_path))

            assert result.success_count == 2
            assert result.failure_count == 1
            assert mock_process.call_count == 3

    def test_case_insensitive_fit_matching(self, tmp_path):
        (tmp_path / "lower.fit").write_bytes(b"")
        (tmp_path / "UPPER.FIT").write_bytes(b"")

        with patch("run_intelligence.pipeline.runner.process_file") as mock_process:
            mock_process.return_value = _create_mock_run_data()

            result = process_directory(str(tmp_path))

            assert result.total_files == 2
            assert result.success_count == 2

    def test_files_processed_alphabetically(self, tmp_path):
        (tmp_path / "z.fit").write_bytes(b"")
        (tmp_path / "a.fit").write_bytes(b"")
        (tmp_path / "m.fit").write_bytes(b"")

        call_order = []

        def capture_call(file_path, **kwargs):
            call_order.append(file_path)
            return _create_mock_run_data()

        with patch("run_intelligence.pipeline.runner.process_file") as mock_process:
            mock_process.side_effect = capture_call

            process_directory(str(tmp_path))

        assert call_order == sorted(call_order)

    def test_total_elapsed_time_recorded(self, tmp_path):
        (tmp_path / "test.fit").write_bytes(b"")

        with patch("run_intelligence.pipeline.runner.process_file") as mock_process:
            mock_process.return_value = _create_mock_run_data()

            result = process_directory(str(tmp_path))

            assert result.total_elapsed_seconds >= 0.0


class TestProcessDirectoryCLI:
    """Test CLI-level batch behavior via _handle_batch (indirectly)."""

    def test_cli_exit_code_zero_on_partial_success(self, tmp_path):
        from run_intelligence.cli import _handle_batch

        (tmp_path / "a.fit").write_bytes(b"")
        with patch("run_intelligence.pipeline.runner.process_directory") as mock_dir:
            mock_dir.return_value = BatchResult(
                total_files=2,
                success_count=1,
                failure_count=1,
                failed_files=[str(tmp_path / "b.fit")],
                total_elapsed_seconds=5.0,
                dry_run=False,
            )
            with pytest.raises(typer.Exit) as exc_info:
                _handle_batch(str(tmp_path), verbose=False, dry_run=False)
            assert exc_info.value.exit_code == 0

    def test_cli_exit_code_one_on_all_failures(self, tmp_path):
        from run_intelligence.cli import _handle_batch

        (tmp_path / "a.fit").write_bytes(b"")
        with patch("run_intelligence.pipeline.runner.process_directory") as mock_dir:
            mock_dir.return_value = BatchResult(
                total_files=2,
                success_count=0,
                failure_count=2,
                failed_files=[str(tmp_path / "a.fit")],
                total_elapsed_seconds=5.0,
                dry_run=False,
            )
            with pytest.raises(typer.Exit) as exc_info:
                _handle_batch(str(tmp_path), verbose=False, dry_run=False)
            assert exc_info.value.exit_code == 1

    def test_cli_exit_code_two_on_invalid_directory(self, tmp_path):
        from run_intelligence.cli import _handle_batch

        with patch("run_intelligence.pipeline.runner.process_directory") as mock_dir:
            mock_dir.side_effect = ValueError("Path is not a directory: /some/file.fit")
            with pytest.raises(typer.Exit) as exc_info:
                _handle_batch("/some/file.fit", verbose=False, dry_run=False)
            assert exc_info.value.exit_code == 2
