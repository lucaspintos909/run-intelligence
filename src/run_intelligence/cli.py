"""CLI entry point for Run Intelligence."""

import typer

app = typer.Typer(
    name="run-intelligence",
    help="Running intelligence system with asthma-aware metrics",
)


@app.callback()
def main(
    mode: str = typer.Option(None, "--mode", "-m", help="Output mode"),
) -> None:
    """Main CLI entry point."""
    if mode:
        typer.echo(f"Mode: {mode}")


@app.command()
def process(
    file: str = typer.Option(..., "--file", "-f", help="FIT file to process"),
) -> None:
    """Process a FIT file."""
    typer.echo(f"Processing: {file}")


@app.command()
def batch(
    directory: str = typer.Option(..., "--directory", "-d", help="Directory with FIT files"),
) -> None:
    """Batch process FIT files."""
    typer.echo(f"Batch processing: {directory}")


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
