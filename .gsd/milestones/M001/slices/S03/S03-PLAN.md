# S03: Health Log Query Commands

**Goal:** User can list and view health log entries via CLI
**Demo:** User can list and view health log entries via CLI

## Must-Haves

- User can run `run-intelligence list-health-logs` to see all health log entries and `run-intelligence view-health-log --id <entry_id>` to view a specific entry

## Proof Level

- This slice proves: integration

## Integration Closure

Uses existing HealthLogRepository.get_entries() and get_entry() methods - no new repository code needed

## Verification

- Run the task and slice verification checks for this slice.

## Tasks

- [x] **T01: Implemented list-health-logs and view-health-log CLI commands** `est:30m`
  Add two new CLI commands to cli.py: (1) list-health-logs with --limit option that calls HealthLogRepository.get_entries(limit) and prints formatted list, (2) view-health-log with --id option that calls HealthLogRepository.get_entry(id) and prints entry details. Follow existing CLI patterns: exit code 2 for validation errors (invalid ID), exit code 1 for database errors, use sys.stdout.write() and sys.stderr.write() with [ERROR] prefixes.
  - Files: `/home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/src/run_intelligence/cli.py`
  - Verify: python3 -m run_intelligence list-health-logs --help && python3 -m run_intelligence view-health-log --help

- [x] **T02: Added CLI tests for list-health-logs and view-health-log commands** `est:30m`
  Add tests to tests/test_health_log/test_cli.py covering: (1) list-health-logs shows entries, (2) list-health-logs handles empty list, (3) view-health-log shows entry details, (4) view-health-log with invalid ID returns exit code 2 with error message. Follow existing test patterns using typer.testing.CliRunner and mocking.
  - Files: `/home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/tests/test_health_log/test_cli.py`
  - Verify: python3 -m pytest tests/test_health_log/test_cli.py -v

## Files Likely Touched

- /home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/src/run_intelligence/cli.py
- /home/lpintos/.gsd/projects/e51dd9a6b959/worktrees/M001/tests/test_health_log/test_cli.py
