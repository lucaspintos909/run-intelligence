"""CLI entry point for Run Intelligence."""

import sys
import traceback
from typing import Optional

import typer

from run_intelligence.pipeline.fit_parser import FitParseError
from run_intelligence.pipeline.metrics import MetricCalculationError
from run_intelligence.pipeline.runner import process_file

app = typer.Typer(
    name="run-intelligence",
    help="Running intelligence system with asthma-aware metrics",
    invoke_without_command=True,
)


def _handle_process(file: str, verbose: bool, dry_run: bool) -> None:
    """Shared handler for process execution and error reporting."""
    try:
        process_file(file, verbose=verbose, dry_run=dry_run)
        raise typer.Exit(code=0)
    except FitParseError as e:
        sys.stderr.write(f"[PIPELINE_ERROR] cli: {e}\n")
        raise typer.Exit(code=1)
    except MetricCalculationError as e:
        sys.stderr.write(f"[PIPELINE_ERROR] cli: {e}\n")
        raise typer.Exit(code=1)
    except Exception as e:
        sys.stderr.write(f"[PIPELINE_ERROR] cli: Unexpected error: {e}\n")
        sys.stderr.write(traceback.format_exc())
        raise typer.Exit(code=1)


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
            raise typer.Exit(code=1)
        raise typer.Exit(code=0)
    except ValueError as e:
        sys.stderr.write(f"[CLI_ERROR] {e}\n")
        if "does not exist" in str(e):
            raise typer.Exit(code=1)
        raise typer.Exit(code=2)
    except typer.Exit:
        raise
    except Exception as e:
        sys.stderr.write(f"[CLI_ERROR] Batch processing failed: {e}\n")
        sys.stderr.write(traceback.format_exc())
        raise typer.Exit(code=1)


@app.callback()
def main(
    ctx: typer.Context,
    process: Optional[str] = typer.Option(None, "--process", help="Path to .fit file to process"),
    batch: Optional[str] = typer.Option(None, "--batch", help="Process all .fit files in directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed processing output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Process without writing to database"),
) -> None:
    """Main CLI entry point for Run Intelligence."""
    if ctx.invoked_subcommand is None:
        if batch:
            _handle_batch(batch, verbose=verbose, dry_run=dry_run)
        elif process:
            _handle_process(process, verbose=verbose, dry_run=dry_run)
        else:
            typer.echo(ctx.get_help())
            raise typer.Exit(code=0)


@app.command()
def process(
    file_arg: Optional[str] = typer.Argument(None, help="Path to .fit file to process"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Path to .fit file to process"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed processing output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Process without writing to database"),
) -> None:
    """Process a single .fit file through the pipeline."""
    actual_file = file or file_arg
    if not actual_file:
        sys.stderr.write("[PIPELINE_ERROR] cli: Missing file path. Provide a positional argument or --file/-f.\n")
        raise typer.Exit(code=2)
    _handle_process(actual_file, verbose=verbose, dry_run=dry_run)


@app.command()
def batch(
    directory: str = typer.Argument(..., help="Directory containing .fit files"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed per-file output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Process without writing to database"),
) -> None:
    """Process all .fit files in a directory."""
    _handle_batch(directory, verbose=verbose, dry_run=dry_run)


@app.command()
def log_health(
    date: str = typer.Option(..., "--date", help="Date (YYYY-MM-DD)"),
    symptom: str = typer.Option(..., "--symptom", help="Symptom description"),
    severity: int = typer.Option(3, "--severity", min=1, max=5, help="Severity 1-5"),
) -> None:
    """Log health information."""
    typer.echo(f"Logged: {date} - {symptom} (severity: {severity})")


@app.command()
def report(
    start_date: str = typer.Option(..., "--start", help="Start date"),
    end_date: str = typer.Option(..., "--end", help="End date"),
) -> None:
    """Generate a report."""
    typer.echo(f"Report: {start_date} to {end_date}")


@app.command()
def purge(
    confirm: bool = typer.Option(False, "--confirm", help="Confirm data purge"),
) -> None:
    """Purge all data."""
    if confirm:
        typer.echo("Data purged")
    else:
        typer.echo("Use --confirm to purge data")


if __name__ == "__main__":
    app()
