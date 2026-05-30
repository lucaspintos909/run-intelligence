---
id: T02
parent: S02
milestone: M001
key_files:
  - src/run_intelligence/cli.py
key_decisions:
  - Used RunRepository.get_runs(limit=100) to list available runs
  - Displayed distance from raw_metrics_json when available
  - Used typer.confirm() for yes/no prompt and typer.prompt() with validation loop for run ID selection
duration: 
verification_result: passed
completed_at: 2026-05-30T18:24:10.942Z
blocker_discovered: false
---

# T02: Added interactive run selection prompt to log-health command

**Added interactive run selection prompt to log-health command**

## What Happened

In interactive mode (no CLI arguments provided), after prompting for health fields (date, peak_flow, sleep_quality, post_run_rpe, asthma_symptoms, saba_use, notes), the CLI now queries available runs using RunRepository.get_runs() and displays them in a table format showing ID, Date, and Distance (extracted from raw_metrics_json). The user is then prompted to confirm if they want to associate with a run. If yes, they can enter a run ID with validation to ensure the run exists. If no runs exist, a helpful message is shown directing users to process a file first. The implementation handles edge cases like invalid input and empty run lists.

## Verification

Ran python3 -m run_intelligence log-health --help to verify CLI works. All 40 health_log tests pass. The interactive run selection is triggered only when no arguments are provided to the command (interactive mode).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -m run_intelligence log-health --help` | 0 | pass | 100ms |
| 2 | `python3 -m pytest tests/test_health_log/ -v --tb=short` | 0 | pass | 250ms |

## Deviations

None

## Known Issues

None

## Files Created/Modified

- `src/run_intelligence/cli.py`
