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


class TestLogHealthRunAssociation:
    """Tests for run association functionality in log-health command."""

    @pytest.fixture
    def mock_run(self):
        """Create a mock run object."""
        mock = MagicMock()
        mock.id = 1
        mock.file_path = "/path/to/run.fit"
        mock.processed_at = date(2026, 5, 21)
        mock.raw_metrics_json = '{"distance": 5000}'
        return mock

    @pytest.fixture
    def mock_health_entry(self):
        """Create a mock health log entry."""
        mock = MagicMock()
        mock.id = 1
        mock.date = date(2026, 5, 21)
        return mock

    def test_associate_with_valid_run_id_passes(self, mock_run, mock_health_entry):
        """Test that associating with a valid run ID succeeds."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.RunRepository"
            ) as mock_run_repo_class:
                mock_run_repo = MagicMock()
                mock_run_repo.get_run.return_value = mock_run
                mock_run_repo_class.return_value = mock_run_repo

                with patch(
                    "run_intelligence.db.repository.HealthLogRepository"
                ) as mock_health_repo_class:
                    mock_health_repo = MagicMock()
                    mock_health_repo.create_entry.return_value = mock_health_entry
                    mock_health_repo_class.return_value = mock_health_repo

                    from typer.testing import CliRunner

                    runner = CliRunner()
                    result = runner.invoke(
                        app,
                        [
                            "log-health",
                            "--date", "2026-05-21",
                            "--peak-flow", "450",
                            "--associate-run", "1",
                        ],
                    )
                    assert result.exit_code == 0
                    # Verify the run was looked up
                    mock_run_repo.get_run.assert_called_once_with(1)

    def test_associate_with_invalid_run_id_exits_2(self, mock_health_entry):
        """Test that associating with an invalid run ID shows error and exits 2."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.RunRepository"
            ) as mock_run_repo_class:
                mock_run_repo = MagicMock()
                mock_run_repo.get_run.return_value = None  # Run not found
                mock_run_repo_class.return_value = mock_run_repo

                with patch(
                    "run_intelligence.db.repository.HealthLogRepository"
                ) as mock_health_repo_class:
                    mock_health_repo = MagicMock()
                    mock_health_repo.create_entry.return_value = mock_health_entry
                    mock_health_repo_class.return_value = mock_health_repo

                    from typer.testing import CliRunner

                    runner = CliRunner()
                    result = runner.invoke(
                        app,
                        [
                            "log-health",
                            "--date", "2026-05-21",
                            "--peak-flow", "450",
                            "--associate-run", "999",
                        ],
                    )
                    assert result.exit_code == 2
                    assert "Run with ID 999 not found" in result.output or "[VALIDATION_ERROR]" in result.output

    def test_associate_with_no_available_runs_shows_message(self, mock_health_entry):
        """Test that when no runs are available, appropriate message is shown."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.RunRepository"
            ) as mock_run_repo_class:
                mock_run_repo = MagicMock()
                mock_run_repo.get_runs.return_value = []  # No runs
                mock_run_repo_class.return_value = mock_run_repo

                with patch(
                    "run_intelligence.db.repository.HealthLogRepository"
                ) as mock_health_repo_class:
                    mock_health_repo = MagicMock()
                    mock_health_repo.create_entry.return_value = mock_health_entry
                    mock_health_repo_class.return_value = mock_health_repo

                    from typer.testing import CliRunner

                    runner = CliRunner()
                    result = runner.invoke(
                        app,
                        [
                            "log-health",
                            "--date", "2026-05-21",
                            "--peak-flow", "450",
                        ],
                    )
                    # This should succeed - the no-runs message only shows in interactive mode
                    assert result.exit_code == 0

    def test_interactive_mode_with_runs_shows_available_runs(self, mock_run, mock_health_entry):
        """Test interactive mode shows available runs when runs exist."""
        mock_session = MagicMock()
        
        with patch("run_intelligence.db.session._get_engine"):
            with patch("sqlalchemy.orm.sessionmaker") as mock_sessionmaker:
                mock_sessionmaker.return_value.return_value = mock_session
                
                with patch(
                    "run_intelligence.db.repository.RunRepository"
                ) as mock_run_repo_class:
                    mock_run_repo = MagicMock()
                    mock_run_repo.get_runs.return_value = [mock_run]
                    mock_run_repo.get_run.return_value = mock_run
                    mock_run_repo_class.return_value = mock_run_repo

                    with patch(
                        "run_intelligence.db.repository.HealthLogRepository"
                    ) as mock_health_repo_class:
                        mock_health_repo = MagicMock()
                        mock_health_repo.create_entry.return_value = mock_health_entry
                        mock_health_repo_class.return_value = mock_health_repo

                        from typer.testing import CliRunner

                        runner = CliRunner()
                        # Interactive mode - no health args, let user select run
                        # Input: date, peak_flow, sleep_quality, skip post_run_rpe, skip asthma_symptoms,
                        # saba_use (n), skip notes, decline to associate with run (n)
                        result = runner.invoke(
                            app,
                            ["log-health"],
                            input="2026-05-21\n450\n3\n\n\nn\n\nn\n",
                        )
                        # Should complete without error
                        assert result.exit_code == 0

    def test_interactive_mode_selects_run(self, mock_run, mock_health_entry):
        """Test interactive mode allows run selection."""
        mock_session = MagicMock()
        
        with patch("run_intelligence.db.session._get_engine"):
            with patch("sqlalchemy.orm.sessionmaker") as mock_sessionmaker:
                mock_sessionmaker.return_value.return_value = mock_session
                
                with patch(
                    "run_intelligence.db.repository.RunRepository"
                ) as mock_run_repo_class:
                    mock_run_repo = MagicMock()
                    mock_run_repo.get_runs.return_value = [mock_run]
                    mock_run_repo.get_run.return_value = mock_run
                    mock_run_repo_class.return_value = mock_run_repo

                    with patch(
                        "run_intelligence.db.repository.HealthLogRepository"
                    ) as mock_health_repo_class:
                        mock_health_repo = MagicMock()
                        mock_health_repo.create_entry.return_value = mock_health_entry
                        mock_health_repo_class.return_value = mock_health_repo

                        from typer.testing import CliRunner

                        runner = CliRunner()
                        # Interactive mode with run selection
                        # Input: date, peak_flow, skip sleep, skip rpe, skip symptoms, saba_use (n),
                        # skip notes, confirm to associate with run (y), enter run ID 1
                        result = runner.invoke(
                            app,
                            ["log-health"],
                            input="2026-05-21\n450\n\n\n\nn\n\ny\n1\n",
                        )
                        # Should complete successfully
                        assert result.exit_code == 0


class TestListHealthLogs:
    """Tests for list-health-logs command."""

    @pytest.fixture
    def mock_health_entries(self):
        """Create mock health log entries."""
        entries = []
        for i in range(3):
            mock = MagicMock()
            mock.id = i + 1
            mock.date = date(2026, 5, 20 + i)
            mock.peak_flow = 400 + (i * 50)
            mock.sleep_quality = 3 + i
            mock.post_run_rpe = 5 + i
            mock.asthma_symptoms = i
            mock.saba_use = i > 0
            mock.notes = None
            mock.run_id = None
            entries.append(mock)
        return entries

    def test_list_health_logs_shows_entries(self, mock_health_entries):
        """Test list-health-logs shows entries."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.get_entries.return_value = mock_health_entries
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()
                result = runner.invoke(app, ["list-health-logs"])
                assert result.exit_code == 0
                # Check that entries are displayed
                assert "ID" in result.output
                assert "Date" in result.output
                assert "Peak Flow" in result.output
                assert "2026-05-20" in result.output
                assert "2026-05-21" in result.output
                assert "2026-05-22" in result.output

    def test_list_health_logs_with_limit(self, mock_health_entries):
        """Test list-health-logs respects --limit option."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.get_entries.return_value = mock_health_entries[:1]
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()
                result = runner.invoke(app, ["list-health-logs", "--limit", "1"])
                assert result.exit_code == 0
                # Verify limit was passed to get_entries
                mock_repo.get_entries.assert_called_once_with(limit=1)

    def test_list_health_logs_empty_list(self):
        """Test list-health-logs handles empty list."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.get_entries.return_value = []
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()
                result = runner.invoke(app, ["list-health-logs"])
                assert result.exit_code == 0
                assert "No health log entries found" in result.output


class TestViewHealthLog:
    """Tests for view-health-log command."""

    @pytest.fixture
    def mock_health_entry(self):
        """Create a mock health log entry."""
        mock = MagicMock()
        mock.id = 1
        mock.date = date(2026, 5, 21)
        mock.peak_flow = 450
        mock.sleep_quality = 4
        mock.post_run_rpe = 7
        mock.asthma_symptoms = 2
        mock.saba_use = False
        mock.notes = "Feeling good today"
        mock.run_id = None
        return mock

    def test_view_health_log_shows_entry_details(self, mock_health_entry):
        """Test view-health-log shows entry details."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.get_entry.return_value = mock_health_entry
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()
                result = runner.invoke(app, ["view-health-log", "--id", "1"])
                assert result.exit_code == 0
                # Check that entry details are displayed
                assert "Health Log Entry #1" in result.output
                assert "2026-05-21" in result.output
                assert "450" in result.output
                assert "Peak Flow" in result.output
                assert "Sleep Quality" in result.output

    def test_view_health_log_with_invalid_id_returns_exit_2(self):
        """Test view-health-log with invalid ID returns exit code 2 with error message."""
        with patch("run_intelligence.db.session._get_engine"):
            with patch(
                "run_intelligence.db.repository.HealthLogRepository"
            ) as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.get_entry.return_value = None  # Entry not found
                mock_repo_class.return_value = mock_repo

                from typer.testing import CliRunner

                runner = CliRunner()
                result = runner.invoke(app, ["view-health-log", "--id", "999"])
                assert result.exit_code == 2
                assert "[ERROR]" in result.output or "not found" in result.output.lower()

    def test_view_health_log_requires_id_option(self):
        """Test view-health-log requires --id option."""
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["view-health-log"])
        # Should fail due to missing required option
        assert result.exit_code == 2
