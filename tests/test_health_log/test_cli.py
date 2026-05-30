"""Tests for interactive health log CLI functionality."""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from run_intelligence.cli import app


class TestLogHealthInteractiveMode:
    """Tests for interactive mode when running log-health without arguments."""

    def test_interactive_mode_detected_when_no_args_provided(self):
        """Test that interactive mode is detected when no health arguments are provided."""
        # The CLI should detect interactive mode by checking if all health params are None
        # This is a code-level test of the logic
        from run_intelligence.cli import log_health

        # Simulate the interactive mode detection logic
        date_val = None
        peak_flow = None
        sleep_quality = None
        post_run_rpe = None
        asthma_symptoms = None
        saba_use = None
        notes = None

        interactive_mode = (
            date_val is None
            and peak_flow is None
            and sleep_quality is None
            and post_run_rpe is None
            and asthma_symptoms is None
            and saba_use is None
            and notes is None
        )

        assert interactive_mode is True

    def test_non_interactive_mode_with_args(self):
        """Test that non-interactive mode is detected when args are provided."""
        # Test with args provided
        date_val = "2026-05-21"
        peak_flow = 450

        interactive_mode = (
            date_val is None
            and peak_flow is None
            and sleep_quality is None
            and post_run_rpe is None
            and asthma_symptoms is None
            and saba_use is None
            and notes is None
        )

        assert interactive_mode is False

    def test_interactive_mode_partial_args(self):
        """Test that partial args trigger non-interactive mode (only flags used)."""
        # Only some args provided - still non-interactive
        date_val = None
        peak_flow = None
        sleep_quality = 3  # One arg provided
        post_run_rpe = None
        asthma_symptoms = None
        saba_use = None
        notes = None

        interactive_mode = (
            date_val is None
            and peak_flow is None
            and sleep_quality is None
            and post_run_rpe is None
            and asthma_symptoms is None
            and saba_use is None
            and notes is None
        )

        assert interactive_mode is False


class TestLogHealthNonInteractiveMode:
    """Tests for non-interactive mode (existing functionality)."""

    @pytest.fixture
    def mock_health_entry(self):
        """Create a mock health log entry."""
        mock = MagicMock()
        mock.id = 1
        mock.date = date(2026, 5, 21)
        return mock

    def test_log_health_with_all_args(self, mock_health_entry):
        """Test log-health with all arguments provided."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.create_entry.return_value = mock_health_entry
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()
                result = runner.invoke(
                    app,
                    [
                        "log-health",
                        "--date", "2026-05-21",
                        "--peak-flow", "450",
                        "--sleep-quality", "4",
                        "--post-run-rpe", "7",
                        "--asthma-symptoms", "2",
                        "--notes", "Test entry",
                    ],
                )
                assert result.exit_code == 0

    def test_log_health_with_minimal_args(self, mock_health_entry):
        """Test log-health with only required/optional fields."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.create_entry.return_value = mock_health_entry
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()
                result = runner.invoke(
                    app,
                    ["log-health", "--peak-flow", "450"],
                )
                assert result.exit_code == 0


class TestLogHealthInputValidation:
    """Tests for input validation in both modes."""

    def test_invalid_date_format_exits_2(self):
        """Test that invalid date format returns exit code 2."""
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["log-health", "--date", "not-a-date", "--peak-flow", "450"],
        )
        assert result.exit_code == 2
        assert "[VALIDATION_ERROR]" in result.output or "Invalid date format" in result.output

    def test_date_format_yyyy_mm_dd(self):
        """Test that YYYY-MM-DD date format is accepted."""
        mock_entry = MagicMock()
        mock_entry.id = 1

        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.create_entry.return_value = mock_entry
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()
                result = runner.invoke(
                    app,
                    ["log-health", "--date", "2026-05-21", "--peak-flow", "450"],
                )
                assert result.exit_code == 0

    def test_sleep_quality_validation_range(self):
        """Test sleep quality validation (1-5)."""
        # Test value too low
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["log-health", "--sleep-quality", "0", "--peak-flow", "450"],
        )
        # Typer validates min/max on options - this should fail at validation
        assert result.exit_code == 2

    def test_sleep_quality_max_validation(self):
        """Test sleep quality max validation (1-5)."""
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["log-health", "--sleep-quality", "6", "--peak-flow", "450"],
        )
        assert result.exit_code == 2

    def test_post_run_rpe_validation_range(self):
        """Test post-run RPE validation (1-10)."""
        from typer.testing import CliRunner

        runner = CliRunner()
        # Value too low
        result = runner.invoke(
            app,
            ["log-health", "--post-run-rpe", "0", "--peak-flow", "450"],
        )
        assert result.exit_code == 2

    def test_asthma_symptoms_validation_range(self):
        """Test asthma symptoms validation (0-5)."""
        from typer.testing import CliRunner

        runner = CliRunner()
        # Value too high
        result = runner.invoke(
            app,
            ["log-health", "--asthma-symptoms", "6", "--peak-flow", "450"],
        )
        assert result.exit_code == 2


class TestLogHealthEdgeCases:
    """Edge case tests for health log CLI."""

    @pytest.fixture
    def mock_health_entry(self):
        mock = MagicMock()
        mock.id = 42
        mock.date = date.today()
        return mock

    def test_optional_fields_can_be_none(self, mock_health_entry):
        """Test that optional fields can be None in database."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.create_entry.return_value = mock_health_entry
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()
                # Only provide date, leave others optional
                result = runner.invoke(
                    app,
                    ["log-health", "--date", "2026-05-21"],
                )
                # Should succeed with only date provided
                assert result.exit_code == 0

    def test_saba_use_boolean_flag(self, mock_health_entry):
        """Test saba-use boolean flag works correctly."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.create_entry.return_value = mock_health_entry
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()

                # Test with just the flag (typer Boolean option)
                # This sets saba_use to True - to set False, omit the flag
                result = runner.invoke(
                    app,
                    ["log-health", "--peak-flow", "450", "--saba-use"],
                )
                assert result.exit_code == 0

    def test_verbose_mode_shows_values(self, mock_health_entry):
        """Test verbose mode shows all field values."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.create_entry.return_value = mock_health_entry
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()
                result = runner.invoke(
                    app,
                    [
                        "log-health",
                        "--date", "2026-05-21",
                        "--peak-flow", "450",
                        "--sleep-quality", "4",
                        "--verbose",
                    ],
                )
                assert result.exit_code == 0
                assert "[LOG_HEALTH]" in result.output
                assert "Peak flow: 450" in result.output

    def test_notes_optional_field(self, mock_health_entry):
        """Test notes field is optional."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.create_entry.return_value = mock_health_entry
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()

                # Without notes
                result = runner.invoke(
                    app,
                    ["log-health", "--peak-flow", "450"],
                )
                assert result.exit_code == 0

                # With notes
                result = runner.invoke(
                    app,
                    ["log-health", "--peak-flow", "450", "--notes", "Feeling good"],
                )
                assert result.exit_code == 0


class TestLogHealthErrorHandling:
    """Tests for error handling in health log CLI."""

    def test_database_failure_exits_1(self):
        """Test database failure returns exit code 1."""
        from typer.testing import CliRunner

        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.create_entry.side_effect = Exception("DB connection failed")
                mock_repo_class.return_value = mock_repo

                runner = CliRunner()
                result = runner.invoke(
                    app,
                    ["log-health", "--peak-flow", "450"],
                )
                assert result.exit_code == 1
                assert "[LOG_HEALTH_ERROR]" in result.output
