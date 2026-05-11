---
stepsCompleted:
  - step-01-init
  - step-02-context
  - step-03-starter
  - step-04-decisions
  - step-05-patterns
  - step-06-structure
  - step-07-validation
  - step-08-complete
workflowType: 'architecture'
lastStep: 8
status: 'complete'
completedAt: '2026-05-11'
inputDocuments:
  - /home/lpintos/proyectos/run-intelligence/_bmad-output/planning-artifacts/prd.md
  - /home/lpintos/proyectos/run-intelligence/_bmad-output/planning-artifacts/product-brief-run-intelligence.md
  - /home/lpintos/proyectos/run-intelligence/_bmad-output/planning-artifacts/product-brief-run-intelligence-distillate.md
  - /home/lpintos/proyectos/run-intelligence/docs/base_cientifica_running.md
  - /home/lpintos/proyectos/run-intelligence/docs/asma_running_base_teorica.md
workflowType: 'architecture'
project_name: 'run-intelligence'
user_name: 'lpintos'
date: '2026-05-11'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements (46 total across 8 categories):**

- **Run Data Ingestion (FR1–FR7)**: .fit parsing pipeline with standard + asthma-aware derived metrics, HR artifact detection, GPS drift flagging, cadence inconsistency flagging, low-confidence flagging, single + batch processing
- **Asthma-Aware Analytics (FR8–FR14)**: Hypothesis lifecycle with min evidence thresholds, cross-referencing objective+subjective data, clinical seed thresholds, confidence quantification, promotion blocking without evidence, data quality downgrade
- **Health Logging (FR15–FR17)**: Interactive CLI input (peak flow, sleep, RPE, symptoms 0-3, SABA use), association with run data, subjective data as hypothesis evidence
- **Profile Intelligence (FR18–FR24)**: Separate asthma/runner profiles with domain-isolated boundaries, synthesis preserving tension, conflict detection + escalation to user, decision recording, git-versioned evolution tracking
- **Coaching & Decision Support (FR25–FR31)**: Conversational coach with prepared context package, evidence-anchored recommendations, deterministic BIE risk simulation, structured risk output, natural language translation, strict generative-deterministic boundary
- **Medical Reporting (FR32–FR35)**: Monthly structured reports with clinical source citation, confirmed vs testing-stage pattern separation, user-controlled sharing
- **Data Management & Configuration (FR36–FR43)**: SQLite persistence, markdown profiles, verbose/dry-run modes, output redirection, batch independence, stdout/stderr separation, conversation history persistence
- **Orchestration (FR45–FR46)**: Multi-agent pipeline with conditional transitions across 6 LangGraph nodes

**Non-Functional Requirements (20 total across 3 categories):**

- **Performance (NFR1–NFR5)**: .fit processing ≤5s, context package prep ≤2s, BIE simulator deterministic ≤1s, batch independence, profile update bounded by LLM latency
- **Security & Privacy (NFR6–NFR15)**: Local-first data sovereignty, git-versioned profiles, LLM data handling transparency, deterministic clinical engine, wellness positioning disclaimers, encrypted data at rest, OS-level auth, audit trail, data purge capability, credential isolation
- **Integration (NFR16–NFR20)**: .fit protocol compatibility, provider-interchangeable LLM endpoint, git version tracking, SQLite WAL concurrency, stdout/stderr separation

**Scale & Complexity:**

- Primary domain: CLI tool + AI/LLM orchestration + domain-specific data pipeline (healthcare/wellness)
- Complexity level: High
- Estimated architectural components: 9–10

### Technical Constraints & Dependencies

1. **Deterministic-generative boundary**: All clinical risk calculations, threshold logic, and metric derivations MUST be deterministic code. LLM restricted to interpreting, narrating, communicating results it never generated.
2. **LangGraph orchestration**: 6-node state machine with conditional transitions — architectural backbone for agent coordination.
3. **SQLite WAL**: Single-writer, read-concurrent local DB. No multi-process contention expected (single-user MVP).
4. **Git-versioned markdown profiles**: Narrative profiles are human-readable text files, not DB blobs. Version control is user-initiated, not automatic.
5. **Context-package injection**: Orchestrator prepares ALL context before Coach invocation. No on-demand RAG. Reduces hallucination vectors at cost of token budget management.
6. **Coros .fit protocol**: Garmin FIT SDK for parsing. Open standard — multi-platform extension is post-MVP.
7. **Provider-interchangeable LLM endpoint**: OpenAI API-compatible format. Provider swap = endpoint URL + credentials change only.
8. **CLI-only MVP**: No visual dashboard. Two interaction modes: conversational (--mode coach) and scriptable (--process, --batch, --report).
9. **Single-user design**: No multi-tenancy, no auth system beyond OS user, no concurrent access patterns.

### Cross-Cutting Concerns Identified

1. **Hallucination mitigation** — spans profiles, coach, hypothesis lifecycle. Mitigated by: evidence anchoring, context-package injection, deterministic boundary, hypothesis evidence thresholds.
2. **Evidence traceability** — every recommendation must cite source (KB document section, profile data point, or deterministic calculation). Affects coach prompts, profile output format, report generation.
3. **Data validation pipeline** — HR artifacts, GPS drift, cadence inconsistencies propagate confidence flags downstream to profiles and derived metrics. Affects pipeline → profile data contract.
4. **Profile domain separation** — zero cross-contamination between asthma and runner contexts. Only synthesis node sees both. Affects state schema, agent prompts, data flow.
5. **Hypothesis lifecycle enforcement** — transition rules (evidence thresholds, confidence scoring) cross pipeline → profiles → coach. Requires consistent enforcement across all agents.
6. **Audit trail** — NFR14 requires logging all health data read/write and profile updates. Affects DB schema, profile write operations.
7. **Wellness positioning** — disclaimers in every Coach session init and every medical report. Affects coach system prompt, report template.
8. **Token budget management** — context-package injection means all context must fit within LLM context window. Affects profile granularity, doc selection, conversation history truncation.

## Starter Template Evaluation

### Primary Technology Domain

CLI tool + AI/LLM orchestration + domain-specific data pipeline (healthcare/wellness)

### Starter Options Considered

No se evaluaron starters externos. El proyecto requiere una estructura custom por:

- Dominio específico (salud + running + asma) sin equivalentes en el mercado
- Arquitectura multi-agente LangGraph con frontera determinista-generativa
- SQLite local-first con git-versioned profiles
- CLI como única interfaz — sin web, sin dashboard

Un starter genérico Python/LangGraph agregaría complejidad innecesaria sin aportar al dominio.

### Selected Starter: Custom desde cero

**Rationale:** Proyecto con requisitos arquitectónicos singulares (separación determinista-generativa, hypothesis lifecycle state machine, BIE risk engine, profile domain isolation). Ningún starter cubre estos dominios. Desde cero da control total sobre la arquitectura y evita desaprendizaje.

### Stack Técnico Confirmado

| Decisión | Elección | Rationale |
|---|---|---|
| Lenguaje | Python 3.11+ | PRD requirement, ecosistema LangGraph |
| CLI framework | Typer | Type hints, autocompletion, moderno |
| Package manager | Poetry | Dependency lock, pyproject.toml nativo |
| Testing | pytest | Estándar de facto Python |
| Linting/Formatting | Ruff | Reemplaza flake8+isort+black, rápido |
| .fit parsing | fitparse | Librería madura para FIT protocol |
| LLM orchestration | LangGraph | PRD requirement, 6 nodos condicionales |
| DB | SQLite + WAL | PRD requirement, single-user local-first |
| Profiles | Markdown + git | PRD requirement, human-readable, auditable |
| LLM API | OpenAI-compatible | PRD requirement, provider-interchangeable |

### Estructura de Proyecto

```
run-intelligence/
├── pyproject.toml
├── src/
│   └── run_intelligence/
│       ├── __init__.py
│       ├── cli.py              # Typer entry point
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── fit_parser.py   # fitparse wrapper
│       │   ├── metrics.py      # Standard + asthma-aware derived metrics
│       │   ├── validation.py   # HR artifacts, GPS drift, cadence flags
│       │   └── runner.py       # Pipeline orchestration
│       ├── db/
│       │   ├── __init__.py
│       │   ├── models.py       # SQLite schema (runs, health_log, conversation_history, runner_metrics_history)
│       │   └── repository.py   # CRUD operations
│       ├── risk_engine/
│       │   ├── __init__.py
│       │   └── risk_engine.py   # Deterministic BIE risk calculator
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── asthma_profile.py
│       │   ├── runner_profile.py
│       │   ├── synthesis.py
│       │   └── coach.py
│       ├── orchestrator/
│       │   ├── __init__.py
│       │   └── graph.py         # LangGraph state + conditional transitions
│       ├── reports/
│       │   ├── __init__.py
│       │   └── medical_report.py
│       ├── health_log/
│       │   ├── __init__.py
│       │   └── cli_input.py     # Interactive health log prompts
│       └── config.py           # .env loading, constants
├── profiles/                    # Git-versioned markdown
│   ├── asma_profile.md
│   └── runner_profile.md
├── docs/                         # Scientific knowledge base
│   ├── base_cientifica_running.md
│   └── asma_running_base_teorica.md
├── tests/
│   ├── test_pipeline/
│   ├── test_risk_engine/
│   ├── test_agents/
│   ├── test_db/
│   └── test_reports/
└── data/
    └── run_intelligence.db       # SQLite (gitignored)
```

**Note:** Project initialization (`poetry init`, estructura de directorios, pyproject.toml, ruff config, pytest config) should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1a | ORM / data modeling | SQLAlchemy ORM + Alembic migrations | Robust schema management, migration history, extensible post-MVP |
| 1c | Data validation | Pydantic v2 | Runtime validation on every state transition, serialization, type safety |
| 2a | Encryption at rest | No encryption in MVP — OS-level auth sufficient | Single-user local-first, NFR13 satisfies access control, post-MVP add SQLCipher if needed |
| 3a | LangGraph state schema | TypedDict top-level + nested Pydantic models | LangGraph convention + runtime validation |
| 3a | Domain separation | Channel-level hard separation | Architectural guarantee of FR18, not prompt-dependent |
| 3a | Hypothesis model | Pydantic with lifecycle state machine | Enforces evidence thresholds, prevents unauthorized promotion |
| 3a | Risk assessment model | Structured Pydantic output | Deterministic-generative boundary, auditable, reproducible |
| 3b | Inter-node communication | Full-pass state | Aligned with context-package injection philosophy, simpler for 6-node linear+conditional flow |
| 3c | CLI output formats | stdout (summaries, responses, reports), stderr (warnings, flags, errors), JSON (internal risk_assessment), Markdown (profiles, reports) | PRD-specified, unix convention |

**Important Decisions (Shape Architecture):**

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1d | Profile format | Deterministic structure with sections + agent-generated narrative content | Structured sections for machine parsing, narrative content for human readability |
| 1d | Profile storage | Markdown files only — no DB duplication | Git-versioned markdown is the source of truth per PRD; agents read/write directly |
| 2b | API key management | python-dotenv + .gitignore | PRD requirement, no embedding in DB/profiles/git |
| 4a | Logging | Python stdlib logging + LOG_LEVEL env var | Sufficient for MVP, structured logging post-MVP |
| 4b | Config management | Pydantic BaseSettings | Natural fit with Pydantic decision, env var loading + validation |

**Deferred Decisions (Post-MVP):**

- SQLCipher encryption at rest
- Structured logging (structlog)
- Automated git commit on profile updates (MVP: user-initiated)
- Multi-platform .fit parsing (beyond Coros)
- Conversational health log input (Coach-mediated)
- Environment API module (weather, pollen, AQI)

### Data Architecture

#### Database: SQLite + SQLAlchemy ORM + Alembic

**Tables (defined in `db/models.py`):**

- `runs` — Raw + calculated metrics including subjective fields. Fitparse output, standard + asthma-aware derived metrics, data quality flags.
- `health_log` — Morning peak flow, sleep quality, asthma symptoms 0-3, RPE, SABA use, notes. Linked to run data by date.
- `conversation_history` — Session messages for Coach context. Persisted between invocations.
- `runner_metrics_history` — VO2max, VDOT, ACWR snapshots over time. Enables longitudinal analysis.
- `audit_log` — NFR14 requirement. Who (which agent/process) accessed/modified data and when.

**Migrations:** Alembic with versioned migration scripts. Initial schema auto-generated from SQLAlchemy models. Each migration versioned in `alembic/versions/`.

**Data Validation:** Pydantic models for all inputs/outputs:
- CLI input validation (health log prompts, .fit file paths)
- Pipeline output validation (metrics, flags)
- LLM output validation (profile updates, coach responses)
- Risk assessment validation (structured `{risk_level, factors, confidence, sources}`)

#### Profile Storage: Git-Versioned Markdown

**Profile structure** — deterministic sections with agent-generated narrative content:

```markdown
# [Asthma/Runner] Profile — [User]

## Active Triggers
[Agent-generated: confirmed trigger patterns with evidence]

## Hypotheses
### [Lifecycle State]: [Hypothesis Statement]
- Confidence: [low/medium/high] ([score]/1.0)
- Evidence: [N data points]
- Supporting data: [references to specific runs/logs]
- Sources: [cited doc sections]
- Last updated: [date]

## Key Metrics
- [Agent-generated metric summaries]

## Evolution History
- [Agent-generated: key changes with dates]

---
*Generated by Run Intelligence. Last updated: [date]*
```

**Source of truth:** Markdown files. No DB duplication. Agents read file content directly, write updated content, user controls git commits.

### Authentication & Security

**MVP Approach:**

- **No encryption at rest** — OS-level user authentication (NFR13). SQLite file in user directory with POSIX permissions. Single-user design makes multi-tenant encryption unnecessary.
- **API credentials** — `.env` file excluded from git via `.gitignore`. Never embedded in DB, profiles, or version-tracked files (NFR9).
- **Wellness disclaimers** — Hard-coded in Coach system prompt and report template. Not a configuration toggle — always present (NFR10, NFR11).
- **Audit trail** — `audit_log` table records all health data read/write and profile update operations (NFR14).
- **Data purge** — `python run.py --purge` command deletes all user data per NFR15.
- **LLM data handling** — Health data flows to LLM provider only during active Coach sessions. Documented privacy tradeoff per NFR8.

**Post-MVP:** Add SQLCipher for at-rest encryption if sharing becomes a requirement.

### API & Communication Patterns

#### LangGraph State Schema

**Top-level state** — TypedDict (LangGraph convention) with nested Pydantic models (runtime validation):

```python
class RunIntelligenceState(TypedDict):
    # Pipeline output
    run_data: RunData | None
    health_log_entry: HealthLogEntry | None

    # Domain-isolated channels
    asthma_state: AsthmaDomainState
    runner_state: RunnerDomainState

    # Synthesis output
    synthesis_text: str | None
    conflict_flag: bool
    conflict_details: str | None

    # BIE Risk Assessment (conditional node)
    risk_assessment: RiskAssessment | None

    # Coach context
    context_package: ContextPackage | None
    coach_response: str | None

    # Conversation
    messages: list[BaseMessage]
```

**Domain state models** — channel-level hard separation enforces FR18:

```python
class AsthmaDomainState(BaseModel):
    profile_text: str
    hypotheses: list[Hypothesis]
    relevant_docs: list[str]
    trigger_history: list[TriggerEvent]

class RunnerDomainState(BaseModel):
    profile_text: str
    hypotheses: list[Hypothesis]
    relevant_docs: list[str]
    metrics_history: list[MetricsSnapshot]
```

**Hypothesis lifecycle model** — state machine with evidence thresholds:

```python
class Hypothesis(BaseModel):
    id: str
    statement: str
    lifecycle: Literal["proposed", "testing", "confirmed", "contradicted", "archived"]
    confidence: float  # 0-1 (low ≤0.33, medium 0.34-0.66, high ≥0.67)
    evidence_count: int
    supporting_data: list[str]
    sources: list[str]
    created_date: date
    last_updated: date
```

**Lifecycle transition rules (enforced in code, not LLM):**
- `proposed` → `testing`: ≥2 data points with cross-referenced objective+subjective data
- `testing` → `confirmed`: ≥5 data points with consistent pattern
- `testing` → `contradicted`: ≥2 data points contradicting, stronger evidence than supporting
- `proposed` stuck after 10 runs → flagged for review, never auto-promoted

**Risk Assessment model** — deterministic output, never LLM-generated:

```python
class RiskAssessment(BaseModel):
    risk_level: Literal["low", "moderate", "high", "very_high"]
    factors: list[RiskFactor]
    confidence: float
    sources: list[str]

class RiskFactor(BaseModel):
    name: str
    value: str
    weight: int  # 1-5
    source: str  # clinical reference
```

#### Data Flow Enforcement

**Domain separation guarantee:**
- `AsthmaProfile` node receives only `asthma_state` + `run_data` + `health_log_entry`
- `RunnerProfile` node receives only `runner_state` + `run_data`
- `Synthesis` node receives both domain states
- `Coach` receives full `context_package` (both profiles + docs + synthesis + risk)
- Profile agents cannot access each other's domain state — enforced at orchestration level, not prompt level

**Deterministic-generative boundary:**
- `risk_engine.py` receives structured inputs → returns `RiskAssessment` (Pydantic validated)
- `pipeline.py` receives .fit data → returns `RunData` (Pydantic validated)
- All clinical threshold calculations in deterministic code
- LLM agents restricted to: interpretation, narration, communication of pre-computed results

#### CLI Output Convention

| Stream | Content | Destination |
|---|---|---|
| stdout | Pipeline summaries, Coach responses, report output | Terminal / `--output` file |
| stderr | Validation warnings, HR artifacts, GPS drift, errors | Terminal / pipe filtering |
| JSON (internal) | `RiskAssessment` structured output | Consumed by Coach, not displayed directly |
| Markdown | Profile updates, medical reports | `profiles/` dir / `--output` file |

### Decision Impact Analysis

**Implementation Sequence:**

1. Project init (poetry, pyproject.toml, ruff, pytest, directory structure)
2. SQLAlchemy models + Alembic initial migration
3. Pipeline module (fitparse → RunData → validation flags)
4. Risk engine (deterministic RiskAssessment calculator)
5. Pydantic state models (domain states, hypotheses, context package)
6. LangGraph orchestrator (state schema, node definitions, conditional transitions)
7. Profile agents (asthma, runner) with hypothesis lifecycle
8. Synthesis node + conflict detection
9. Coach with context package injection
10. CLI entry points (Typer commands)
11. Medical report generator
12. Audit logging + data purge

**Cross-Component Dependencies:**

- SQLAlchemy models ↔ Alembic ↔ All modules (data persistence layer)
- Pydantic state models ↔ LangGraph orchestrator (state transit between nodes)
- Pydantic models ↔ Profile agents (hypothesis lifecycle validation)
- Risk engine ↔ Coach (deterministic output → generative interpretation)
- Pipeline validation ↔ Profile agents (data quality flags propagate)
- Domain state separation ↔ LangGraph routing (asthma_state ≠ runner_state access)

## Implementation Patterns & Consistency Rules

### Conflict Points Identified

**24 areas** where AI agents could make inconsistent choices, organized into 6 categories:

### Naming Patterns

**Database:**
- Tables: `snake_case`, singular for uncountable — `runs`, `health_log`, `conversation_history`, `runner_metrics_history`, `audit_log`
- Columns: `snake_case` — `run_id`, `created_at`, `hr_max`, `pace_avg`, `data_quality_flags`
- Foreign keys: `{singular_table}_id` — `run_id`, `health_log_id`
- Indexes: `idx_{table}_{column}` — `idx_runs_created_at`

**Python Code:**
- Modules: `snake_case` — `risk_engine.py`, `fit_parser.py`, `cli_input.py`
- Classes: `PascalCase` — `RunData`, `HealthLogEntry`, `RiskAssessment`, `Hypothesis`
- Functions: `snake_case` — `calculate_hr_pace_drift()`, `parse_fit_file()`, `detect_hr_artifacts()`
- Constants: `UPPER_SNAKE_CASE` — `MAX_HR_BPM`, `MIN_EVIDENCE_CONFIRMED`, `BIE_TEMP_THRESHOLD`
- Private functions: `_leading_underscore` — `_format_profile_section()`

**Pydantic Models:**
- Model names: `PascalCase` matching domain concept — `RunData`, `Hypothesis`, `RiskAssessment`
- Fields: `snake_case` — `risk_level`, `confidence`, `evidence_count`
- JSON serialization: `by_alias=False` — keep snake_case in JSON, no camelCase conversion

**Files & Directories:**
- Implementation: `src/run_intelligence/{module}/`
- Tests: `tests/test_{module}/` mirroring `src/` structure
- Profiles: `profiles/{type}_profile.md` — `asma_profile.md`, `runner_profile.md`
- Docs: `docs/*.md` — existing knowledge base files

### Structure Patterns

**Project Organization:**
- Single package: `run_intelligence` under `src/`
- Sub-packages by domain: `pipeline/`, `db/`, `risk_engine/`, `agents/`, `orchestrator/`, `reports/`, `health_log/`
- `config.py` at package root — constants, env vars, thresholds
- `cli.py` at package root — Typer entry point
- Tests mirror src structure: `tests/test_pipeline/`, `tests/test_risk_engine/`, etc.

**Cross-cutting module: `config.py`:**
- All clinical thresholds (GINA, ACSM, Daniels) as named constants
- All configuration via `BaseSettings` (Pydantic) → env vars with defaults
- Thresholds grouped: `BIE_THRESHOLDS`, `HR_LIMITS`, `HYPOTHESIS_RULES`

**Where Pydantic models live:**
- State models (LangGraph state schema): `orchestrator/state.py`
- Domain models (RunData, Hypothesis, etc.): in their respective domain modules
- DB models (SQLAlchemy): `db/models.py`
- NEVER create a separate `models/` package — models live with their domain

**Where constants live:**
- Clinical thresholds: `config.py` — single source of truth
- Pipeline validation thresholds: `config.py`
- NEVER hardcode thresholds in agent prompts or risk_engine logic — reference config

### Format Patterns

**Risk Assessment JSON output (internal) — ALWAYS this structure:**
```json
{
    "risk_level": "low | moderate | high | very_high",
    "factors": [
        {"name": "temperature", "value": "8°C", "weight": 4, "source": "GINA 2024 Track 1"}
    ],
    "confidence": 0.75,
    "sources": ["GINA 2024 Track 1", "Anderson et al. 2000"]
}
```

**Datetime handling:**
- Internal: `datetime.date` for dates, `datetime.datetime` for timestamps
- DB storage: ISO 8601 strings
- Profile markdown: `DD/MM/YYYY` (user-facing, Argentine format)
- NEVER use epoch timestamps

**Error output:**
- Pipeline errors → stderr with structured format: `[PIPELINE_ERROR] {module}: {message}`
- Validation warnings → stderr: `[VALIDATION_WARNING] {metric}: {details}`
- LLM failures → `coach_response` field in state with error message + user-facing apology
- NEVER raise exceptions that crash the CLI without user-facing message

**Profile markdown format:**
- UTF-8 encoding
- Sections with `##` headings (deterministic structure)
- Hypotheses with `### {lifecycle}: {statement}`
- Data with bullet points
- Footer with generation timestamp

### Communication Patterns

**Inter-node state passing:**
- Full state access: Pipeline, Synthesis, Coach
- Domain-restricted: Asthma Profile (no `runner_state`), Runner Profile (no `asthma_state`)
- Enforced by orchestrator routing, NOT by prompt instruction
- Each node reads what it needs from state, writes ONLY its designated fields

**Node write fields (ONLY these — NEVER write outside your lane):**

| Node | Writes to | Reads from |
|---|---|---|
| Pipeline | `run_data` | .fit file input |
| Asthma Profile | `asthma_state` | `run_data`, `health_log_entry`, asthma docs |
| Runner Profile | `runner_state` | `run_data`, runner docs |
| Synthesis | `synthesis_text`, `conflict_flag`, `conflict_details` | `asthma_state`, `runner_state` |
| BIE Risk | `risk_assessment` | `asthma_state`, env/health inputs |
| Coach | `coach_response` | `context_package` (all) |

**Error propagation in state:**
- Nodes return updated state, NEVER raise exceptions into LangGraph
- Error states captured in dedicated fields: `error_message: str | None`
- Coach handles errors by presenting user-facing message
- Pipeline errors on individual .fit files → logged to stderr, batch continues

**LLM output validation:**
1. Structured outputs (profile updates, hypothesis state changes) → ALWAYS validated with Pydantic schema before writing to state
2. Narrative outputs (coach responses, profile narrative text) → NOT Pydantic-validated (free text), but checked for minimum length and disclaimer presence
3. Retry strategy: max 2 retries with temperature 0 for structured outputs. If still fails → error in state, fallback message to user

### Process Patterns

**Deterministic-generative boundary enforcement:**
- `pipeline/`, `risk_engine/`, and threshold logic in `config.py` are DETERMINISTIC — no LLM calls, no randomness, same input → same output
- `agents/` modules are GENERATIVE — LLM produces narrative + structured updates, validated post-hoc
- `risk_engine.py` returns `RiskAssessment` Pydantic model → Coach receives this as read-only context → Coach NEVER recalculates risk
- Pipeline metrics → Profile agents receive as read-only context → agents NEVER recalculate metrics
- Health log data → Profile agents receive as evidence → agents NEVER modify health log entries

**Hypothesis lifecycle enforcement:**
- State transitions checked in code BEFORE writing to profile
- Evidence count validated against thresholds in `config.py`
- Promotion to `confirmed` requires `≥5` supporting data points — this check runs in Python, NOT in LLM prompt
- LLM can propose hypotheses, but lifecycle transitions are deterministic code

**Config pattern — single source of truth:**
```python
# config.py
HYPOTHESIS_RULES = {
    "min_evidence_testing": 2,
    "min_evidence_confirmed": 5,
    "min_evidence_contradicted": 2,
    "max_runs_before_review": 10,
    "confidence_levels": {"low": (0, 0.33), "medium": (0.34, 0.66), "high": (0.67, 1.0)},
}

BIE_THRESHOLDS = {
    "temperature_risk": {"very_high": 5, "high": 10, "moderate": 15},
    "humidity_risk": {"very_high": 40, "high": 55},
    "saba_protection_factor": 3,
}

HR_LIMITS = {
    "artifact_threshold_bpm": 220,
    "gps_drift_mps": 50,
    "cadence_change_pct": 20,
}
```

**Logging pattern:**
- `DEBUG`: Internal state changes, Pydantic validation details, LLM prompts
- `INFO`: Pipeline stages completed, profile updates, coaching sessions started/ended
- `WARNING`: Data quality flags (HR artifacts, GPS drift, low confidence metrics)
- `ERROR`: Pipeline failures, LLM API errors, validation failures
- `LOG_LEVEL` env var controls output (default `INFO`)

**Wellness disclaimer enforcement:**
- Every Coach session start → disclaimer injected in system prompt
- Every medical report → disclaimer section auto-generated
- Disclaimers are in `config.py` constants, NEVER in agent prompts directly (single source of truth)

### Enforcement Guidelines

**All AI Agents MUST:**

1. Reference `config.py` for ALL thresholds and constants — NEVER hardcode clinical values
2. Validate LLM structured outputs with Pydantic BEFORE writing to state
3. Write ONLY to designated state fields per node lane diagram — NEVER write outside your lane
4. Use `snake_case` for everything except classes (`PascalCase`) and constants (`UPPER_SNAKE_CASE`)
5. Include wellness disclaimers from config — NEVER embed disclaimer text in prompts
6. Follow deterministic-generative boundary — deterministic code NEVER calls LLM, generative code NEVER calculates clinical values
7. Propagate data quality flags from pipeline through to profiles — NEVER silently drop validation warnings
8. Use ISO 8601 for internal dates, DD/MM/YYYY for user-facing text
9. Handle errors via state fields, not exceptions — NEVER crash CLI without user-facing message
10. Write tests in `tests/test_{module}/` mirroring `src/run_intelligence/{module}/` structure

### Pattern Examples

**Good:**
```python
# risk_engine.py — deterministic
from ..config import BIE_THRESHOLDS

def calculate_bie_risk(inputs: BIERiskInput) -> RiskAssessment:
    temp_factor = _assess_temperature(inputs.temperature)
    return RiskAssessment(risk_level=..., factors=..., confidence=..., sources=...)
```

**Anti-patterns:**
```python
# NEVER hardcode threshold in prompt
prompt = "If temperature is below 10°C, BIE risk is high."

# NEVER let LLM calculate risk
prompt = "Calculate the BIE risk level based on these inputs."

# NEVER read across domain boundaries
runner_data = state["runner_state"]  # in asthma_profile node
```

## Project Structure & Boundaries

### Complete Project Directory Structure

```
run-intelligence/
├── pyproject.toml                    # Poetry config, deps, scripts, ruff, pytest
├── alembic.ini                      # Alembic configuration
├── .env.example                     # Template with all required env vars
├── .gitignore                       # Python, .env, data/, __pycache__, .db
├── README.md                        # Setup, usage, architecture overview
│
├── alembic/                         # Database migrations
│   ├── env.py
│   ├── versions/
│   │   └── 001_initial_schema.py    # runs, health_log, conversation_history, runner_metrics_history, audit_log
│
├── src/run_intelligence/
│   ├── __init__.py
│   ├── cli.py                       # Typer entry point (--mode coach, --process, --batch, --log-health, --report, --purge)
│   ├── config.py                    # BaseSettings, BIE_THRESHOLDS, HR_LIMITS, HYPOTHESIS_RULES, disclaimers
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── fit_parser.py            # fitparse wrapper → raw metric extraction
│   │   ├── metrics.py               # Standard + asthma-aware derived metrics calculation
│   │   ├── validation.py            # HR artifacts, GPS drift, cadence flags, low-confidence marking
│   │   └── runner.py                # Pipeline orchestration: parse → calculate → validate → RunData
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py                # SQLAlchemy models (runs, health_log, conversation_history, runner_metrics_history, audit_log)
│   │   ├── repository.py            # CRUD operations, queries, data persistence
│   │   └── session.py              # SQLAlchemy engine, session factory, WAL config
│   │
│   ├── risk_engine/
│   │   ├── __init__.py
│   │   ├── risk_engine.py           # Deterministic BIE risk calculator
│   │   └── thresholds.py            # GINA/ACSM/Anderson threshold tables (imports from config)
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── asthma_profile.py        # Asthma Profile agent (writes to asthma_state)
│   │   ├── runner_profile.py        # Runner Profile agent (writes to runner_state)
│   │   ├── synthesis.py             # Synthesis node (writes synthesis_text, conflict detection)
│   │   ├── coach.py                 # Coach agent (writes coach_response)
│   │   └── prompts.py               # All agent system prompts, disclaimer templates, source citation instructions
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── graph.py                 # LangGraph StateGraph definition, node registration, conditional edges
│   │   ├── state.py                 # RunIntelligenceState, AsthmaDomainState, RunnerDomainState, Hypothesis, RiskAssessment, etc.
│   │   └── context_builder.py       # Context package assembly (profiles + docs + history → ContextPackage)
│   │
│   ├── reports/
│   │   ├── __init__.py
│   │   └── medical_report.py        # Monthly medical report generator (structured markdown)
│   │
│   ├── health_log/
│   │   ├── __init__.py
│   │   └── cli_input.py             # Interactive Typer prompts for health log entry
│   │
│   └── profiles/
│       ├── __init__.py
│       ├── reader.py                # Read profile markdown, parse sections
│       └── writer.py                # Write profile markdown, preserve structure
│
├── profiles/                         # Git-versioned markdown profiles (source of truth)
│   ├── asma_profile.md              # Asthma Profile — deterministic sections + agent narrative
│   └── runner_profile.md            # Runner Profile — deterministic sections + agent narrative
│
├── docs/                              # Scientific knowledge base (read-only by agents)
│   ├── base_cientifica_running.md   # Running science reference
│   └── asma_running_base_teorica.md  # Asthma science reference
│
├── tests/
│   ├── conftest.py                   # Shared fixtures, mock .fit files, test DB
│   ├── test_pipeline/
│   │   ├── test_fit_parser.py
│   │   ├── test_metrics.py
│   │   ├── test_validation.py
│   │   └── test_runner.py
│   ├── test_risk_engine/
│   │   ├── test_risk_engine.py       # Deterministic: same inputs → same outputs
│   │   └── test_thresholds.py
│   ├── test_agents/
│   │   ├── test_asthma_profile.py
│   │   ├── test_runner_profile.py
│   │   ├── test_synthesis.py
│   │   └── test_coach.py
│   ├── test_db/
│   │   ├── test_models.py
│   │   └── test_repository.py
│   ├── test_orchestrator/
│   │   ├── test_graph.py             # Node transitions, conditional routing, state flow
│   │   ├── test_state.py             # Pydantic validation, lifecycle transitions
│   │   └── test_context_builder.py
│   ├── test_reports/
│   │   └── test_medical_report.py
│   └── test_health_log/
│       └── test_cli_input.py
│
├── data/                             # SQLite database (gitignored)
│   └── run_intelligence.db
│
└── scripts/                          # Utility scripts
    └── seed_profiles.py              # Initialize profile templates for first run
```

### Architectural Boundaries

**Deterministic Boundary:**
- `pipeline/` — NO LLM calls. Pure Python + fitparse. Same `.fit` file → identical `RunData` output.
- `risk_engine/` — NO LLM calls. Pure math + thresholds from `config.py`. Same inputs → identical `RiskAssessment`.
- `config.py` thresholds — Single source of truth. No clinical values in prompts, agents, or LLM instructions.
- `db/` — Data persistence only. No business logic.

**Generative Boundary:**
- `agents/` — LLM calls allowed. Structured outputs validated by Pydantic before writing to state.
- `prompts.py` — All LLM system prompts centralized. Source citation instructions, disclaimers, domain constraints.
- Coach receives deterministic results as read-only context and translates to natural language. Never recalculates.

**Data Boundary:**
- `db/repository.py` is the ONLY module that touches SQLite directly. All other modules go through repository.
- `profiles/reader.py` and `profiles/writer.py` are the ONLY modules that read/write profile markdown files.
- `health_log/cli_input.py` collects user input → passes to database via `repository.py`. Never directly writes files.
- `orchestrator/context_builder.py` is the ONLY module that combines all three data sources (profiles, docs, history).

**Domain Isolation Boundary:**
- `asthma_profile.py` can ONLY read `asthma_state`, `run_data`, `health_log_entry`, and asthma-relevant docs.
- `runner_profile.py` can ONLY read `runner_state`, `run_data`, and running-relevant docs.
- Enforced in `orchestrator/graph.py` through state routing — NOT in prompts.

### Requirements to Structure Mapping

| FR Category | Module(s) | Key Files |
|---|---|---|
| FR1–FR7: Run Data Ingestion | `pipeline/` | `fit_parser.py`, `metrics.py`, `validation.py`, `runner.py` |
| FR8–FR14: Asthma-Aware Analytics | `agents/asthma_profile.py`, `pipeline/metrics.py` | Hypothesis lifecycle in `orchestrator/state.py` |
| FR15–FR17: Health Logging | `health_log/`, `db/` | `cli_input.py`, `models.py`, `repository.py` |
| FR18–FR24: Profile Intelligence | `agents/`, `profiles/`, `orchestrator/` | `asthma_profile.py`, `runner_profile.py`, `synthesis.py`, `reader.py`, `writer.py` |
| FR25–FR31: Coaching & Decision Support | `agents/coach.py`, `risk_engine/`, `orchestrator/` | `coach.py`, `risk_engine.py`, `context_builder.py` |
| FR32–FR35: Medical Reporting | `reports/` | `medical_report.py` |
| FR36–FR43: Data Management & Config | `db/`, `cli.py`, `config.py` | `repository.py`, `session.py`, `cli.py` |
| FR45–FR46: Orchestration | `orchestrator/` | `graph.py`, `state.py` |
| NFR1–NFR5: Performance | All modules | Pipeline ≤5s, context ≤2s, risk ≤1s |
| NFR6–NFR15: Security & Privacy | `config.py`, `db/`, `cli.py` | `.env` handling, audit log, purge command, disclaimers |
| NFR16–NFR20: Integration | `pipeline/fit_parser.py`, `orchestrator/` | `.fit` parsing, LLM provider interchangeability |

**Cross-cutting concerns:**

| Concern | Location | Mechanism |
|---|---|---|
| Data validation flags | `pipeline/validation.py` → state → agents | Flags propagate via `run_data.data_quality_flags` |
| Hypothesis lifecycle | `orchestrator/state.py` → `agents/*.py` | Transitions enforced in Python before profile write |
| Evidence traceability | `agents/prompts.py`, `reports/` | Source citation instructions in every agent prompt |
| Wellness disclaimers | `config.py` → `agents/prompts.py` → `reports/` | Constants injected, never hardcoded |
| Audit logging | `db/repository.py` | Every health data read/write logged to `audit_log` table |

### Integration Points

**Internal Communication — Data Flow:**

```
CLI (Typer)
  ├── --process <file.fit> ─→ pipeline/runner.py ─→ RunData ─→ orchestrator/graph.py
  ├── --mode coach ─────────→ orchestrator/graph.py ─→ Coach ─→ coach_response → stdout
  ├── --log-health ─────────→ health_log/cli_input.py ─→ HealthLogEntry ─→ db/repository.py
  ├── --batch <dir> ────────→ pipeline/runner.py (loop) ─→ RunData[] ─→ orchestrator/graph.py
  └── --report <month> ─────→ db/repository.py ─→ reports/medical_report.py ─→ stdout/--output

LangGraph Flow:
  Pipeline ─→ AsthmaProfile ─┐
  Pipeline ─→ RunnerProfile ──┤─→ Synthesis ─→ [BIE Risk?] ─→ Coach ─→ response
                               ↑──── conflict detection ──────↑
```

**External Integration — Only one:**

| Integration | Module | Config | Direction |
|---|---|---|---|
| LLM API (OpenAI-compatible) | `orchestrator/graph.py` via LangGraph | `LLM_API_KEY`, `LLM_MODEL`, `LLM_ENDPOINT` in `.env` | Outbound only, during Coach/Profile invocations |

**End-to-end Data Flow:**

1. User runs `python run.py --process run.fit`
2. `cli.py` → `pipeline/runner.py` → fitparse → raw metrics → `metrics.py` → derived metrics → `validation.py` → flags → `RunData` Pydantic model
3. `RunData` → `db/repository.py` → SQLite `runs` table
4. If Coach mode: `orchestrator/graph.py` assembles `RunIntelligenceState`
5. `AsthmaProfile` node reads `asthma_state` + `run_data` + `health_log_entry` + docs → writes `asthma_state`
6. `RunnerProfile` node reads `runner_state` + `run_data` + docs → writes `runner_state`
7. `Synthesis` node reads both states → writes `synthesis_text`, `conflict_flag`
8. Conditional: if user asks BIE risk → `risk_engine.py` (deterministic) → `RiskAssessment`
9. `Coach` node receives full context package → writes `coach_response`
10. `coach_response` → stdout + `db/repository.py` → `conversation_history`

### File Organization Patterns

**Configuration:**
- `pyproject.toml` — Poetry deps, ruff config, pytest config, CLI entry point
- `.env.example` — Template with all var names, no real values
- `.env` — REAL values, gitignored
- `config.py` — `BaseSettings` loads from env, adds app-level constants/thresholds

**Source organization:**
- Domain-driven sub-packages under `src/run_intelligence/`
- Each sub-package is a bounded context with clear responsibilities
- Shared models in `orchestrator/state.py` — not scattered across modules
- Shared prompts in `agents/prompts.py` — not duplicated in agent files

**Test organization:**
- Mirror `src/` structure under `tests/`
- `conftest.py` provides shared fixtures (test DB, mock .fit data, mock LLM responses)
- `test_risk_engine.py` — deterministic assertions: same inputs → same outputs
- `test_state.py` — Pydantic validation, hypothesis lifecycle transitions
- `test_graph.py` — LangGraph node transitions, conditional routing, domain isolation

**Asset organization:**
- `profiles/` — git-versioned markdown (user commits manually)
- `docs/` — read-only scientific knowledge base
- `data/` — SQLite DB, gitignored
- `scripts/` — utility scripts (seed profiles, etc.)

### Development Workflow

**Run commands:**
```bash
# Install
poetry install

# Process a single .fit file
poetry run python -m run_intelligence --process data/runs/morning_run.fit

# Batch process
poetry run python -m run_intelligence --batch data/runs/

# Interactive coach mode
poetry run python -m run_intelligence --mode coach

# Health log entry
poetry run python -m run_intelligence --log-health

# Monthly report
poetry run python -m run_intelligence --report 2026-05

# Dry run (validate without writing)
poetry run python -m run_intelligence --process data/runs/test.fit --dry-run

# Verbose output
poetry run python -m run_intelligence --process data/runs/test.fit --verbose

# Run tests
poetry run pytest

# Lint + format
poetry run ruff check . && poetry run ruff format .

# DB migration
poetry run alembic upgrade head
```

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- Python 3.11+ + LangGraph + SQLAlchemy + Pydantic + Typer → stack coherente, sin conflictos de versión
- LangGraph usa TypedDict como convención de state → nuestro TypedDict con Pydantic anidado es compatible
- SQLite WAL + single-user MVP → sin contención multi-proceso, consistente con NFR19
- fitparse (pure Python) → sin conflictos con SQLAlchemy o LangGraph
- Alembic migrations → consistente con SQLAlchemy ORM decision
- Poetry + Ruff + pytest → ecosistema Python moderno sin superposición

**Pattern Consistency:**
- snake_case en DB, código, JSON → consistente en todos los niveles
- Pydantic validation en state transitions → consistente con LangGraph node inputs/outputs
- Domain isolation enforced en orchestrator/graph.py → consistente con FR18 y el state schema
- Deterministic-generative boundary → consistente entre risk_engine, pipeline (deterministic) y agents (generative)

**Structure Alignment:**
- Estructura de dominio por sub-package → alinea con boundaries de aislamiento
- `config.py` como single source of truth para thresholds → alinea con deterministic boundary
- `orchestrator/state.py` centraliza todos los modelos → alinea con state schema decision
- Profiles en filesystem + DB solo para structured data → alinea con git-versioned markdown decision

### Requirements Coverage Validation ✅

**Functional Requirements Coverage:**

| FR Category | Architectural Support | Module | Status |
|---|---|---|---|
| FR1–FR7: Run Data Ingestion | Pipeline con fitparse, metrics, validation, batch | `pipeline/` | ✅ |
| FR8–FR14: Asthma-Aware Analytics | Hypothesis lifecycle con Pydantic state machine, evidence thresholds | `orchestrator/state.py`, `agents/asthma_profile.py` | ✅ |
| FR15–FR17: Health Logging | Typer CLI prompts, DB persistence | `health_log/`, `db/` | ✅ |
| FR18–FR24: Profile Intelligence | Domain-isolated states, synthesis con conflict detection, git profiles | `agents/`, `profiles/`, `orchestrator/` | ✅ |
| FR25–FR31: Coaching & Decision Support | Context-package injection, evidence-anchored prompts, deterministic risk engine | `agents/coach.py`, `risk_engine/`, `orchestrator/context_builder.py` | ✅ |
| FR32–FR35: Medical Reporting | Structured markdown report con clinical citation | `reports/medical_report.py` | ✅ |
| FR36–FR43: Data Management & Config | SQLite WAL, .env config, verbose/dry-run, purge, stdout/stderr | `db/`, `cli.py`, `config.py` | ✅ |
| FR45–FR46: Orchestration | LangGraph 6-node graph con conditional transitions | `orchestrator/graph.py` | ✅ |

**Non-Functional Requirements Coverage:**

| NFR | Architectural Support | Status |
|---|---|---|
| NFR1: Pipeline ≤5s | Pure Python + fitparse, no LLM in pipeline | ✅ |
| NFR2: Context ≤2s | Local DB reads + profile file reads, no RAG | ✅ |
| NFR3: BIE Risk deterministic ≤1s | Pure math + threshold tables, no LLM | ✅ |
| NFR4: Batch independence | Independent file processing, error per file | ✅ |
| NFR5: Profile update latency | Bounded by LLM, not local processing | ✅ |
| NFR6–NFR11: Security | Local-first, .env, disclaimers, deterministic risk | ✅ |
| NFR12: Encryption at rest | Deferred to post-MVP (OS-level auth for MVP) | ⚠️ Post-MVP |
| NFR13: OS-level auth | Single-user, local machine | ✅ |
| NFR14: Audit trail | `audit_log` table in DB | ✅ |
| NFR15: Data purge | `--purge` CLI command | ✅ |
| NFR16–NFR20: Integration | fitparse, OpenAI-compatible, git, SQLite WAL, stdout/stderr | ✅ |

### Implementation Readiness Validation ✅

**Decision Completeness:**
- ✅ Todas las decisiones críticas documentadas con rationale
- ✅ Stack técnico completo con versiones y alternativas
- ✅ Patrones de implementación con ejemplos y anti-patrones
- ✅ Enforcement guidelines para AI agents

**Structure Completeness:**
- ✅ Directorio completo con todos los archivos
- ✅ Boundaries arquitectónicas definidas (deterministic, generative, data, domain isolation)
- ✅ Integration points mapeados (LLM API como único externo)
- ✅ Data flow end-to-end documentado
- ✅ Requirements mapped a modules y files

**Pattern Completeness:**
- ✅ Naming conventions (DB, Python, Pydantic, files)
- ✅ Structure patterns (project org, config, models location)
- ✅ Format patterns (JSON dates, error output, profile markdown)
- ✅ Communication patterns (state passing, lane assignments, error propagation)
- ✅ Process patterns (deterministic boundary, hypothesis lifecycle, config, logging)

### Gap Analysis Results

**Critical Gaps:** None

**Important Gaps:**

1. **NFR12 — Encryption at rest** — explícitamente diferido a post-MVP con SQLCipher. OS-level auth satisface NFR13 para single-user. Documentado y aceptado.
2. **Conversation history truncation** — PRD dice "persisted between sessions" (FR43) pero no especifica estrategia de truncation por token budget. Se resuelve con `MAX_CONVERSATION_HISTORY` configurable en `config.py`. Implementation detail, no architectural gap.
3. **Profile narrative update mechanism** — agentes generan perfil completo con estructura determinista preservada. `profiles/writer.py` preserva secciones fijas y reemplaza contenido narrativo. Prompt engineering detail, no structural gap.

**Nice-to-Have Gaps:**

1. CI/CD pipeline — post-MVP cuando haya deployment objectives
2. Docker configuration — single-user local CLI no necesita containerization para MVP
3. Structured logging (structlog) — post-MVP enhancement documentado

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
- Deterministic-generative boundary is architecturally enforced, not prompt-dependent
- Domain isolation (asthma ↔ runner) is guaranteed at the orchestration level via channel-level state routing
- Hypothesis lifecycle transitions are enforced in Python code with configurable thresholds, not delegated to LLM
- Single source of truth in `config.py` for all clinical values prevents hardcoding
- Clear implementation patterns with enforcement guidelines give AI agents unambiguous rules

**Areas for Future Enhancement:**
- SQLCipher encryption at rest (post-MVP)
- Structured logging with structlog (post-MVP)
- Automated git commits on profile updates (post-MVP, user-controlled in MVP)
- Conversation history truncation strategy (implementation detail, configurable in `config.py`)

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented in this file
- Use implementation patterns consistently across all components
- Respect project structure and boundaries
- Refer to this document for all architectural questions
- When in doubt, follow the deterministic-generative boundary: if it's a calculation, it's code; if it's interpretation, it's LLM

**First Implementation Priority:**
```bash
poetry init
```
Then: SQLAlchemy models + Alembic initial migration → Pipeline module → Risk engine → Pydantic state models → LangGraph orchestrator → Profile agents → Synthesis → Coach → CLI → Reports → Audit logging