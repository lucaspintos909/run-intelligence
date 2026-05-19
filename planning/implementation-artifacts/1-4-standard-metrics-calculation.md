# Story 1.4: Standard Metrics Calculation

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story ID & Key

- **Story ID:** 1.4
- **Story Key:** 1-4-standard-metrics-calculation
- **Epic:** Epic 1: Project Foundation & Data Pipeline
- **FRs Covered:** FR1 (process .fit files to extract standard running metrics), FR2 (derive asthma-aware metrics - foundation)
- **NFRs Covered:** NFR1 (.fit processing ≤5s), NFR6 (local data persistence)

## Story

As a system,
I want to calculate standard running metrics from raw .fit data,
So that users get meaningful performance metrics.

## Acceptance Criteria

### AC1: Standard Metrics Calculation

**Given** raw metrics from `fit_parser.parse_fit_file()`
**When** I call `calculate_standard_metrics(raw_data: RawRunData)`
**Then** I receive a `StandardMetrics` Pydantic model containing:
- `pace_avg_min_per_km`: Average pace in minutes per km
- `pace_max_min_per_km`: Maximum pace (fastest) in min/km
- `pace_min_min_per_km`: Minimum pace (slowest) in min/km
- `hr_zone_distribution`: dict with time in seconds for each zone Z1-Z5
- `cadence_avg_rpm`: Average cadence (already in RawRunData)
- `cadence_max_rpm`: Maximum cadence (already in RawRunData)
- `elevation_gain_m`: Total elevation gain in meters
- `elevation_loss_m`: Total elevation loss in meters

### AC2: HR Zone Calculation

**Given** HR data (avg, max, min) from RawRunData
**When** I calculate HR zones
**Then** I use standard running zones:
- Z1 (Recovery): 50-60% max HR
- Z2 (Endurance): 60-70% max HR
- Z3 (Tempo): 70-80% max HR
- Z4 (Threshold): 80-90% max HR
- Z5 (VO2max): 90-100% max HR
**And** time in each zone is estimated based on duration and HR distribution
**And** max HR is calculated as `220 - age` (default 30 years if unknown, configurable via config.py)

### AC3: Elevation Gain/Loss Calculation

**Given** `gps_elevation` array from RawRunData (list of elevation points)
**When** I calculate elevation metrics
**Then** I compute:
- `elevation_gain_m`: Sum of all positive elevation changes between consecutive points
- `elevation_loss_m`: Sum of all negative elevation changes between consecutive points
**And** I ignore changes below 2 meters (noise filter)
**And** I handle `None` values in the elevation array by skipping those points

### AC4: Pace Calculation

**Given** `pace_sec_per_km` from RawRunData (session-level calculation from total distance/duration)
**When** I calculate standard metrics
**Then** if the raw pace exists, I convert to min/km format
**And** I note that RawRunData currently provides session-level aggregate (single value), not per-segment min/max
**And** the single pace value is used for `pace_avg_min_per_km`

### AC5: Pydantic Output Model Validation

**Given** derived metrics are calculated
**When** the `StandardMetrics` model is constructed
**Then** all values are validated within physiologically plausible ranges
**And** invalid/out-of-range values raise `MetricCalculationError`
**And** the model uses `by_alias=False` for JSON serialization (snake_case)

### AC6: Integration with Pipeline

**Given** `calculate_standard_metrics()` is implemented
**When** it is called by `pipeline/runner.py`
**Then** it returns `StandardMetrics` that can be serialized to JSON for `derived_metrics_json` column
**And** the function follows the deterministic boundary: NO LLM calls, pure Python

### AC7: Test Coverage

**Given** `calculate_standard_metrics()` is implemented
**When** tests are run
**Then** tests cover: valid data, edge cases (no GPS, missing HR, etc.)
**And** tests verify deterministic behavior: same input → same output

## Tasks / Subtasks

- [x] Task 1: Create `StandardMetrics` Pydantic model in `pipeline/metrics.py` (AC: #1, #5)
  - [x] Subtask 1.1: Define `StandardMetrics` class with all fields from AC1
  - [x] Subtask 1.2: Add field validators for HR zones (0-100% ranges), elevation (non-negative), cadence (0-300 rpm)
  - [x] Subtask 1.3: Add `to_json()` and `from_json()` methods for serialization
  - [x] Subtask 1.4: Add `MetricCalculationError` custom exception class

- [x] Task 2: Implement `calculate_standard_metrics()` function (AC: #2, #3, #4, #6)
  - [x] Subtask 2.1: Implement HR zone calculation with configurable max HR (default 220-age from config.py)
  - [x] Subtask 2.2: Implement elevation gain/loss calculation with 2m noise filter
  - [x] Subtask 2.3: Handle missing/None GPS elevation data gracefully
  - [x] Subtask 2.4: Handle missing HR/cadence data by returning None for those fields
  - [x] Subtask 2.5: Ensure function is deterministic: no randomness, no LLM calls

- [x] Task 3: Add constants to config.py (AC: #2, #3)
  - [x] Subtask 3.1: Add `HR_ZONES` dict with zone boundaries and labels
  - [x] Subtask 3.2: Add `DEFAULT_AGE` constant for max HR calculation (30 years default)
  - [x] Subtask 3.3: Add `ELEVATION_NOISE_FILTER_METERS` constant (2m threshold)

- [x] Task 4: Update `pipeline/__init__.py` exports (AC: #6)
  - [x] Subtask 4.1: Export `calculate_standard_metrics`, `StandardMetrics`, `MetricCalculationError`

- [x] Task 5: Add tests (AC: #7)
  - [x] Subtask 5.1: Create `tests/test_pipeline/test_metrics.py`
  - [x] Subtask 5.2: Test HR zone calculation with various HR values
  - [x] Subtask 5.3: Test elevation gain/loss with various GPS profiles
  - [x] Subtask 5.4: Test edge cases: no GPS, no HR, missing values
  - [x] Subtask 5.5: Test deterministic behavior: same input → same output
  - [x] Subtask 5.6: Test JSON serialization round-trip

- [x] Task 6: Verify code quality
  - [x] Subtask 6.1: Run `poetry run ruff check .` — zero errors
  - [x] Subtask 6.2: Run `poetry run pytest tests/test_pipeline/test_metrics.py -v`
  - [x] Subtask 6.3: Verify no regression in existing tests (`poetry run pytest`)

### Review Findings

- [x] [Review][Patch] `hr_zone_distribution` model structure: Migrar de campos planos a dict anidado `hr_zone_distribution: dict[str, int]` como pide AC1. **Fixed.**
- [x] [Review][Dismiss] Pace cero/negativo silenciado a `None` — Aceptado: se trata como dato faltante (decisión del usuario: "tratar como faltante").
- [x] [Review][Dismiss] Validadores del modelo lanzan `ValidationError` — Aceptado: comportamiento idiomático de Pydantic v2 (decisión del usuario: "aceptar ValidationError").

- [x] [Review][Patch] Elevaciones negativas descartadas silenciosamente — **Fixed.** Eliminado filtro `val >= 0`; solo se saltean `None` y valores no numéricos.
- [x] [Review][Patch] Filtro de ruido excluye cambios exactos de 2.0m — **Fixed.** Cambiado a `>= noise_threshold` / `<= -noise_threshold`.
- [x] [Review][Patch] Falta type hint `RawRunData` — **Fixed.** Agregado `raw_data: RawRunData` con import bajo `TYPE_CHECKING` para evitar ciclos.
- [x] [Review][Patch] Excepción demasiado amplia `except Exception` — **Fixed.** Ahora captura `ValidationError` explícitamente y relanza con `from e`.
- [x] [Review][Patch] Excepción silenciosa en cálculo de zonas FC — **Fixed.** El `except` ahora relanza `MetricCalculationError` con `from e` en lugar de `pass`.
- [x] [Review][Patch] `age` sin validación de límites — **Fixed.** Agregado `0 < age <= 120` en `calculate_max_hr`.
- [x] [Review][Patch] `calculate_max_hr` puede retornar `float` — **Fixed.** Forzado a `int()` en el return.
- [x] [Review][Patch] `MetricCalculationError` sin exception chaining — **Fixed.** Todos los `raise MetricCalculationError(...)` ahora usan `from e`.
- [x] [Review][Patch] Type hint de `gps_elevation` incorrecto — **Fixed.** Cambiado a `Optional[list[Optional[float]]]`.
- [x] [Review][Patch] Segundos fraccionarios truncados — **Fixed.** Cambiado `int(duration_seconds)` a `round(duration_seconds)`.
- [x] [Review][Patch] Test de filtro de ruido con aserción débil — **Fixed.** Test ahora verifica que deltas exactos de 2m se cuenten y que deltas <2m sean suprimidos.
- [x] [Review][Patch] Test JSON invalid input captura `Exception` genérico — **Fixed.** Ahora captura `ValidationError` explícitamente.
- [x] [Review][Patch] Validadores permiten `NaN`/`Inf` — **Fixed.** Agregados chequeos `math.isnan`/`math.isinf` en todos los validadores numéricos.
- [x] [Review][Patch] `NaN` en `hr_avg` no tratado como `None` — **Fixed.** Agregado check `math.isnan(hr_avg)` tanto en `calculate_hr_zone_distribution` como en `calculate_standard_metrics`.
- [x] [Review][Patch] `duration_seconds` negativo no validado — **Fixed.** Agregada validación en `calculate_hr_zone_distribution`.
- [x] [Review][Patch] `calculate_standard_metrics` no valida `raw_data is None` — **Fixed.** Agregado check al inicio de la función.
- [x] [Review][Patch] Tests faltan cubrir casos límite — **Fixed.** Agregados tests para: edad negativa, NaN en datos, pendiente gradual sostenida, pace ≈0, boundary exacto de zona, `duration_seconds` negativo, input `None`.

## Dev Notes

### Architecture Requirements

**This is Story 1.4 in the implementation sequence.** It builds on Story 1.3 (fit file parsing) and produces output that Story 1.6 (data validation) will incorporate into `RunData`.

**Technology Stack (from Architecture.md):**
- Pydantic v2 for runtime validation
- Pure Python (deterministic boundary — NO LLM calls)
- `snake_case` for functions, `PascalCase` for classes/models
- All thresholds from `config.py` (single source of truth)

**Deterministic Boundary (CRITICAL):**
- `pipeline/` is DETERMINISTIC — NO LLM calls, NO randomness
- `metrics.py` computes from raw data deterministically
- Same `RawRunData` input → identical `StandardMetrics` output, always

**Module Location:**
- `src/run_intelligence/pipeline/metrics.py` — standard + asthma-aware metrics calculation
- This story creates the `calculate_standard_metrics()` function
- Story 1.5 will add `calculate_asthma_aware_metrics()` to the same module

**Relationship to RawRunData from Story 1.3:**
- `RawRunData` provides session-level aggregates: `hr_avg_bpm`, `hr_max_bpm`, `hr_min_bpm`
- Story 1.4 computes from these session-level values when per-record data isn't available
- `gps_elevation` is the one field with per-record granularity — use it for elevation gain/loss

### Critical Implementation Notes

1. **HR Zones from Session Data**: RawRunData only provides avg/max/min HR, not per-record time series. Calculate HR zone distribution by estimating time distribution based on available HR statistics and duration. Document this as an approximation.

2. **Elevation from GPS Array**: The `gps_elevation` field is a list of per-record elevation values. Compute gain/loss by summing positive/negative deltas between consecutive points, filtering noise below 2m.

3. **Missing Data Handling**: If RawRunData has `None` for any field (e.g., no GPS data), `calculate_standard_metrics()` should gracefully return `None` for the affected output fields rather than raising an error.

4. **Pydantic v2 Syntax**: Use `model_config = ConfigDict(...)` (NOT `class Config`), use `field_validator` and `model_validator` for validation. Consistent with Story 1.2 and 1.3 patterns.

5. **Config Constants**: All thresholds (HR zone boundaries, elevation noise filter) MUST come from `config.py`. Never hardcode clinical values.

6. **Deterministic-Generative Boundary**: This function is pure Python computation. Do NOT call any LLM, do NOT generate any text beyond the structured metrics model.

### What StandardMetrics Must Contain

| Field | Type | Nullable | Source |
|---|---|---|---|
| `pace_avg_min_per_km` | `float` | Yes | Converted from RawRunData.pace_sec_per_km |
| `pace_max_min_per_km` | `float` | Yes | Same as avg (session-level only) |
| `pace_min_min_per_km` | `float` | Yes | Same as avg (session-level only) |
| `hr_zone_z1_seconds` | `int` | Yes | Estimated from HR stats + duration |
| `hr_zone_z2_seconds` | `int` | Yes | Estimated from HR stats + duration |
| `hr_zone_z3_seconds` | `int` | Yes | Estimated from HR stats + duration |
| `hr_zone_z4_seconds` | `int` | Yes | Estimated from HR stats + duration |
| `hr_zone_z5_seconds` | `int` | Yes | Estimated from HR stats + duration |
| `cadence_avg_rpm` | `float` | Yes | From RawRunData.cadence_avg_rpm |
| `cadence_max_rpm` | `float` | Yes | From RawRunData.cadence_max_rpm |
| `elevation_gain_m` | `float` | Yes | Computed from gps_elevation array |
| `elevation_loss_m` | `float` | Yes | Computed from gps_elevation array |

**Note on HR Zones**: RawRunData only provides `hr_avg_bpm`, `hr_max_bpm`, `hr_min_bpm` — not per-record HR values. For Story 1.4, estimate zone distribution based on these session-level statistics and total duration. This is an approximation; accurate zone time requires per-record HR data (future enhancement).

### Previous Story Intelligence

**From Story 1.3 (.fit File Parsing):**
- `RawRunData` Pydantic model with: `timestamp`, `duration_seconds`, `distance_meters`, `pace_sec_per_km`, `hr_avg_bpm`, `hr_max_bpm`, `hr_min_bpm`, `cadence_avg_rpm`, `cadence_max_rpm`, `gps_lat`, `gps_lon`, `gps_elevation`
- `FitParseError` custom exception for parsing failures
- `parse_fit_file(file_path: str) -> RawRunData` function
- JSON serialization via `to_json()` / `from_json()`
- `fitparse` library for FIT protocol parsing
- GPS semicircle conversion handled in fit_parser

**From Story 1.2 (Database Schema):**
- `runs` table has `derived_metrics_json` column (this story populates it)
- `RunRepository.create_run()` accepts `derived_metrics_json` parameter
- Pydantic v2 validation patterns established
- `config.py` has `HR_LIMITS` dict with `age_predicted_max: 220`

**From Story 1.1 (Project Initialization):**
- Poetry with `pyproject.toml` — `poetry run pytest`, `poetry run ruff check .`
- Module invocation: `python -m run_intelligence`
- `config.py` uses `pydantic_settings.BaseSettings` with `model_config = SettingsConfigDict`
- Tests mirror src structure: `tests/test_pipeline/`

### Existing Code That This Story Interacts With

**Files to CREATE:**
- `src/run_intelligence/pipeline/metrics.py` — Main metrics module
- `tests/test_pipeline/test_metrics.py` — Metrics tests

**Files that EXIST and must NOT be modified:**
- `src/run_intelligence/pipeline/fit_parser.py` — RawRunData already defined
- `src/run_intelligence/db/models.py` — Run model already has derived_metrics_json column
- `src/run_intelligence/db/repository.py` — Already supports derived_metrics_json

**Files that may need MINOR UPDATES:**
- `src/run_intelligence/config.py` — Add HR_ZONES, DEFAULT_AGE, ELEVATION_NOISE_FILTER constants
- `src/run_intelligence/pipeline/__init__.py` — Add exports for new symbols

### Testing Requirements

**Test isolation:**
- Tests must work with mock `RawRunData` objects
- Test DB not required (metrics calculation is pure computation)
- Test various HR profiles: normal, elevated max HR, missing HR

**Test coverage must include:**
- Standard metrics calculation from complete RawRunData
- Handling missing optional fields (no GPS, no HR, etc.)
- HR zone calculation with various max HR values
- Elevation gain/loss with various GPS profiles (ascending, descending, mixed, flat)
- JSON serialization round-trip
- Deterministic behavior verification

**Existing test infrastructure:**
- `tests/conftest.py` from Story 1.2 has shared fixtures — reuse as needed
- `tests/test_pipeline/` directory exists with test_fit_parser.py

**Testing commands:**
```bash
poetry run pytest tests/test_pipeline/test_metrics.py -v
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
│   ├── fit_parser.py        # EXISTS (Story 1.3)
│   ├── metrics.py           # NEW — this story (Story 1.4)
│   ├── validation.py        # Story 1.6 (NOT this story)
│   └── runner.py            # Story 1.7 (NOT this story)
```

**Alignment with unified project structure:**
- Implementation: `src/run_intelligence/pipeline/metrics.py`
- Tests: `tests/test_pipeline/test_metrics.py`
- Constants: `src/run_intelligence/config.py`

### References

- [Source: architecture.md#Core Architectural Decisions] — Deterministic boundary: pipeline/ must have NO LLM calls
- [Source: architecture.md#Project Structure] — File location: `pipeline/metrics.py`
- [Source: architecture.md#Process Patterns] — Deterministic code pattern, config.py single source of truth
- [Source: architecture.md#Communication Patterns] — Node write fields: Pipeline writes to `run_data`
- [Source: epics.md#Story 1.4] — Acceptance criteria for standard metrics calculation
- [Source: prd.md#FR1] — Process .fit files to extract standard running metrics
- [Source: prd.md#FR2] — Derive asthma-aware metrics (foundation)
- [Source: prd.md#NFR1] — Pipeline processes single file in ≤5 seconds
- [Source: Story 1.3] — RawRunData model and parse_fit_file() function
- [Source: Story 1.2] — Database schema with derived_metrics_json column

## Dev Agent Record

### Agent Model Used

minimax-m2.7

### Debug Log References

### Completion Notes List

- Story 1.4 (Standard Metrics Calculation) fully implemented
- Created `StandardMetrics` Pydantic model with all required fields and validators
- Implemented `calculate_standard_metrics()` function with deterministic behavior (no LLM calls)
- Added HR zone calculation using session-level HR data (approximation due to RawRunData constraints)
- Added elevation gain/loss calculation with 2m noise filter
- Added constants to config.py: HR_ZONES, DEFAULT_AGE, ELEVATION_NOISE_FILTER_METERS
- Updated pipeline/__init__.py with new exports
- Created comprehensive test suite (44 tests) covering all ACs and edge cases
- All tests pass (118 passed, 1 skipped in full suite)
- Lint checks pass for src/ and tests/

### File List

**Created:**
- `src/run_intelligence/pipeline/metrics.py` — Standard + asthma-aware metrics calculation
- `tests/test_pipeline/test_metrics.py` — Metrics tests (44 tests)

**Modified:**
- `src/run_intelligence/pipeline/__init__.py` — Added exports for StandardMetrics, MetricCalculationError, calculate_standard_metrics
- `src/run_intelligence/config.py` — Added HR_ZONES dict, DEFAULT_AGE=30, ELEVATION_NOISE_FILTER_METERS=2.0
- `planning/implementation-artifacts/sprint-status.yaml` — Updated story status to in-progress then to review

### Change Log

- 2026-05-19: Implemented Story 1.4 - Standard Metrics Calculation (all tasks completed, tests passing, ready for review)