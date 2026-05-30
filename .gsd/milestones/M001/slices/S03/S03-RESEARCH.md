# S03 — Research: Health Log Query Commands

**Date:** 2026-05-30

## Summary

S03 adds CLI commands to list and view health log entries. The backend already supports this via `HealthLogRepository.get_entry()` and `HealthLogRepository.get_entries()` in `src/run_intelligence/db/repository.py`. The slice needs to expose these through new Typer commands following the existing CLI patterns established in `src/run_intelligence/cli.py`.

The `log_health` command (added in S01/S02) uses Typer with interactive prompts. The new query commands should follow the same patterns: exit code 2 for validation errors, consistent output formatting, and proper database session handling.

## Recommendation

Implement two new CLI commands in `src/run_intelligence/cli.py`:

1. **`list-health-logs`** — Lists health log entries with optional limit/date filtering
2. **`view-health-log`** — Shows a specific health log entry by ID

The existing repository methods provide:
- `get_entry(entry_id)` — returns `Optional[HealthLog]`
- `get_entries(limit=100)` — returns `List[HealthLog]` ordered by date desc

No new repository methods required; the slice only needs CLI wrapper code.

## Implementation Landscape

### Key Files

| File | Purpose |
|------|---------|
| `src/run_intelligence/cli.py` | Add new commands here (around line 400, after `log_health`) |
| `src/run_intelligence/db/repository.py` | Already has `HealthLogRepository.get_entry()` and `get_entries()` |
| `src/run_intelligence/db/models.py` | `HealthLog` model with fields: id, date, peak_flow, sleep_quality, post_run_rpe, asthma_symptoms, saba_use, notes, run_id |

### Build Order

1. Add `list-health-logs` command using existing `HealthLogRepository.get_entries(limit)`
2. Add `view-health-log` command using existing `HealthLogRepository.get_entry(id)`
3. Add CLI tests for both commands

### Verification Approach

- `python -m run_intelligence list-health-logs --help` shows command
- `python -m run_intelligence list-health-logs` lists entries
- `python -m run_intelligence view-health-log --id 1` shows entry details
- `python -m run_intelligence view-health-log --id 99999` returns exit code 2 with error
- Tests in `tests/test_health_log/test_cli.py` pass

## Patterns Established

From prior slices (stored in memory):

- **CLI validation pattern**: Exit code 2 for invalid arguments, exit code 1 for database errors
- **Interactive CLI**: Uses `typer.prompt()` for text, `typer.confirm()` for booleans
- **Repository pattern**: Uses `HealthLogRepository` with session/audit_logger injection
- **Output format**: Uses `sys.stdout.write()` and `sys.stderr.write()` with prefixed messages

## Constraints

- No new dependencies — uses existing SQLAlchemy/Typer
- Must follow existing CLI patterns (exit codes, error messages)
- HealthLogRepository already has needed methods; no repository changes needed

## Common Pitfalls

- **Missing session close** — Always use try/finally for database sessions
- **Invalid entry ID** — Should return exit code 2 with clear error message (matching run validation pattern)
- **Empty list** — Should print informative message, not crash

## Don't Hand-Roll

| Problem | Existing Solution |
|---------|------------------|
| Listing entries | `HealthLogRepository.get_entries(limit)` |
| Getting single entry | `HealthLogRepository.get_entry(id)` |
| Database session | Same pattern as `log_health` command |

## Skills Discovered

No additional skills required. The work is straightforward CLI wrapper code using existing patterns.

## Sources

- CLI pattern: `src/run_intelligence/cli.py` — existing commands (process, batch, log_health)
- Repository: `src/run_intelligence/db/repository.py` — HealthLogRepository class
- Model: `src/run_intelligence/db/models.py` — HealthLog table definition
