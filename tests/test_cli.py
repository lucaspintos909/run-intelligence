"""Tests for CLI output modes - stdout/stderr separation, exit codes, and help."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from run_intelligence.cli import app


class TestCliHelp:
    """AC2: Comprehensive help documentation."""

    def test_main_help_shows_all_commands(self):
        result = subprocess.run(
            [sys.executable, "-m", "run_intelligence", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        output = result.stdout
        assert "process" in output
        assert "batch" in output
        assert "log-health" in output
        assert "report" in output
        assert "purge" in output

    def test_process_help_shows_options(self):
        result = subprocess.run(
            [sys.executable, "-m", "run_intelligence", "process", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        output = result.stdout
        assert "--file" in output or "-f" in output
        assert "--verbose" in output or "-v" in output
        assert "--dry-run" in output

    def test_batch_help_shows_options(self):
        result = subprocess.run(
            [sys.executable, "-m", "run_intelligence", "batch", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        output = result.stdout
        assert "--verbose" in output or "-v" in output
        assert "--dry-run" in output

    def test_report_help_shows_options(self):
        result = subprocess.run(
            [sys.executable, "-m", "run_intelligence", "report", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        output = result.stdout
        assert "--start" in output
        assert "--end" in output
        assert "--output" in output or "-o" in output
        assert "--verbose" in output or "-v" in output

    def test_log_health_help_shows_options(self):
        result = subprocess.run(
            [sys.executable, "-m", "run_intelligence", "log-health", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        output = result.stdout
        assert "--date" in output
        assert "--peak-flow" in output
        assert "--verbose" in output or "-v" in output

    def test_purge_help_shows_options(self):
        result = subprocess.run(
            [sys.executable, "-m", "run_intelligence", "purge", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        output = result.stdout
        assert "--confirm" in output
        assert "--verbose" in output or "-v" in output

    def test_version_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "run_intelligence", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        assert "run-intelligence" in result.stdout
        assert "0.1.0" in result.stdout


class TestExitCodes:
    """AC3: Consistent exit codes."""

    def test_process_missing_file_exits_2(self):
        result = subprocess.run(
            [sys.executable, "-m", "run_intelligence", "process"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 2
        assert "[CLI_ERROR]" in result.stderr or "Missing file path" in result.stderr

    def test_batch_invalid_directory_exits_1(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "run_intelligence",
                "batch",
                "/nonexistent/path/to/dir",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 1

    def test_report_missing_required_args_exits_2(self):
        result = subprocess.run(
            [sys.executable, "-m", "run_intelligence", "report"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 2

    def test_report_invalid_date_format_exits_2(self, tmp_path):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "run_intelligence",
                "report",
                "--start",
                "invalid",
                "--end",
                "2026-05-31",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 2
        assert "[REPORT_ERROR]" in result.stderr


class TestLogHealthOutput:
    """AC1, AC7: stdout/stderr separation for log_health command."""

    @pytest.fixture
    def mock_health_log_repo(self):
        mock_entry = MagicMock()
        mock_entry.id = 1
        mock_entry.date = "2026-05-21"
        return mock_entry

    def test_log_health_success_goes_to_stdout(self, mock_health_log_repo):
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.create_entry.return_value = mock_health_log_repo
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()
                result = runner.invoke(
                    app,
                    ["log-health", "--date", "2026-05-21", "--peak-flow", "450"],
                )
                assert result.exit_code == 0
                assert (
                    "Logged:" in result.stdout or "peak_flow=450" in result.stdout
                )

    def test_log_health_invalid_date_goes_to_stderr(self):
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["log-health", "--date", "not-a-date", "--peak-flow", "450"],
        )
        assert result.exit_code == 2
        assert (
            "[VALIDATION_ERROR]" in result.output
            or "Invalid date format" in result.output
        )

    def test_log_health_verbose_mode_shows_field_values(self):
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_entry = MagicMock()
                mock_entry.id = 1
                mock_repo = MagicMock()
                mock_repo.create_entry.return_value = mock_entry
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()
                result = runner.invoke(
                    app,
                    [
                        "log-health",
                        "--date",
                        "2026-05-21",
                        "--peak-flow",
                        "450",
                        "--verbose",
                    ],
                )
                assert result.exit_code == 0
                assert "[LOG_HEALTH]" in result.stdout
                assert "Peak flow: 450" in result.stdout


class TestReportOutput:
    """AC1, AC4: stdout/stderr separation and --output flag for report command."""

    def test_report_without_output_writes_to_stdout(self):
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.RunRepository"
            ) as mock_run_repo:
                with patch(
                    "run_intelligence.db.repository.HealthLogRepository"
                ) as mock_health_repo:
                    mock_run_repo_instance = MagicMock()
                    mock_run_repo_instance.get_runs.return_value = []
                    mock_run_repo.return_value = mock_run_repo_instance

                    mock_health_repo_instance = MagicMock()
                    mock_health_repo_instance.get_entries.return_value = []
                    mock_health_repo.return_value = mock_health_repo_instance

                    from typer.testing import CliRunner

                    runner = CliRunner()
                    result = runner.invoke(
                        app,
                        ["report", "--start", "2026-05-01", "--end", "2026-05-31"],
                    )
                    assert result.exit_code == 0
                    assert (
                        "Medical Report:" in result.stdout
                        or "Run Summary" in result.stdout
                    )

    def test_report_with_output_writes_to_file(self, tmp_path):
        output_file = tmp_path / "report.md"

        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.RunRepository"
            ) as mock_run_repo:
                with patch(
                    "run_intelligence.db.repository.HealthLogRepository"
                ) as mock_health_repo:
                    mock_run_repo_instance = MagicMock()
                    mock_run_repo_instance.get_runs.return_value = []
                    mock_run_repo.return_value = mock_run_repo_instance

                    mock_health_repo_instance = MagicMock()
                    mock_health_repo_instance.get_entries.return_value = []
                    mock_health_repo.return_value = mock_health_repo_instance

                    from typer.testing import CliRunner

                    runner = CliRunner()
                    result = runner.invoke(
                        app,
                        [
                            "report",
                            "--start",
                            "2026-05-01",
                            "--end",
                            "2026-05-31",
                            "--output",
                            str(output_file),
                        ],
                    )
                    assert result.exit_code == 0
                    assert output_file.exists()
                    content = output_file.read_text()
                    assert (
                        "Medical Report:" in content or "Run Summary" in content
                    )
                    assert "Report written to" in result.stdout

    def test_report_output_file_missing_directory(self, tmp_path):
        output_file = tmp_path / "nonexistent" / "report.md"

        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.RunRepository"
            ) as mock_run_repo:
                with patch(
                    "run_intelligence.db.repository.HealthLogRepository"
                ) as mock_health_repo:
                    mock_run_repo_instance = MagicMock()
                    mock_run_repo_instance.get_runs.return_value = []
                    mock_run_repo.return_value = mock_run_repo_instance

                    mock_health_repo_instance = MagicMock()
                    mock_health_repo_instance.get_entries.return_value = []
                    mock_health_repo.return_value = mock_health_repo_instance

                    from typer.testing import CliRunner

                    runner = CliRunner()
                    result = runner.invoke(
                        app,
                        [
                            "report",
                            "--start",
                            "2026-05-01",
                            "--end",
                            "2026-05-31",
                            "--output",
                            str(output_file),
                        ],
                    )
                    assert result.exit_code == 1
                    assert "[REPORT_ERROR]" in result.output

    def test_report_start_after_end_returns_2(self):
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["report", "--start", "2026-06-01", "--end", "2026-05-01"],
        )
        assert result.exit_code == 2
        assert "[REPORT_ERROR]" in result.output

    def test_report_verbose_mode_shows_stages(self):
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.RunRepository"
            ) as mock_run_repo:
                with patch(
                    "run_intelligence.db.repository.HealthLogRepository"
                ) as mock_health_repo:
                    mock_run_repo_instance = MagicMock()
                    mock_run_repo_instance.get_runs.return_value = []
                    mock_run_repo.return_value = mock_run_repo_instance

                    mock_health_repo_instance = MagicMock()
                    mock_health_repo_instance.get_entries.return_value = []
                    mock_health_repo.return_value = mock_health_repo_instance

                    from typer.testing import CliRunner

                    runner = CliRunner()
                    result = runner.invoke(
                        app,
                        [
                            "report",
                            "--start",
                            "2026-05-01",
                            "--end",
                            "2026-05-31",
                            "--verbose",
                        ],
                    )
                    assert result.exit_code == 0
                    assert "[REPORT]" in result.stdout


class TestPurgeOutput:
    """AC1, AC8: stdout/stderr separation for purge command."""

    def test_purge_without_confirm_warns_to_stdout(self):
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["purge"],
        )
        assert result.exit_code == 0
        assert "Warning:" in result.stdout
        assert "--confirm" in result.stdout

    def test_purge_with_confirm_success(self):
        with patch("run_intelligence.db.session._get_engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = (
                lambda _: mock_conn
            )
            mock_engine.return_value.connect.return_value.__exit__ = (
                lambda *_: None
            )

            from typer.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(
                app,
                ["purge", "--confirm"],
            )
            assert result.exit_code == 0
            assert (
                "purged" in result.stdout.lower() or "All data" in result.stdout
            )
            # Verify SQL was actually executed
            execute_calls = [
                call for call in mock_conn.method_calls if "execute" in str(call)
            ]
            assert len(execute_calls) >= 5

    def test_purge_verbose_mode_shows_steps(self):
        with patch("run_intelligence.db.session._get_engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = (
                lambda _: mock_conn
            )
            mock_engine.return_value.connect.return_value.__exit__ = (
                lambda *_: None
            )

            from typer.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(
                app,
                ["purge", "--confirm", "--verbose"],
            )
            assert result.exit_code == 0
            assert "[PURGE]" in result.stdout


class TestStderrFiltering:
    """AC1: stderr can be filtered with 2>/dev/null."""

    def test_log_health_error_goes_to_actual_stderr(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "run_intelligence",
                "log-health",
                "--date",
                "invalid-date",
                "--peak-flow",
                "450",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 2
        assert "[VALIDATION_ERROR]" in result.stderr
        assert result.stdout == ""

    def test_report_error_goes_to_actual_stderr(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "run_intelligence",
                "report",
                "--start",
                "invalid",
                "--end",
                "2026-05-31",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 2
        assert "[REPORT_ERROR]" in result.stderr
        assert result.stdout == ""


class TestProcessAndBatchRegression:
    """Regression tests for process and batch stdout/stderr separation."""

    def test_process_file_not_found_exits_1(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "run_intelligence",
                "process",
                "/nonexistent/file.fit",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 1

    def test_process_help_shows_all_options(self):
        result = subprocess.run(
            [sys.executable, "-m", "run_intelligence", "process", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        output = result.stdout
        assert "--verbose" in output or "-v" in output
        assert "--dry-run" in output

    def test_batch_help_shows_all_options(self):
        result = subprocess.run(
            [sys.executable, "-m", "run_intelligence", "batch", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        output = result.stdout
        assert "--verbose" in output or "-v" in output
        assert "--dry-run" in output


class TestDryRunMode:
    """AC6: Dry-run mode consistency."""

    def test_process_dry_run_flag_exists(self):
        result = subprocess.run(
            [sys.executable, "-m", "run_intelligence", "process", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert "--dry-run" in result.stdout

    def test_batch_dry_run_flag_exists(self):
        result = subprocess.run(
            [sys.executable, "-m", "run_intelligence", "batch", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert "--dry-run" in result.stdout


class TestDbFailureExitCodes:
    """Missing tests for DB failure exit code 1 on non-processing commands."""

    def test_log_health_db_failure_exits_1(self):
        with patch(
            "run_intelligence.db.session._get_engine",
            side_effect=RuntimeError("DB unreachable"),
        ):
            from typer.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(
                app,
                ["log-health", "--date", "2026-05-21", "--peak-flow", "450"],
            )
            assert result.exit_code == 1
            assert "[LOG_HEALTH_ERROR]" in result.output

    def test_report_db_failure_exits_1(self):
        with patch(
            "run_intelligence.db.session._get_engine",
            side_effect=RuntimeError("DB unreachable"),
        ):
            from typer.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(
                app,
                ["report", "--start", "2026-05-01", "--end", "2026-05-31"],
            )
            assert result.exit_code == 1
            assert "[REPORT_ERROR]" in result.output

    def test_purge_db_failure_exits_1(self):
        with patch(
            "run_intelligence.db.session._get_engine",
            side_effect=RuntimeError("DB unreachable"),
        ):
            from typer.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(
                app,
                ["purge", "--confirm"],
            )
            assert result.exit_code == 1
            assert "[PURGE_ERROR]" in result.output


class TestStderrNullFilter:
    """Test actual 2>/dev/null suppression works at OS level."""

    def test_log_health_stderr_suppressed_by_redirect(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "run_intelligence",
                "log-health",
                "--date",
                "invalid-date",
                "--peak-flow",
                "450",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 2
        assert result.stdout == b""

    def test_report_stderr_suppressed_by_redirect(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "run_intelligence",
                "report",
                "--start",
                "invalid",
                "--end",
                "2026-05-31",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 2
        assert result.stdout == b""
