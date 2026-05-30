---
depends_on: []
---

# M001: Health Logging

**Gathered:** 2026-05-30
**Status:** Ready for planning

## Project Description

Run Intelligence is an asthma-aware running intelligence platform that integrates Coros .fit file parsing with chronic asthma management. M001 focuses on enabling users to log health data interactively and associate it with runs for cross-referencing.

## Why This Milestone

Runners with asthma need to track subjective health data (peak flow, symptoms, medication use) to identify triggers and correlate them with objective run metrics. Without health logging, the asthma-aware features have no input to work with.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Log health data interactively via CLI (peak flow, sleep quality, RPE, asthma symptoms 0-3, SABA use, notes)
- Associate health log entries with specific runs
- View health log history

### Entry point / environment

- Entry point: `python -m run_intelligence --log-health` (interactive) or `python -m run_intelligence --log-health --associate-run <id>`
- Environment: CLI local
- Live dependencies involved: SQLite database, no external APIs

## Completion Class

- Contract complete means: CLI health-log command works, data persists to DB, run association functional
- Integration complete means: Health logs can be queried with run data
- Operational complete means: CLI works reliably, handles edge cases gracefully

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Interactive health logging flow works end-to-end (prompt → validate → persist)
- Health log entries can be associated with existing runs
- Health log data is queryable via CLI (list, view)
- Error handling works for invalid inputs and missing runs
- Unit tests pass for core logic
- Integration tests verify CLI → DB flow

## Architectural Decisions

### MiniMax LLM Integration

**Decision:** Use MiniMax as LLM provider via OpenAI-compatible API

**Rationale:** User specified MiniMax with ANTHROPIC_BASE_URL and ANTHROPIC_MODEL config

**Alternatives Considered:**
- OpenAI — not chosen (user preference)
- Anthropic direct — not chosen (user preference)
- Ollama local — not chosen (user preference)

### Interactive CLI with Typer

**Decision:** Use Typer with interactive prompts for health logging

**Rationale:** Matches existing CLI pattern, provides validation, user requested interactive interface

### Domain Isolation (Future-Proofing)

**Decision:** Health log data accessible to Asthma Profile only (not Runner Profile)

**Rationale:** Per Epic 3 architecture — asthma context appears only in Asthma Profile

## Error Handling Strategy

- **Invalid values:** Typer prompts with validation, retry until valid or skip
- **Missing run association:** Clear error, list available runs
- **Duplicate date:** Warn and offer update or new entry
- **Incomplete session (ctrl+c):** Cleanup, no partial writes
- **Out-of-range clinical values:** Allow but warn (no validation blocking per user request)

## Risks and Unknowns

- MiniMax API integration not yet configured — need env vars setup
- LangGraph orchestration not yet implemented — health log is standalone for now
- Hypothesis lifecycle (Epic 3) not started — R003 depends on it

## Existing Codebase / Prior Art

- `src/run_intelligence/cli.py` — existing CLI with process, batch commands
- `src/run_intelligence/db/models.py` — HealthLog model already defined
- `src/run_intelligence/health_log/` — empty module, to be implemented

## Relevant Requirements

- R001 — Interactive health logging CLI
- R002 — Health log run association
- R003 — Health log as hypothesis evidence

## Scope

### In Scope

- Interactive CLI health log input (peak flow, sleep, RPE, symptoms, SABA, notes)
- Health log persistence to SQLite
- Run association (link health log to existing run)
- Health log list/view commands
- Unit + integration tests
- Pydantic validation for input types

### Out of Scope / Non-Goals

- Conversational health log input (Epic 4)
- Hypothesis lifecycle integration (Epic 3)
- Multi-athlete support
- Weather/pollen integration
- Visual dashboard

## Technical Constraints

- MiniMax API credentials must be configured via .env
- Must follow deterministic boundary: health_log module has NO LLM calls
- Must maintain existing CLI patterns from Epic 1

## Integration Points

- **Database:** HealthLog table already exists in schema
- **CLI:** Extend existing cli.py with health-log command
- **Future:** Health log will feed into Asthma Profile agent (Epic 3)

## Testing Requirements

- Unit tests for health log input validation
- Unit tests for run association logic
- Integration tests for CLI → DB flow
- Edge case tests (invalid inputs, missing runs, ctrl+c)

## Acceptance Criteria

### S01: Interactive Health Logging CLI
- User can input peak flow (L/min), sleep quality (1-5), post-run RPE (1-10), asthma symptoms (0-3), SABA use (yes/no), notes (free text)
- All inputs validated via Pydantic
- Data persists to health_log table

### S02: Run Association
- User can associate health log entry with existing run via run ID
- System validates run exists before association
- Association is queryable

### S03: Health Log Query
- User can list health log entries (last N, date range)
- User can view specific health log entry
- User can filter by run association

## Open Questions

- MiniMax API key setup — pending user configuration
