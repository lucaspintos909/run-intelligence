# S01 — Research: Interactive Health Logging CLI

**Date:** 2026-05-30

## Summary

The Interactive Health Logging CLI slice has **partial implementation**. The core infrastructure exists:
- `log_health` command in `cli.py` with CLI flag options
- `HealthLog` model in `db/models.py` (includes `run_id` for future association)
- `HealthLogRepository` in `db/repository.py` with full CRUD + `link_to_run()`

The **missing piece** is **interactive prompting** when users run `python -m run_intelligence log-health` without arguments. Currently the CLI requires all fields as explicit flags (e.g., `--peak-flow 450`), but the slice requirement calls for interactive input prompts.

## Recommendation

Implement Typer's built-in interactive prompts using `prompt=True` pattern on CLI options. This is the recommended approach because:
1. It aligns with Typer's native interactive CLI pattern
2. Allows non-interactive scripting (use flags) AND interactive use (no flags = prompts)
3. No additional dependencies needed (already uses typer[all])
4. Follows existing CLI patterns in the codebase

## Implementation Landscape

### Key Files

- `src/run_intelligence/cli.py` — Contains `log_health()` command; needs `prompt=True` added to options for interactive mode
- `src/run_intelligence/db/models.py` — HealthLog model already defined with all fields (date, peak_flow, sleep_quality, post_run_rpe, asthma_symptoms, saba_use, notes, run_id)
- `src/run_intelligence/db/repository.py` — HealthLogRepository has `create_entry()` that accepts all fields; ready for use
- `tests/test_health_log/` — Empty; needs unit tests added

### Build Order

1. **First Proof**: Add interactive prompts to `log_health` command in cli.py using `prompt=True` pattern
   - Convert optional CLI options from `Optional[...]` to have `prompt=True` fallback
   - Verify interactive flow works: `python -m run_intelligence log-health` prompts for each field

2. **Input Validation**: Add Pydantic schema for health log input (optional enhancement for type safety)
   - Current CLI has Typer's min/max validation on options
   - Could add `HealthLogInput` Pydantic model for structured validation

3. **Tests**: Create unit + integration tests
   - `tests/test_health_log/test_cli.py` — Test interactive prompts, validation
   - `tests/test_health_log/test_repository.py` — Test CRUD operations

### Verification Approach

```bash
# Interactive mode (no args) - should prompt for input
python -m run_intelligence log-health

# Non-interactive mode (with args) - existing behavior
python -m run_intelligence log-health --peak-flow 450 --sleep-quality 4

# Verify data persists
python -m run_intelligence report --start 2026-01-01 --end 2026-12-31
```

## Constraints

- **Python 3.11+** — Required by project
- **Typer with rich** — Already in dependencies (`typer[all]` includes rich for styled prompts)
- **SQLAlchemy 2.0** — Already used for persistence
- **No external APIs** — Local-only CLI operation

## Common Pitfalls

- **Prompt for boolean fields** — `saba_use` as bool needs special handling in prompts; use `typer.confirm()`
- **Empty input handling** — Should allow skipping fields (press Enter to skip)
- **Ctrl+C during prompt** — Should gracefully exit without partial writes

## Open Risks

- **No existing tests** for health_log module — need to create from scratch
- **Interactive prompts not verified** with actual CLI invocation — need integration testing
- **Run association** is S02 scope but HealthLog model already has `run_id` — may need validation that run exists

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Typer interactive prompts | Built-in (typer[all]) | Available |
| Pydantic validation | Already in dependencies | Available |

## Sources

- Typer prompt documentation: https://github.com/fastapi/typer/blob/master/docs/tutorial/prompt.md
- Typer options with prompt: https://github.com/fastapi/typer/blob/master/docs/tutorial/options/prompt.md
