# S02: Run Association

**Goal:** Add --associate-run option to log-health command so users can associate health log entries with existing runs via CLI flag or interactive selection
**Demo:** User can associate a health log entry with an existing run via `--associate-run <id>`

## Must-Haves

- User can run `python -m run_intelligence log-health --associate-run <id>` and link a health entry to an existing run. In interactive mode, user is prompted to select from available runs.

## Proof Level

- This slice proves: integration

## Integration Closure

This slice composes the existing HealthLogRepository.create_entry(run_id=) capability with the CLI, completing the run-association feature wiring. S03 (query commands) will consume this new capability.

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Added --associate-run CLI option with validation for linking health entries to runs** `est:30m`
  Add --associate-run option to log_health command in cli.py. Update interactive_mode detection to include associate_run parameter. Validate run exists via RunRepository.get_run() before creating entry. Pass run_id to create_entry() - repository already supports this.
  - Files: `/home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/src/run_intelligence/cli.py`
  - Verify: python3 -m run_intelligence log-health --help

- [x] **T02: Added interactive run selection prompt to log-health command** `est:30m`
  In interactive mode, if --associate-run not provided, prompt user to select from available runs. Show run IDs, dates, and optionally distance. Handle case where no runs exist (show helpful message). Uses RunRepository.get_runs() to list available runs.
  - Files: `/home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/src/run_intelligence/cli.py`
  - Verify: python3 -m run_intelligence log-health --help

- [x] **T03: Added CLI tests for run association in log-health command** `est:30m`
  Add tests to test_cli.py: test with valid run ID passes, test with invalid run ID shows error and exits 2, test with no runs shows appropriate message, test interactive mode run selection.
  - Files: `/home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/tests/test_health_log/test_cli.py`
  - Verify: python3 -m pytest tests/test_health_log/test_cli.py -v -k run --tb=short

## Files Likely Touched

- /home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/src/run_intelligence/cli.py
- /home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/tests/test_health_log/test_cli.py
