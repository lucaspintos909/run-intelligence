# Story 1.8: Batch Processing

Status: review

## Story ID & Key

- **Story ID:** 1.8
- **Story Key:** 1-8-batch-processing
- **Epic:** Epic 1: Project Foundation & Data Pipeline
- **FRs Covered:** FR7 (batch process all .fit files in directory), FR41 (batch files independently — one corrupt file doesn't stop), FR39 (dry-run mode), FR42 (stdout/stderr separation)
- **NFRs Covered:** NFR1 (≤5s per file), NFR4 (batch independence), NFR20 (stdout/stderr separation)

## Story

As a user,
I want to process all .fit files in a directory,
So that I can ingest my complete run history efficiently.

## Acceptance Criteria

### AC1: Batch Processing via CLI

**Given** a directory with multiple .fit files
**When** I run `python -m run_intelligence --batch ./runs/`
**Then** each valid .fit file is processed independently
**And** one corrupt file does NOT stop the batch
**And** errors are logged to stderr with file identification
**And** successful runs are persisted to the database

### AC2: Batch Dry-Run Mode

**Given** batch processing
**When** I run `python -m run_intelligence --batch ./runs/ --dry-run`
**Then** all files are validated without writing to the database
**And** I see summary: N files would be processed, M errors

### AC3: Batch Verbose Mode

**Given** batch processing
**When** I run `python -m run_intelligence --batch ./runs/ --verbose`
**Then** I see detailed per-file output: each pipeline stage, metric calculations, validation results for each file
**And** aggregate summary shows total files, successes, failures, processing time

### AC4: Batch Error Independence (NFR4)

**Given** a batch containing one invalid .fit file and multiple valid files
**When** batch processing runs
**Then** the invalid file produces an error logged to stderr with its filename
**And** all valid files are still processed successfully
**And** the exit code is 0 (success) if at least one file processed successfully
**And** the exit code is 1 (error) only if ALL files fail

### AC5: Batch Output Separation (NFR20)

**Given** batch processing with mixed valid/invalid files
**When** processing completes
**Then** aggregate summary and per-file success indicators go to stdout
**And** per-file errors and validation warnings go to stderr with file identification
**And** the format is: `[BATCH_ERROR] {filename}: {message}` for errors
**And** the format is: `[VALIDATION_WARNING] {filename}: {details}` for warnings

### AC6: Performance

**Given** a directory with N typical .fit files (each ≤2 hours, ≤1000 records)
**When** batch processing runs
**Then** total processing time is approximately N × ≤5 seconds (each file independently within NFR1)
**And** files are processed sequentially (not parallel — single-user MVP, SQLite single-writer)

## Tasks / Subtasks

- [x] Task 1: Implement `process_directory()` in `pipeline/runner.py` (AC: #1, #3, #4, #5, #6)
  - [x] Subtask 1.1: Implement `process_directory(directory_path: str, verbose: bool = False, dry_run: bool = False) -> BatchResult` that scans directory for .fit files and processes each independently
  - [x] Subtask 1.2: Implement per-file error catching: try/except around `process_file()` call, log error to stderr with filename, continue to next file
  - [x] Subtask 1.3: Implement `_format_batch_summary(result: BatchResult) -> str` for stdout aggregate output
  - [x] Subtask 1.4: Implement `_format_batch_error(file_path: str, error: Exception) -> str` for stderr error output with `[BATCH_ERROR]` prefix
  - [x] Subtask 1.5: Create `BatchResult` dataclass/Pydantic model with: total_files, success_count, failure_count, failed_files list, total_elapsed_seconds
  - [x] Subtask 1.6: Implement directory scanning: list all `.fit` files (case-insensitive: `.fit`, `.FIT`) in directory, sorted alphabetically for determinism
  - [x] Subtask 1.7: Pass `verbose` and `dry_run` flags through to each `process_file()` call

- [x] Task 2: Update `cli.py` with `batch` command (AC: #1, #2, #3, #4, #5)
  - [x] Subtask 2.1: Add `batch` subcommand with `directory: str` positional argument
  - [x] Subtask 2.2: Add `--verbose` / `-v` flag to batch command
  - [x] Subtask 2.3: Add `--dry-run` flag to batch command
  - [x] Subtask 2.4: Implement exit code logic: 0 if ≥1 success, 1 if all fail, 2 for invalid args
  - [x] Subtask 2.5: Implement stdout/stderr separation: summary → stdout, errors → stderr
  - [x] Subtask 2.6: Add `--batch` as global flag on `main()` callback (invoke_without_command=True) for backward compatibility with `python -m run_intelligence --batch ./runs/`

- [x] Task 3: Update `pipeline/__init__.py` exports (AC: #1)
  - [x] Subtask 3.1: Add `process_directory` and `BatchResult` to `__all__`

- [x] Task 4: Add tests for batch processing (AC: #1, #2, #3, #4, #5, #6)
  - [x] Subtask 4.1: Test `process_directory()` with all valid .fit files → all processed, BatchResult shows 0 failures
  - [x] Subtask 4.2: Test `process_directory()` with one corrupt file → valid files still processed, BatchResult shows 1 failure with filename
  - [x] Subtask 4.3: Test `process_directory()` with all corrupt files → BatchResult shows all failures, no crashes
  - [x] Subtask 4.4: Test `process_directory()` with `dry_run=True` → no DB writes, BatchResult indicates dry-run mode
  - [x] Subtask 4.5: Test `process_directory()` with `verbose=True` → detailed per-file output to stdout
  - [x] Subtask 4.6: Test stdout/stderr separation: summary → stdout, errors → stderr with `[BATCH_ERROR]` prefix
  - [x] Subtask 4.7: Test NFR4: corrupt file doesn't stop batch — assert all valid files processed after a failure
  - [x] Subtask 4.8: Test empty directory → graceful handling, summary shows 0 files
  - [x] Subtask 4.9: Test directory with no .fit files → graceful handling, summary shows 0 files
  - [x] Subtask 4.10: Test CLI exit codes: 0 for partial success, 1 for all failures, 2 for invalid directory

- [x] Task 5: Verify code quality
  - [x] Subtask 5.1: Run `poetry run ruff check .` — zero errors
  - [x] Subtask 5.2: Run `poetry run pytest tests/test_pipeline/test_runner.py -v` (all tests pass including existing Story 1.7 tests)
  - [x] Subtask 5.3: Run `poetry run pytest` — full suite, no regressions (1 pre-existing failure in test_fit_parser.py unrelated to this story)
  - [x] Subtask 5.4: Verify CLI help shows batch command with all options

## Dev Notes

### Architecture Requirements

**This is Story 1.8 in the implementation sequence.** It builds EXACTLY on:
- Story 1.7: `process_file()` in `pipeline/runner.py` — single file processing with DB persistence, stdout/stderr separation, verbose/dry-run modes
- Story 1.3-1.6: Pipeline modules (fit_parser, metrics, validation) — called by `process_file()`
- Story 1.2: Database schema and repositories — used by `process_file()` for persistence

**CRITICAL: This story is a THIN WRAPPER around `process_file()`.** Do NOT reimplement pipeline logic. Do NOT reimplement DB persistence. Do NOT reimplement validation. Call `process_file()` for each file and handle errors gracefully.

**Technology Stack (from Architecture.md):**
- Typer for CLI framework (already in pyproject.toml, already wired in Story 1.7)
- SQLAlchemy + Alembic for DB (already implemented)
- Pydantic v2 for validation (already in use)
- `pipeline/runner.py` is DETERMINISTIC — NO LLM calls, NO randomness
- All thresholds from `config.py` (single source of truth)

**Deterministic Boundary (CRITICAL):**
- Batch processing is in `pipeline/` — DETERMINISTIC — NO LLM calls, NO randomness
- Same directory with same files → same outputs, always
- The only side effect is DB persistence per file, controlled by `dry_run` flag

**Module Location:**
- `src/run_intelligence/pipeline/runner.py` — MODIFY existing file (ADD `process_directory()` and `BatchResult`)
- `src/run_intelligence/cli.py` — MODIFY existing file (ADD `batch` command)
- `src/run_intelligence/pipeline/__init__.py` — MODIFY (ADD exports)
- `tests/test_pipeline/test_runner.py` — MODIFY existing test file (ADD batch tests)

### Critical Implementation Notes

1. **`process_directory()` is a loop with error handling around `process_file()`**: Story 1.7's `process_file()` raises `FitParseError` and `MetricCalculationError` on failure. The batch wrapper MUST catch these exceptions (and general `Exception` as fallback), log them to stderr with the filename, and continue to the next file. This is the ENTIRE point of batch independence (NFR4).

2. **`process_directory()` signature:**
   ```python
   @dataclass
   class BatchResult:
       total_files: int
       success_count: int
       failure_count: int
       failed_files: list[str]  # list of file paths that failed
       total_elapsed_seconds: float
       dry_run: bool
   
   def process_directory(
       directory_path: str,
       verbose: bool = False,
       dry_run: bool = False,
   ) -> BatchResult:
       """Process all .fit files in a directory.

       Orchestrates independent file processing: one corrupt file
       does not stop the batch. Calls process_file() for each file.

       Args:
           directory_path: Path to directory containing .fit files
           verbose: If True, print detailed per-file output to stdout
           dry_run: If True, process without writing to database

       Returns:
           BatchResult with aggregate statistics
       """
   ```

3. **Directory scanning:** Use `pathlib.Path(directory_path).glob("*.fit")` + `glob("*.FIT")` for case-insensitive matching. Sort alphabetically for deterministic processing order. Filter to files only (not directories).

4. **Per-file error handling:**
   ```python
   for fit_file in fit_files:
       try:
           process_file(str(fit_file), verbose=verbose, dry_run=dry_run)
           success_count += 1
       except FitParseError as e:
           failure_count += 1
           failed_files.append(str(fit_file))
           sys.stderr.write(f"[BATCH_ERROR] {fit_file.name}: FitParseError: {e}\n")
       except MetricCalculationError as e:
           failure_count += 1
           failed_files.append(str(fit_file))
           sys.stderr.write(f"[BATCH_ERROR] {fit_file.name}: MetricCalculationError: {e}\n")
       except Exception as e:
           failure_count += 1
           failed_files.append(str(fit_file))
           sys.stderr.write(f"[BATCH_ERROR] {fit_file.name}: Unexpected error: {e}\n")
   ```

5. **stdout/stderr Separation (NFR20) — CRITICAL for batch mode:**
   - **stdout**: Aggregate batch summary (total files, successes, failures, elapsed time), per-file success indicators
   - **stderr**: Per-file errors with `[BATCH_ERROR]` prefix, validation warnings
   - The CLI callback prints summary to stdout, routes errors to stderr
   - Per-file warnings from `process_file()` already go to stderr — DO NOT double-log them

6. **Batch output format:**
   ```
   # stdout:
   Batch Processing Summary
   ========================
   Directory: ./runs/
   Total files: 5
   Successful: 4
   Failed: 1
   Failed files: corrupt.fit
   Total time: 12.3s
   
   # stderr (if failures):
   [BATCH_ERROR] corrupt.fit: FitParseError: File is truncated
   ```

7. **CLI `batch` command:** Follow the same pattern as Story 1.7's `process` command:
   ```python
   @app.command()
   def batch(
       directory: str = typer.Argument(..., help="Directory containing .fit files"),
       verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed per-file output"),
       dry_run: bool = typer.Option(False, "--dry-run", help="Process without writing to database"),
   ) -> None:
       """Process all .fit files in a directory."""
   ```
   
   Also support global flag: `--batch ./runs/` on `main()` callback (like `--process` in Story 1.7).

8. **Exit codes:**
   - `0` if at least one file processed successfully (partial success is success for batch)
   - `1` if ALL files fail or directory doesn't exist / has no .fit files
   - `2` for invalid arguments (e.g., path is a file, not directory)

9. **Dry-run mode:** Pass `dry_run=True` to each `process_file()` call. The per-file dry-run logic is already implemented in Story 1.7 — batch just passes the flag through.

10. **Performance (NFR1 + NFR4):** Process files sequentially, NOT in parallel. SQLite single-writer constraint means parallel writes would cause contention. Each file must process in ≤5s, so total batch time ≈ N × 5s.

11. **Empty / no .fit files directory:** Handle gracefully. Print summary showing 0 files. Do not crash. Exit code 1 (no work done).

### Previous Story Intelligence

**From Story 1.7 (Pipeline Orchestration) — CRITICAL learnings:**
- `process_file(file_path, verbose, dry_run)` is the main single-file orchestrator — it calls `validate_and_flag()` and conditionally persists to DB
- `process_file()` raises `FitParseError` on parse failure, `MetricCalculationError` on calculation failure
- `process_file()` already handles stdout/stderr separation for single files
- `process_file()` already implements `--verbose` and `--dry-run` modes
- `process_file()` returns `RunData` on success, raises on failure
- `RunData` model has `.raw_data`, `.standard_metrics`, `.asthma_aware_metrics`, `.data_quality_flags`, `.confidence_score`
- `_persist_run()` handles DB session management, audit logging, JSON serialization with `by_alias=False`
- `_format_summary()` and `_format_warnings()` are available in `runner.py` but primarily used by `process_file()`
- DB session pattern: `create_session()` → `AuditLogRepository(session, engine)` → `RunRepository(session, audit_logger)` → `create_run()` → commit → close
- CLI uses Typer with `invoke_without_command=True` on `main()` callback
- `--process` works both as global flag AND as subcommand (backward compatibility)
- `runner.py` uses `sys.stdout.write()` / `sys.stderr.write()` for output separation
- All Pydantic models use `model_dump_json(by_alias=False)` for snake_case JSON

**From Story 1.7 Review Findings:**
- Review found and fixed: `fall` typo, `stderr` variable name error, `_format_verbose_output` not being called, duplicate stderr logging, timer excluding DB persistence, `_persist_run` returning None, `low_confidence_flag` ignored, `model_dump()` vs `model_dump_json()`, broad `except Exception`, session rollback overwriting error, trivial test assertions, CLI breaking change, missing exit code 2, import of private `_get_engine`, `_format_warnings` exact key assumptions, incorrect docstring about side effects
- These patterns MUST be followed and NOT repeated in batch implementation
- Review found 24 tests covering Story 1.7, all passing
- 295 total tests in suite (1 pre-existing failure in test_fit_parser.py unrelated to pipeline)

**From Story 1.6 (Data Validation):**
- `validate_and_flag()` orchestrates: parse → standard metrics → asthma-aware metrics → validation → `RunData`
- `DataQualityFlags` model has fields for HR artifacts, GPS drift, cadence inconsistencies, low confidence
- `RunData.confidence_score` aggregates across all metrics

**From Story 1.2 (Database Schema):**
- `RunRepository.create_run()` accepts JSON strings
- `AuditLogRepository` requires `engine` parameter for separate session
- SQLite WAL mode enabled in `db/session.py`

### Git Intelligence

Recent commits establish patterns:
- Code in `src/run_intelligence/pipeline/` modules
- Tests in `tests/test_pipeline/`
- Constants in `src/run_intelligence/config.py`
- Exports updated in `src/run_intelligence/pipeline/__init__.py`
- Custom exceptions: `FitParseError`, `MetricCalculationError`
- pytest with `-v` for verbose output
- ruff check `.` and ruff format `.`
- Story 1.7 modified `cli.py`, `runner.py`, `pipeline/__init__.py`, created `test_runner.py`

### Existing Code That This Story Interacts With

**Files to CREATE:**
- None (all modifications to existing files)

**Files to MODIFY:**
- `src/run_intelligence/pipeline/runner.py` — ADD `BatchResult` dataclass, `process_directory()` function, `_format_batch_summary()`, `_format_batch_error()`
- `src/run_intelligence/cli.py` — ADD `batch` subcommand + `--batch` global flag on `main()` callback
- `src/run_intelligence/pipeline/__init__.py` — ADD `process_directory` and `BatchResult` to `__all__`
- `tests/test_pipeline/test_runner.py` — ADD batch processing test cases to existing test file

**Files to IMPORT FROM (DO NOT MODIFY):**
- `src/run_intelligence/pipeline/runner.py` — `process_file()`, `FitParseError`, `MetricCalculationError` (from their original modules)
- `src/run_intelligence/pipeline/fit_parser.py` — `FitParseError` (if not already imported in runner.py)
- `src/run_intelligence/pipeline/metrics.py` — `MetricCalculationError` (if not already imported in runner.py)
- `src/run_intelligence/config.py` — `Settings`, constants (if needed)

**Files that EXIST and must NOT be modified (read-only reference):**
- `src/run_intelligence/pipeline/fit_parser.py` — Already complete
- `src/run_intelligence/pipeline/metrics.py` — Already complete
- `src/run_intelligence/pipeline/validation.py` — Already complete
- `src/run_intelligence/db/models.py` — Already complete
- `src/run_intelligence/db/repository.py` — Already complete
- `src/run_intelligence/db/session.py` — Already complete
- `src/run_intelligence/config.py` — No changes needed for this story

### What process_directory() Must Contain

Complete implementation pseudocode:

```python
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from run_intelligence.pipeline.fit_parser import FitParseError
from run_intelligence.pipeline.metrics import MetricCalculationError
from run_intelligence.pipeline.runner import process_file


@dataclass
class BatchResult:
    total_files: int
    success_count: int
    failure_count: int
    failed_files: list[str]
    total_elapsed_seconds: float
    dry_run: bool


def process_directory(
    directory_path: str,
    verbose: bool = False,
    dry_run: bool = False,
) -> BatchResult:
    """Process all .fit files in a directory independently.

    One corrupt file does not stop the batch. Each file is processed
    by calling process_file().

    Args:
        directory_path: Path to directory containing .fit files
        verbose: If True, print detailed per-file output
        dry_run: If True, process without writing to database

    Returns:
        BatchResult with aggregate statistics
    """
    path = Path(directory_path)
    if not path.exists():
        raise ValueError(f"Directory does not exist: {directory_path}")
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {directory_path}")

    # Find all .fit files (case-insensitive)
    fit_files = sorted(
        list(path.glob("*.fit")) + list(path.glob("*.FIT"))
    )

    total_files = len(fit_files)
    success_count = 0
    failure_count = 0
    failed_files: list[str] = []

    start_time = time.perf_counter()

    for fit_file in fit_files:
        try:
            process_file(str(fit_file), verbose=verbose, dry_run=dry_run)
            success_count += 1
        except (FitParseError, MetricCalculationError) as e:
            failure_count += 1
            failed_files.append(str(fit_file))
            sys.stderr.write(f"[BATCH_ERROR] {fit_file.name}: {type(e).__name__}: {e}\n")
        except Exception as e:
            failure_count += 1
            failed_files.append(str(fit_file))
            sys.stderr.write(f"[BATCH_ERROR] {fit_file.name}: Unexpected error: {e}\n")

    elapsed = time.perf_counter() - start_time

    return BatchResult(
        total_files=total_files,
        success_count=success_count,
        failure_count=failure_count,
        failed_files=failed_files,
        total_elapsed_seconds=elapsed,
        dry_run=dry_run,
    )


def _format_batch_summary(result: BatchResult) -> str:
    """Format batch result summary for stdout."""
    lines = [
        "Batch Processing Summary",
        "========================",
        f"Total files: {result.total_files}",
        f"Successful: {result.success_count}",
        f"Failed: {result.failure_count}",
    ]
    if result.failed_files:
        lines.append(f"Failed files: {', '.join(Path(f).name for f in result.failed_files)}")
    lines.append(f"Total time: {result.total_elapsed_seconds:.1f}s")
    if result.dry_run:
        lines.append("[DRY RUN] No data was written to the database.")
    return "\n".join(lines) + "\n"
```

### What `cli.py` Batch Command Must Look Like

```python
@app.command()
def batch(
    directory: str = typer.Argument(..., help="Directory containing .fit files"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed per-file output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Process without writing to database"),
) -> None:
    """Process all .fit files in a directory."""
    from run_intelligence.pipeline.runner import process_directory, _format_batch_summary
    
    try:
        result = process_directory(directory, verbose=verbose, dry_run=dry_run)
        summary = _format_batch_summary(result)
        sys.stdout.write(summary)
        
        if result.success_count == 0:
            raise typer.Exit(code=1)
    except ValueError as e:
        sys.stderr.write(f"[CLI_ERROR] {e}\n")
        raise typer.Exit(code=2)
    except Exception as e:
        sys.stderr.write(f"[CLI_ERROR] Batch processing failed: {e}\n")
        raise typer.Exit(code=1)
```

Also add global flag on `main()` callback:
```python
@app.callback(invoke_without_command=True)
def main(
    process: str | None = typer.Option(None, "--process", help="Process a single .fit file"),
    batch: str | None = typer.Option(None, "--batch", help="Process all .fit files in directory"),
    # ... existing options
) -> None:
    if batch:
        # invoke batch command logic
        ...
```

### Testing Requirements

**Test isolation:**
- Use mock `process_file()` or mock `.fit` files in temp directories
- Do NOT require real Coros .fit files for batch tests
- Create temp directory with mock files (can be empty files if mocking `process_file`)

**Test coverage must include:**
- `process_directory()` with all valid files → success_count == total_files, failure_count == 0
- `process_directory()` with one corrupt file → success_count == total - 1, failed_files contains corrupt file name, other files processed
- `process_directory()` with all corrupt files → success_count == 0, failure_count == total_files
- `process_directory()` with `dry_run=True` → no DB writes, BatchResult.dry_run == True
- `process_directory()` with `verbose=True` → detailed output (can verify process_file called with verbose=True)
- `process_directory()` with empty directory → total_files == 0, no crash
- `process_directory()` with directory containing no .fit files → total_files == 0, no crash
- `process_directory()` with non-existent directory → raises ValueError
- `process_directory()` with file path instead of directory → raises ValueError
- stdout/stderr separation: summary to stdout, errors to stderr with `[BATCH_ERROR]` prefix
- NFR4 test: one failure does not prevent subsequent files from processing
- CLI exit code 0 when ≥1 success
- CLI exit code 1 when all files fail
- CLI exit code 2 for invalid directory path
- `_format_batch_summary()` produces expected format with all fields
- `_format_batch_summary()` includes dry-run note when applicable
- `_format_batch_summary()` includes failed files list when applicable

**Pattern to follow:**
- `tests/test_pipeline/test_runner.py` already exists from Story 1.7
- Add batch test class: `TestProcessDirectory`
- Use `tmp_path` pytest fixture for temp directories
- Use `unittest.mock.patch` to mock `process_file` where appropriate
- Use `unittest.mock.patch("sys.stdout")` and `patch("sys.stderr")` to verify output separation

**Testing commands:**
```bash
poetry run pytest tests/test_pipeline/test_runner.py -v
poetry run pytest tests/test_pipeline/ -v
poetry run pytest  # full suite, verify no regressions
poetry run ruff check .
poetry run ruff format .
```

### Project Structure Notes

**File locations (from Architecture.md):**
```
src/run_intelligence/
├── pipeline/
│   ├── __init__.py          # EXISTS (update exports)
│   ├── fit_parser.py         # EXISTS (Story 1.3)
│   ├── metrics.py            # EXISTS (Story 1.4 + 1.5)
│   ├── validation.py         # EXISTS (Story 1.6)
│   └── runner.py             # EXISTS (Story 1.7) — ADD process_directory()
├── cli.py                    # EXISTS (Story 1.7) — ADD batch command
├── config.py                 # EXISTS (no changes needed)
├── db/
│   ├── models.py             # EXISTS (Story 1.2)
│   ├── repository.py         # EXISTS (Story 1.2)
│   └── session.py            # EXISTS (Story 1.2)
```

**Alignment with unified project structure:**
- Implementation: `src/run_intelligence/pipeline/runner.py` (MODIFY)
- Implementation: `src/run_intelligence/cli.py` (MODIFY)
- Tests: `tests/test_pipeline/test_runner.py` (MODIFY — add to existing file)

### Key Differences from Story 1.7

**Story 1.8 is different from 1.7 in two critical ways:**
1. **Error handling philosophy:** Story 1.7 raises exceptions on errors (caller handles them). Story 1.8 CATCHES exceptions per-file and continues — this is the entire purpose of batch independence.
2. **Aggregate output:** Story 1.7 outputs single-file results. Story 1.8 outputs aggregate batch summaries with success/failure counts.

**Important: Do NOT modify `process_file()` behavior.** The single-file function must remain unchanged. Batch wraps it with try/except.

### References

- [Source: architecture.md#Core Architectural Decisions] — Deterministic boundary: pipeline/ must have NO LLM calls
- [Source: architecture.md#Project Structure] — File location: `pipeline/runner.py` (MODIFY), `cli.py` (MODIFY)
- [Source: architecture.md#Process Patterns] — Deterministic code pattern: same input → same output
- [Source: architecture.md#Communication Patterns] — Node writes: Pipeline writes to `run_data`
- [Source: architecture.md#CLI Output Convention] — stdout for summaries/responses, stderr for warnings/errors
- [Source: architecture.md#Data Architecture] — Pydantic model JSON serialization: `by_alias=False`
- [Source: architecture.md#Integration Points] — CLI → runner.py → RunData → db/repository.py
- [Source: epics.md#Story 1.8] — Acceptance criteria for batch processing
- [Source: prd.md#FR7] — Batch process all .fit files in a specified directory
- [Source: prd.md#FR41] — System processes batch files independently (one corrupt file doesn't stop batch)
- [Source: prd.md#FR39] — Dry-run mode to validate without writing
- [Source: prd.md#NFR1] — Pipeline processes single file in ≤5 seconds
- [Source: prd.md#NFR4] — Batch mode processes .fit files independently
- [Source: prd.md#NFR20] — Normal output to stdout, errors/warnings to stderr
- [Source: Story 1.7] — process_file() function, stdout/stderr separation, DB persistence patterns

## Dev Agent Record

### Agent Model Used

kimi-k2.6 (OpenCode)

### Debug Log References

- Fixed alphabetical ordering issue in test_one_corrupt_file_continues: files are processed sorted, so side_effect order must match alphabetical file names
- Fixed CLI test patch target: process_directory is imported inside _handle_batch function, so patch target must be run_intelligence.pipeline.runner.process_directory
- Fixed missing typer import in test file for pytest.raises(typer.Exit)
- Fixed _handle_batch catching typer.Exit(code=0) in except Exception: added explicit `except typer.Exit: raise` before the general Exception handler

### Completion Notes List

- Implemented BatchResult dataclass and process_directory() in runner.py with case-insensitive .fit file scanning, alphabetical sorting, per-file error handling, and elapsed time tracking
- Implemented _format_batch_summary() for stdout aggregate output and _format_batch_error() for stderr error formatting with [BATCH_ERROR] prefix
- Updated cli.py with full batch subcommand (directory positional arg, --verbose/-v, --dry-run) and --batch global flag on main() callback for backward compatibility
- Added _handle_batch() with proper exit codes (0 for partial success, 1 for all failures, 2 for invalid args) and stdout/stderr separation
- Updated pipeline/__init__.py exports to include process_directory and BatchResult
- Added comprehensive test coverage: 23 new tests across TestBatchResult, TestFormatBatchSummary, TestFormatBatchError, TestProcessDirectory, and TestProcessDirectoryCLI
- All 51 runner tests pass; full suite shows 322 passed, 1 skipped, 1 pre-existing failure unrelated to this story
- ruff check passes with zero errors
- CLI help verified: both `python -m run_intelligence --help` and `python -m run_intelligence batch --help` show correct options

### File List

- src/run_intelligence/pipeline/runner.py — MODIFIED (ADDED BatchResult, process_directory(), _format_batch_summary(), _format_batch_error())
- src/run_intelligence/cli.py — MODIFIED (ADDED _handle_batch(), updated batch subcommand, added --batch global flag on main())
- src/run_intelligence/pipeline/__init__.py — MODIFIED (ADDED process_directory and BatchResult to __all__)
- tests/test_pipeline/test_runner.py — MODIFIED (ADDED 23 batch processing tests)

### Change Log

- Addressed code review findings — 0 items resolved (Date: 2026-05-21)
- Implemented Story 1.8: Batch Processing — added process_directory(), BatchResult, CLI batch command, and comprehensive tests (Date: 2026-05-21)

### Review Findings

(Will be filled by code-review agent after implementation)
