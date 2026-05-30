"""CLI entry point for Run Intelligence."""

import sys
import traceback
from datetime import date as date_type, datetime
from pathlib import Path
from typing import Optional

import typer
from typer import Exit

from run_intelligence.pipeline.fit_parser import FitParseError
from run_intelligence.pipeline.metrics import MetricCalculationError
from run_intelligence.pipeline.runner import process_file

VERSION = "0.1.0"

app = typer.Typer(
    name="run-intelligence",
    help="Run Intelligence — asthma-aware running analytics and coaching CLI",
    invoke_without_command=True,
)


def _handle_process(file: str, verbose: bool, dry_run: bool) -> None:
    """Shared handler for process execution and error reporting."""
    try:
        process_file(file, verbose=verbose, dry_run=dry_run)
        raise Exit(code=0)
    except FitParseError as e:
        sys.stderr.write(f"[PIPELINE_ERROR] cli: {e}\n")
        raise Exit(code=1)
    except MetricCalculationError as e:
        sys.stderr.write(f"[PIPELINE_ERROR] cli: {e}\n")
        raise Exit(code=1)
    except Exception as e:
        sys.stderr.write(f"[PIPELINE_ERROR] cli: Unexpected error: {e}\n")
        sys.stderr.write(traceback.format_exc())
        raise Exit(code=1)


def _handle_batch(directory: str, verbose: bool, dry_run: bool) -> None:
    """Shared handler for batch execution and error reporting."""
    from run_intelligence.pipeline.runner import (
        _format_batch_summary,
        process_directory,
    )

    try:
        result = process_directory(directory, verbose=verbose, dry_run=dry_run)
        summary = _format_batch_summary(result)
        sys.stdout.write(summary)

        if result.success_count == 0:
            raise Exit(code=1)
        raise Exit(code=0)
    except ValueError as e:
        sys.stderr.write(f"[CLI_ERROR] {e}\n")
        if "does not exist" in str(e):
            raise Exit(code=1)
        raise Exit(code=2)
    except Exit:
        raise
    except Exception as e:
        sys.stderr.write(f"[CLI_ERROR] Batch processing failed: {e}\n")
        sys.stderr.write(traceback.format_exc())
        raise Exit(code=1)


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
    process: Optional[str] = typer.Option(
        None, "--process", help="Path to .fit file to process"
    ),
    batch: Optional[str] = typer.Option(
        None, "--batch", help="Process all .fit files in directory"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed processing output"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Process without writing to database"
    ),
) -> None:
    """Main CLI entry point for Run Intelligence.

    Run `run-intelligence --help` for available commands.
    """
    if version:
        sys.stdout.write(f"run-intelligence {VERSION}\n")
        raise Exit(code=0)

    if ctx.invoked_subcommand is None:
        if batch:
            _handle_batch(batch, verbose=verbose, dry_run=dry_run)
        elif process:
            _handle_process(process, verbose=verbose, dry_run=dry_run)
        else:
            sys.stdout.write(ctx.get_help())
            raise Exit(code=0)


@app.command()
def process(
    file_arg: Optional[str] = typer.Argument(None, help="Path to .fit file to process"),
    file: Optional[str] = typer.Option(
        None, "--file", "-f", help="Path to .fit file to process"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed processing output"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Process without writing to database"
    ),
) -> None:
    """Process a single .fit file through the pipeline.

    Extracts standard and asthma-aware metrics, validates data quality,
    and persists to the database.

    Example:
        run-intelligence process morning_run.fit --verbose
        run-intelligence process --file path/to/run.fit --dry-run

    Exit codes:
        0: Success
        1: Pipeline or processing error
        2: Invalid arguments (missing file)
    """
    actual_file = file or file_arg
    if not actual_file:
        sys.stderr.write(
            "[CLI_ERROR] Missing file path. Provide positional argument or --file/-f.\n"
        )
        raise Exit(code=2)
    _handle_process(actual_file, verbose=verbose, dry_run=dry_run)


@app.command()
def batch(
    directory: str = typer.Argument(..., help="Directory containing .fit files"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed per-file output"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Process without writing to database"
    ),
) -> None:
    """Process all .fit files in a directory.

    Recursively scans the directory for .fit files and processes each one.
    Produces an aggregate summary of successes and failures.

    Example:
        run-intelligence batch ./runs/2026 --verbose
        run-intelligence batch ./data --dry-run

    Exit codes:
        0: Success (at least one file processed)
        1: All files failed or directory invalid
        2: Invalid arguments
    """
    _handle_batch(directory, verbose=verbose, dry_run=dry_run)


@app.command()
def log_health(
    ctx: typer.Context,
    date: Optional[str] = typer.Option(
        None, "--date", help="Date (YYYY-MM-DD), defaults to today"
    ),
    peak_flow: Optional[int] = typer.Option(
        None, "--peak-flow", help="Peak flow reading (L/min)"
    ),
    sleep_quality: Optional[int] = typer.Option(
        None, "--sleep-quality", min=1, max=5, help="Sleep quality 1-5"
    ),
    post_run_rpe: Optional[int] = typer.Option(
        None, "--post-run-rpe", min=1, max=10, help="Post-run RPE 1-10"
    ),
    asthma_symptoms: Optional[int] = typer.Option(
        None, "--asthma-symptoms", min=0, max=5, help="Asthma symptoms 0-5"
    ),
    saba_use: Optional[bool] = typer.Option(
        None, "--saba-use", help="Rescue inhaler used (true/false)"
    ),
    notes: Optional[str] = typer.Option(None, "--notes", help="Additional notes"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show saved field values"
    ),
) -> None:
    """Log a health entry with asthma symptoms, peak flow, and rescue inhaler use.

    Example:
        run-intelligence log-health --date 2026-05-21 --peak-flow 450 --asthma-symptoms 2
        run-intelligence log-health --post-run-rpe 7 --sleep-quality 3 --verbose

    Exit codes:
        0: Success
        1: Database or write error
        2: Invalid arguments
    """
    from run_intelligence.db.session import _get_engine
    from run_intelligence.db.repository import AuditLogRepository, HealthLogRepository
    from sqlalchemy.orm import sessionmaker

    # Handle saba_use: if not provided via flag, prompt with typer.confirm()
    # Check if we're in interactive mode (no health fields provided via CLI)
    # If no health-related arguments are provided, prompt interactively for each field
    interactive_mode = (
        date is None
        and peak_flow is None
        and sleep_quality is None
        and post_run_rpe is None
        and asthma_symptoms is None
        and saba_use is None
        and notes is None
    )

    if interactive_mode:
        # Prompt for date (optional, defaults to today)
        date_input = typer.prompt("Date (YYYY-MM-DD), or press Enter for today:", default="")
        date = date_input if date_input.strip() else None

        # Prompt for numeric fields with validation
        peak_flow_input = typer.prompt("Peak flow reading (L/min), or press Enter to skip:", default="")
        peak_flow = int(peak_flow_input) if peak_flow_input.strip() else None

        sleep_quality_input = typer.prompt("Sleep quality (1-5), or press Enter to skip:", default="")
        sleep_quality = int(sleep_quality_input) if sleep_quality_input.strip() else None

        post_run_rpe_input = typer.prompt("Post-run RPE (1-10), or press Enter to skip:", default="")
        post_run_rpe = int(post_run_rpe_input) if post_run_rpe_input.strip() else None

        asthma_symptoms_input = typer.prompt("Asthma symptoms (0-5), or press Enter to skip:", default="")
        asthma_symptoms = int(asthma_symptoms_input) if asthma_symptoms_input.strip() else None

        # saba_use uses typer.confirm() for boolean
        saba_use = typer.confirm("Rescue inhaler/SABA used?", default=None)

        notes_input = typer.prompt("Additional notes (optional, press Enter to skip):", default="")
        notes = notes_input.strip() if notes_input.strip() else None

    try:
        parsed_date = date_type.today()
        if date:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                sys.stderr.write(
                    f"[VALIDATION_ERROR] Invalid date format: {date}. Use YYYY-MM-DD.\n"
                )
                raise Exit(code=2)

        engine = _get_engine()
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        try:
            audit_logger = AuditLogRepository(session=session)
            health_repo = HealthLogRepository(
                session=session, audit_logger=audit_logger
            )

            entry = health_repo.create_entry(
                entry_date=parsed_date,
                peak_flow=peak_flow,
                sleep_quality=sleep_quality,
                post_run_rpe=post_run_rpe,
                asthma_symptoms=asthma_symptoms,
                saba_use=saba_use,
                notes=notes,
            )

            if verbose:
                sys.stdout.write(f"[LOG_HEALTH] Saved entry for {parsed_date}\n")
                if peak_flow is not None:
                    sys.stdout.write(f"  Peak flow: {peak_flow} L/min\n")
                if sleep_quality is not None:
                    sys.stdout.write(f"  Sleep quality: {sleep_quality}/5\n")
                if post_run_rpe is not None:
                    sys.stdout.write(f"  Post-run RPE: {post_run_rpe}/10\n")
                if asthma_symptoms is not None:
                    sys.stdout.write(f"  Asthma symptoms: {asthma_symptoms}/5\n")
                if saba_use is not None:
                    sys.stdout.write(f"  SABA use: {'yes' if saba_use else 'no'}\n")
                if notes:
                    sys.stdout.write(f"  Notes: {notes}\n")
                sys.stdout.write(f"  Entry ID: {entry.id}\n")
            else:
                sys.stdout.write(f"Logged: {parsed_date}")
                fields = []
                if peak_flow is not None:
                    fields.append(f"peak_flow={peak_flow}")
                if sleep_quality is not None:
                    fields.append(f"sleep={sleep_quality}")
                if post_run_rpe is not None:
                    fields.append(f"rpe={post_run_rpe}")
                if asthma_symptoms is not None:
                    fields.append(f"symptoms={asthma_symptoms}")
                if saba_use is not None:
                    fields.append(f"saba={'yes' if saba_use else 'no'}")
                if fields:
                    sys.stdout.write(f" ({', '.join(fields)})")
                sys.stdout.write("\n")

        finally:
            session.close()
    except Exit:
        raise
    except Exception as e:
        sys.stderr.write(f"[LOG_HEALTH_ERROR] {e}\n")
        raise Exit(code=1)


@app.command()
def report(
    start_date: str = typer.Option(..., "--start", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "--end", help="End date (YYYY-MM-DD)"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Write report to file instead of stdout"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show generation details"
    ),
) -> None:
    """Generate a medical report for the specified date range.

    Produces a summary of runs, health logs, and wellness trends.

    Example:
        run-intelligence report --start 2026-05-01 --end 2026-05-31
        run-intelligence report --start 2026-05-01 --end 2026-05-31 --output may_report.md

    Exit codes:
        0: Success
        1: Generation or write error
        2: Invalid arguments
    """
    from run_intelligence.db.session import _get_engine
    from run_intelligence.db.repository import (
        AuditLogRepository,
        RunRepository,
        HealthLogRepository,
    )
    from sqlalchemy.orm import sessionmaker

    try:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError as e:
            sys.stderr.write(
                f"[REPORT_ERROR] Invalid date format: {e}. Use YYYY-MM-DD.\n"
            )
            raise Exit(code=2)

        if start > end:
            sys.stderr.write(
                "[REPORT_ERROR] Start date must be before or equal to end date.\n"
            )
            raise Exit(code=2)

        engine = _get_engine()
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        try:
            audit_logger = AuditLogRepository(session=session)
            run_repo = RunRepository(session=session, audit_logger=audit_logger)
            health_repo = HealthLogRepository(
                session=session, audit_logger=audit_logger
            )

            if verbose:
                sys.stdout.write("[REPORT] Fetching runs...\n")

            runs = run_repo.get_runs(limit=1000)
            if len(runs) == 1000 and verbose:
                sys.stdout.write(
                    "[REPORT] Warning: run query capped at 1000 results.\n"
                )
            runs_in_range = [
                r
                for r in runs
                if r.processed_at is not None and start <= r.processed_at.date() <= end
            ]

            if verbose:
                sys.stdout.write(
                    f"[REPORT] Found {len(runs_in_range)} runs in date range\n"
                )
                sys.stdout.write("[REPORT] Fetching health logs...\n")

            health_entries = health_repo.get_entries(limit=1000)
            if len(health_entries) == 1000 and verbose:
                sys.stdout.write(
                    "[REPORT] Warning: health log query capped at 1000 results.\n"
                )
            health_in_range = [h for h in health_entries if start <= h.date <= end]

            if verbose:
                sys.stdout.write(
                    f"[REPORT] Found {len(health_in_range)} health entries in date range\n"
                )
                sys.stdout.write("[REPORT] Generating report content...\n")

            lines = []
            lines.append(f"# Medical Report: {start_date} to {end_date}")
            lines.append("")
            lines.append(
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            lines.append("")
            lines.append("## Run Summary")
            lines.append(f"- Total runs in period: {len(runs_in_range)}")
            if runs_in_range:
                total_distance = 0
                for run in runs_in_range:
                    if run.raw_metrics_json:
                        import json

                        try:
                            metrics = json.loads(run.raw_metrics_json)
                            dist = metrics.get("distance", 0)
                            if dist is not None:
                                total_distance += dist
                        except Exception:
                            pass
                lines.append(f"- Approximate total distance: {total_distance:.1f} m")
            lines.append("")
            lines.append("## Health Summary")
            lines.append(f"- Total health entries in period: {len(health_in_range)}")
            if health_in_range:
                peak_flow_values = [
                    h.peak_flow for h in health_in_range if h.peak_flow is not None
                ]
                if peak_flow_values:
                    avg_peak_flow = sum(peak_flow_values) / len(peak_flow_values)
                    lines.append(f"- Average peak flow: {avg_peak_flow:.0f} L/min")
                saba_count = sum(1 for h in health_in_range if h.saba_use)
                lines.append(f"- SABA use days: {saba_count}")
            lines.append("")
            lines.append("## Recommendations")
            lines.append("- Continue monitoring asthma symptoms before and after runs")
            lines.append("- Maintain regular peak flow logging for trend analysis")
            if health_in_range and any(
                h.asthma_symptoms and h.asthma_symptoms > 3 for h in health_in_range
            ):
                lines.append(
                    "- WARNING: Multiple high-symptom days detected - consider adjusting training intensity"
                )
            lines.append("")

            report_content = "\n".join(lines)

            if output:
                try:
                    Path(output).write_text(report_content, encoding="utf-8")
                    sys.stdout.write(f"Report written to {output}\n")
                except OSError as e:
                    sys.stderr.write(
                        f"[REPORT_ERROR] Failed to write to {output}: {e}\n"
                    )
                    raise Exit(code=1)
            else:
                sys.stdout.write(report_content)
                sys.stdout.write("\n")

        finally:
            session.close()
    except Exit:
        raise
    except Exception as e:
        sys.stderr.write(f"[REPORT_ERROR] {e}\n")
        raise Exit(code=1)


@app.command()
def purge(
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Confirm irreversible data deletion — THIS CANNOT BE UNDONE",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show what is being deleted"
    ),
) -> None:
    """Purge all user data from the system. Requires --confirm.

    Warning: This deletes ALL runs, health logs, profiles, conversation history,
    and audit logs. This action CANNOT be undone.

    Example:
        run-intelligence purge --confirm
        run-intelligence purge --confirm --verbose

    Exit codes:
        0: Success (data purged) or graceful no-op (no --confirm)
        1: Deletion error
        2: Invalid arguments (none in this case, but reserved)
    """
    if not confirm:
        sys.stdout.write(
            "Warning: This will delete ALL your data (runs, health logs, profiles, history).\n"
        )
        sys.stdout.write("Use --confirm to proceed. This action CANNOT be undone.\n")
        raise Exit(code=0)

    from run_intelligence.db.session import _get_engine
    from sqlalchemy import text

    try:
        engine = _get_engine()

        with engine.connect() as conn:
            with conn.begin():
                if verbose:
                    sys.stdout.write("[PURGE] Deleting child tables...\n")
                conn.execute(text("DELETE FROM health_log"))
                if verbose:
                    sys.stdout.write("[PURGE] Health log table: cleared\n")
                conn.execute(text("DELETE FROM conversation_history"))
                if verbose:
                    sys.stdout.write("[PURGE] Conversation history table: cleared\n")
                conn.execute(text("DELETE FROM runner_metrics_history"))
                if verbose:
                    sys.stdout.write("[PURGE] Runner metrics history table: cleared\n")
                conn.execute(text("DELETE FROM audit_log"))
                if verbose:
                    sys.stdout.write("[PURGE] Audit log table: cleared\n")
                if verbose:
                    sys.stdout.write("[PURGE] Deleting runs...\n")
                conn.execute(text("DELETE FROM runs"))
                if verbose:
                    sys.stdout.write("[PURGE] Runs table: cleared\n")

        sys.stdout.write("All data has been purged.\n")
    except Exception as e:
        sys.stderr.write(f"[PURGE_ERROR] Failed to purge data: {e}\n")
        raise Exit(code=1)


if __name__ == "__main__":
    app()
