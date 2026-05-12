---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
inputDocuments:
  - /home/lpintos/proyectos/run-intelligence/planning/planning-artifacts/prd.md
  - /home/lpintos/proyectos/run-intelligence/planning/planning-artifacts/architecture.md
---

# run-intelligence - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for run-intelligence, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**Run Data Ingestion:**
FR1: User can process .fit files from Coros watches to extract standard running metrics (pace, HR, cadence, zones)
FR2: User can process .fit files to derive asthma-aware metrics (HR/pace drift, HR variability as bronchospasm signal, HR zone distribution anomalies, cadence compensations)
FR3: System can detect and flag HR artifacts (values exceeding physiological plausibility thresholds of >220 bpm or exhibiting sudden spikes inconsistent with adjacent data points) during data ingestion
FR4: System can detect and flag GPS drift anomalies (position jumps exceeding 50 meters per second not consistent with recorded pace) during data ingestion
FR5: System can flag derived metrics as low-confidence (confidence score below 0.5 on a 0-1 scale) when underlying data contains flagged artifacts or anomalies
FR6: User can process individual .fit files via dedicated processing command
FR7: User can batch process all .fit files in a specified directory
FR46: System can detect and flag cadence inconsistencies (sudden cadence changes exceeding 20% between consecutive data segments not attributable to pace changes) during data ingestion

**Asthma-Aware Analytics:**
FR8: Asthma Profile can propose trigger hypotheses from run data and health logs spanning ≥3 processed runs with corresponding symptom reports
FR9: Asthma Profile can advance hypothesis lifecycle states (proposed → testing → confirmed/contradicted → archived) based on minimum evidence thresholds (≥5 supporting data points with cross-referenced objective and subjective data for promotion to confirmed)
FR10: Asthma Profile can cross-reference objective metrics (HR/pace drift percentage) with subjective symptom reports (user-reported 0-3 scale) to validate or contradict hypotheses
FR11: Asthma Profile can seed with clinical thresholds from embedded knowledge base (GINA 2024, ACSM) when fewer than 3 runs with health logs have been processed
FR12: Runner Profile can propose, test, and confirm performance and training patterns using the same hypothesis lifecycle with confidence levels (low: 1-2 data points, medium: 3-4, high: ≥5)
FR13: System can maintain hypothesis confidence levels quantified on a defined scale (low: ≤0.33, medium: 0.34-0.66, high: ≥0.67) reflecting the number and consistency of supporting evidence
FR14: System can prevent hypothesis promotion to confirmed state without meeting minimum evidence thresholds (≥5 supporting data points with consistent patterns across objective metrics and/or subjective reports)
FR44: System can downgrade or withhold hypothesis promotion when underlying data contains flagged artifacts, anomalies, or confidence scores below the minimum threshold for that lifecycle state

**Health Logging:**
FR15: User can log health data interactively including morning peak flow, sleep quality, post-run RPE, asthma symptoms (0-3 scale), rescue inhaler use, and notes
FR16: System can associate health log entries with corresponding run data for cross-referencing
FR17: System can use subjective health log data as evidence in hypothesis lifecycle alongside objective metrics

**Profile Intelligence:**
FR18: System can maintain separate Asthma Profile and Runner Profile that operate with domain-isolated boundaries — asthma context appears only in Asthma Profile and running metrics context appears only in Runner Profile
FR19: System can produce a Synthesis that presents unified status (fitness trend, asthma alert level, load status) while preserving tensions between profiles
FR20: System can detect when Asthma Profile and Runner Profile produce contradictory recommendations (e.g., one profile recommends intensity increase while the other recommends intensity decrease for the same time window)
FR21: System can escalate profile conflicts to the user for resolution, presenting both sides with supporting evidence
FR22: System can record user decisions when conflicts are escalated, feeding outcomes back to both profiles for learning
FR23: User can inspect profile evolution via version-tracked text files
FR24: System can track profile changes over time with observable pattern evolution across processed runs

**Coaching & Decision Support:**
FR25: User can interact with AI Coach in conversational mode about training, asthma, and BIE risk
FR26: System can prepare and inject a context package containing all profiles, relevant documents, and recent messages before generating coaching recommendations
FR27: Coach can present recommendations that trace to cited sources (knowledge base documents, profile data, or deterministic calculation results)
FR28: System can simulate BIE risk scenarios using deterministic computation that produces structured risk assessments (risk level, factors, confidence, sources)
FR29: System can present BIE risk simulation results to the user, emphasizing that the user makes all health-performance tradeoff decisions
FR30: Coach can translate structured risk assessment results into natural language explanations
FR31: System can restrict all risk calculations to deterministic computation, limiting the AI coach to interpreting and communicating pre-computed results without generating risk calculations or clinical thresholds

**Medical Reporting:**
FR32: System can generate monthly medical reports with structured sections (sessions processed, symptom patterns, rescue inhaler use, protocol adherence, recommendations, cited sources)
FR33: System can cite clinical sources (GINA 2024, ACSM) in medical reports with specific section references
FR34: System can present confirmed and testing-stage patterns in separate labeled sections in medical reports, distinguishing established patterns from preliminary observations
FR35: User can control sharing of monthly medical reports (generate, export, print) without automatic transmission to any party

**Data Management & Configuration:**
FR36: System can persist all structured data in a local relational data store (runs, health_log, conversation_history, runner_metrics_history)
FR37: System can store narrative profiles as text-based profile files in a configurable directory
FR38: User can run pipeline in verbose mode to see processing output including pipeline stages, metric calculations, and profile update summaries
FR39: User can run pipeline in dry-run mode to validate data processing without writing to the data store
FR40: User can redirect monthly report output to a specified file path
FR41: System can process batch files independently so one corrupt file does not stop the batch
FR42: System can separate normal output from error and validation warnings for piping and log filtering in scheduled workflows
FR43: System can maintain conversation history across sessions by reading from persisted state on each invocation

**Orchestration:**
FR45: System can orchestrate multi-agent data pipeline with context package preparation, Asthma Profile, Runner Profile, Synthesis, BIE Risk Simulator, and Coach stages with conditional transitions between them

### NonFunctional Requirements

**Performance:**
NFR1: The .fit processing pipeline processes a single file in ≤5 seconds for a typical run (≤2 hours, ≤1000 data records) as measured by end-to-end timing on a standard development machine (8-core CPU, 16GB RAM, SSD storage)
NFR2: Context package preparation (loading profiles + docs + history from local data store) completes in ≤2 seconds as measured by timer instrumentation in the orchestrator
NFR3: The BIE Risk Simulator produces identical results for identical inputs in ≤1 second as measured by unit test execution time
NFR4: Batch mode processes .fit files independently — one corrupt or slow file does not block processing of remaining files
NFR5: Profile update latency (time from new run processed to updated profile available for Coach) is bounded by LLM response time rather than local processing

**Security & Privacy:**
NFR6: All user data (runs, health logs, conversation history, profile data) resides in a local structured data store with no cloud dependency or external API calls for data persistence
NFR7: Narrative profiles are stored as human-readable text files under user-controlled version tracking in a local directory, with no remote repository sync in MVP
NFR8: Health data (asthma symptoms, medication use, peak flow, trigger patterns) is sent to the AI service provider as conversation context only when the user initiates a coaching session
NFR9: API credentials are stored in environment configuration files excluded from version control, never embedded in the database, profile files, or version-tracked files
NFR10: The system positions all output as wellness coaching and patient-provided data, explicitly disclaiming medical diagnosis or treatment
NFR11: The BIE Risk Simulator reports probabilities derived from clinical thresholds, never prescribes treatment or diagnoses conditions
NFR12: All structured data is encrypted at rest using standard database encryption (deferred to post-MVP)
NFR13: Access to the system requires local authentication tied to the operating system user account — no separate login mechanism in MVP
NFR14: All data access and modification events are logged in an audit trail within the local data store
NFR15: The user can delete all personal data (runs, health logs, profiles, conversation history) through a single purge command

**Integration:**
NFR16: The system parses .fit files conforming to the Garmin FIT protocol for activity data — compatible with Coros watch exports
NFR17: The AI service integration uses a provider-interchangeable API endpoint format that allows switching providers by changing the endpoint URL and authentication credentials without code changes
NFR18: Profiles are version-tracked through the user's local version control system — user controls when and how to commit, revert, or branch profile updates
NFR19: The local data store operates with read concurrency support to allow simultaneous read operations during background processing
NFR20: All normal processing output routes to standard output and all error and validation warnings route to standard error

### Additional Requirements

**From Architecture - Technical Requirements:**

- **Project Initialization**: Poetry-based Python project with pyproject.toml, Ruff linting/formatting, pytest testing, directory structure following src/run_intelligence/ pattern
- **Database**: SQLite with SQLAlchemy ORM + Alembic migrations, WAL mode for read concurrency
- **Data Validation**: Pydantic v2 for runtime validation on every state transition
- **CLI Framework**: Typer for CLI entry point with commands: --mode coach, --process, --batch, --log-health, --report, --purge
- **Deterministic Boundary**: pipeline/, risk_engine/, config.py contain NO LLM calls; agents/ modules contain LLM calls with structured outputs validated by Pydantic
- **Context Package**: orchestrator prepares ALL context before Coach invocation; no on-demand RAG
- **Domain Isolation**: Asthma Profile node reads only asthma_state + run_data + health_log_entry + asthma docs; Runner Profile node reads only runner_state + run_data + running docs; enforced in orchestrator/graph.py
- **Hypothesis Lifecycle Enforcement**: State transitions checked in Python code BEFORE writing to profile; evidence thresholds in config.py
- **Clinical Thresholds**: All GINA 2024, ACSM, Daniels thresholds in config.py as named constants; NEVER hardcoded in prompts or agents
- **Config Management**: Pydantic BaseSettings for env var loading; all configuration via .env file
- **Wellness Disclaimers**: In config.py constants, injected in every Coach session and medical report

**Implementation Sequence (from Architecture):**
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

### UX Design Requirements

No UX Design document found. CLI-only MVP with terminal interaction.

## Epic List

### Epic 1: Project Foundation & Data Pipeline

The user can process .fit files from their Coros watch to extract standard running metrics (pace, HR, cadence, zones) and asthma-aware metrics (HR/pace drift, HR variability, cadence compensations). The system flags data quality issues (HR artifacts, GPS drift, cadence inconsistencies) and persists all data locally in SQLite.

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR36, FR41, FR42, FR43, FR46
**NFRs covered:** NFR1, NFR4, NFR6, NFR16, NFR19, NFR20

### Epic 2: Health Logging

The user can log health data interactively via CLI (morning peak flow, sleep quality, post-run RPE, asthma symptoms 0-3, rescue inhaler use, notes). Health log entries are associated with run data for cross-referencing and used as evidence in hypothesis lifecycle.

**FRs covered:** FR15, FR16, FR17

### Epic 3: Profile Intelligence & Hypothesis Lifecycle

The user has two domain-isolated profiles (Asthma Profile and Runner Profile) that operate independently. Each profile proposes, tests, and confirms hypotheses using a lifecycle with evidence thresholds. The system detects conflicts between profiles and escalates to the user. Profiles are git-versioned markdown files the user can audit.

**FRs covered:** FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR18, FR19, FR20, FR21, FR22, FR23, FR24, FR44
**NFRs covered:** NFR17

### Epic 4: Coaching & Decision Support

The user can interact with an AI Coach in conversational mode about training, asthma, and BIE risk. The Coach operates with a strict deterministic-generative boundary: all risk calculations are deterministic code, and the Coach only interprets and communicates pre-computed results. Every recommendation cites sources.

**FRs covered:** FR25, FR26, FR27, FR28, FR29, FR30, FR31, FR45
**NFRs covered:** NFR2, NFR3, NFR5

### Epic 5: Medical Reporting

The user can generate monthly medical reports with structured sections (sessions, symptoms, rescue use, protocol adherence, recommendations, cited sources). Confirmed and testing-stage patterns are presented separately. The user controls sharing — no automatic transmission.

**FRs covered:** FR32, FR33, FR34, FR35

### Epic 6: System Integration & Security

The user has full data sovereignty: profiles are git-versioned, all data is local-first with no cloud dependency, API credentials are in .env files, an audit trail logs all data access, and a single purge command can delete all personal data. Wellness disclaimers appear in all Coach output and reports.

**FRs covered:** FR37, FR38, FR39, FR40
**NFRs covered:** NFR7, NFR8, NFR9, NFR10, NFR11, NFR13, NFR14, NFR15, NFR18

## FR Coverage Map

FR1: Epic 1 - Process .fit files to extract standard running metrics (pace, HR, cadence, zones)
FR2: Epic 1 - Derive asthma-aware metrics (HR/pace drift, HR variability, HR zone distribution anomalies, cadence compensations)
FR3: Epic 1 - Detect and flag HR artifacts (>220 bpm or sudden spikes) during data ingestion
FR4: Epic 1 - Detect and flag GPS drift anomalies (>50m/s inconsistent with pace) during data ingestion
FR5: Epic 1 - Flag derived metrics as low-confidence when underlying data contains artifacts
FR6: Epic 1 - Process individual .fit files via dedicated command
FR7: Epic 1 - Batch process all .fit files in a specified directory
FR8: Epic 3 - Asthma Profile proposes trigger hypotheses from ≥3 runs with symptom reports
FR9: Epic 3 - Asthma Profile advances hypothesis lifecycle states based on evidence thresholds
FR10: Epic 3 - Asthma Profile cross-references objective metrics with subjective symptom reports
FR11: Epic 3 - Asthma Profile seeds with clinical thresholds from GINA/ACSM when <3 runs processed
FR12: Epic 3 - Runner Profile proposes, tests, and confirms performance patterns with hypothesis lifecycle
FR13: Epic 3 - System maintains hypothesis confidence levels (low: ≤0.33, medium: 0.34-0.66, high: ≥0.67)
FR14: Epic 3 - System prevents hypothesis promotion to confirmed without meeting evidence thresholds
FR15: Epic 2 - User logs health data interactively (peak flow, sleep, RPE, symptoms, SABA use, notes)
FR16: Epic 2 - System associates health log entries with corresponding run data
FR17: Epic 2 - System uses subjective health log data as evidence in hypothesis lifecycle
FR18: Epic 3 - System maintains separate Asthma and Runner Profiles with domain-isolated boundaries
FR19: Epic 3 - System produces Synthesis presenting unified status while preserving profile tensions
FR20: Epic 3 - System detects contradictory recommendations between Asthma and Runner Profiles
FR21: Epic 3 - System escalates profile conflicts to user with supporting evidence
FR22: Epic 3 - System records user decisions when conflicts are escalated
FR23: Epic 3 - User can inspect profile evolution via version-tracked files
FR24: Epic 3 - System tracks profile changes with observable pattern evolution across runs
FR25: Epic 4 - User interacts with AI Coach in conversational mode
FR26: Epic 4 - System prepares and injects context package before generating recommendations
FR27: Epic 4 - Coach presents recommendations traceable to cited sources
FR28: Epic 4 - System simulates BIE risk scenarios with deterministic computation
FR29: Epic 4 - System presents BIE risk results emphasizing user makes all decisions
FR30: Epic 4 - Coach translates structured risk assessments into natural language
FR31: Epic 4 - System restricts all risk calculations to deterministic computation
FR32: Epic 5 - System generates monthly medical reports with structured sections
FR33: Epic 5 - System cites clinical sources (GINA 2024, ACSM) with specific section references
FR34: Epic 5 - System presents confirmed and testing-stage patterns in separate labeled sections
FR35: Epic 5 - User controls sharing of monthly medical reports (no automatic transmission)
FR36: Epic 1 - System persists all structured data in local SQLite database
FR37: Epic 6 - System stores narrative profiles as text-based files in configurable directory
FR38: Epic 6 - User can run pipeline in verbose mode to see detailed processing output
FR39: Epic 6 - User can run pipeline in dry-run mode to validate without writing
FR40: Epic 6 - User can redirect monthly report output to specified file path
FR41: Epic 1 - System processes batch files independently (one corrupt file doesn't stop batch)
FR42: Epic 1 - System separates normal output (stdout) from errors/warnings (stderr)
FR43: Epic 1 - System maintains conversation history across sessions
FR44: Epic 3 - System downgrades or withholds hypothesis promotion when data quality is low
FR45: Epic 4 - System orchestrates multi-agent pipeline with conditional transitions
FR46: Epic 1 - Detect and flag cadence inconsistencies (>20% change not attributable to pace)

## Epic 1: Project Foundation & Data Pipeline

The user can process .fit files from their Coros watch to extract standard running metrics (pace, HR, cadence, zones) and asthma-aware metrics (HR/pace drift, HR variability, cadence compensations). The system flags data quality issues (HR artifacts, GPS drift, cadence inconsistencies) and persists all data locally in SQLite.

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR36, FR41, FR42, FR43, FR46
**NFRs covered:** NFR1, NFR4, NFR6, NFR16, NFR19, NFR20

### Story 1.1: Project Initialization

As a developer,
I want to have the project scaffolded with Poetry, Typer CLI, and proper directory structure,
So that subsequent stories can build on a consistent, reproducible foundation.

**Acceptance Criteria:**

**Given** a fresh development environment with Python 3.11+ installed
**When** I run `poetry init` and configure the project
**Then** I have a `pyproject.toml` with dependencies: typer, fitparse, sqlalchemy, pydantic, langgraph, python-dotenv, alembic, ruff, pytest
**And** I have the directory structure: `src/run_intelligence/{pipeline,db,risk_engine,agents,orchestrator,reports,health_log,profiles}/`
**And** I have `config.py` with Pydantic BaseSettings loading from `.env`
**And** I have `.env.example` with all required env vars documented

**Given** the project structure is created
**When** I run `poetry install`
**Then** all dependencies resolve without conflicts
**And** `poetry run python -m run_intelligence --help` outputs CLI help

**Given** the CLI is scaffolded
**When** I run `poetry run ruff check .`
**Then** there are no linting errors
**And** `poetry run pytest` runs but shows 0 tests (placeholder structure only)

### Story 1.2: Database Schema

As a developer,
I want SQLite database models for runs, health_log, conversation_history, runner_metrics_history, and audit_log,
So that structured data can be persisted and queried.

**Acceptance Criteria:**

**Given** SQLAlchemy models defined
**When** I run `alembic upgrade head`
**Then** the database is created at `data/run_intelligence.db`
**And** all tables exist with correct columns:
- `runs`: id, file_path, processed_at, raw_metrics_json, derived_metrics_json, data_quality_flags_json
- `health_log`: id, date, peak_flow, sleep_quality, post_run_rpe, asthma_symptoms, saba_use, notes, run_id (FK nullable)
- `conversation_history`: id, session_id, role, content, created_at
- `runner_metrics_history`: id, date, vo2max, vdot, acwr, source_run_id
- `audit_log`: id, timestamp, operation, table_name, record_id, agent, details

**Given** the database schema exists
**When** I query each table
**Then** I can perform CRUD operations via repository.py
**And** WAL mode is enabled for read concurrency

### Story 1.3: .fit File Parsing

As a system,
I want to parse .fit files from Coros watches and extract raw metrics,
So that subsequent steps can derive meaningful running metrics.

**Acceptance Criteria:**

**Given** a valid .fit file from a Coros watch
**When** I call `fit_parser.parse_fit_file(path)`
**Then** I receive a dict with: timestamp, duration_seconds, distance_meters, pace_sec_per_km, hr_bpm (avg, max, min), cadence_rpm (avg, max), gps_lat, gps_lon, gps_elevation
**And** all numeric fields are present (nullable if not in file)

**Given** an invalid or corrupted .fit file
**When** I call `fit_parser.parse_fit_file(path)`
**Then** a `FitParseError` is raised with descriptive message
**And** no partial data is returned

### Story 1.4: Standard Metrics Calculation

As a system,
I want to calculate standard running metrics from raw .fit data,
So that users get meaningful performance metrics.

**Acceptance Criteria:**

**Given** raw metrics from fit_parser
**When** I call `calculate_standard_metrics(raw_data)`
**Then** I receive standard metrics including:
- Pace in min/km (avg, max, min)
- HR zones distribution (time in Z1-Z5)
- Cadence averages
- Elevation gain/loss
**And** all metrics are validated within physiologically plausible ranges

### Story 1.5: Asthma-Aware Metrics Calculation

As a system,
I want to calculate asthma-aware metrics from raw .fit data,
So that trigger patterns can be identified.

**Acceptance Criteria:**

**Given** raw metrics from fit_parser
**When** I call `calculate_asthma_aware_metrics(raw_data)`
**Then** I receive asthma-aware metrics:
- HR/pace drift: percentage change in pace relative to HR trend
- HR variability: RMSSD or standard deviation of RR intervals
- HR zone distribution anomalies: time in Z4/Z5 relative to expected
- Cadence compensation patterns: sudden cadence changes not explained by pace

**Given** metrics are calculated
**When** I call `calculate_asthma_aware_metrics`
**Then** each metric includes a confidence score (0-1) based on data quality

### Story 1.6: Data Validation & Quality Flags

As a system,
I want to detect and flag data quality issues in .fit data,
So that downstream analysis knows which metrics to trust.

**Acceptance Criteria:**

**Given** raw metrics from fit_parser
**When** I call `detect_hr_artifacts(data)`
**Then** HR values >220 bpm are flagged as artifacts
**And** sudden HR spikes inconsistent with adjacent data are flagged
**And** artifact locations are recorded with sample indices

**Given** raw metrics from fit_parser
**When** I call `detect_gps_drift(data)`
**Then** position jumps >50 m/s inconsistent with pace are flagged
**And** GPS confidence is marked low for affected segments

**Given** raw metrics from fit_parser
**When** I call `detect_cadence_inconsistencies(data)`
**Then** cadence changes >20% between consecutive segments not attributable to pace changes are flagged

**Given** all validation checks
**When** I call `validate_and_flag(data)`
**Then** I receive a `RunData` Pydantic model with:
- All metrics
- `data_quality_flags` dict with all detected issues
- `confidence_score` (0-1, below 0.5 triggers low-confidence flag)

### Story 1.7: Pipeline Orchestration

As a user,
I want to process a single .fit file through the complete pipeline,
So that I get validated, derived metrics persisted to the database.

**Acceptance Criteria:**

**Given** a valid .fit file
**When** I run `python -m run_intelligence --process run.fit`
**Then** the pipeline executes: parse → derive metrics → validate → persist to DB
**And** I see summary output to stdout: file processed, metrics extracted, any flags raised
**And** the run is stored in the `runs` table

**Given** pipeline execution
**When** I run with `--verbose`
**Then** I see detailed output: each stage, metric calculations, validation results

**Given** pipeline execution
**When** I run with `--dry-run`
**Then** all processing happens but nothing is written to the database

### Story 1.8: Batch Processing

As a user,
I want to process all .fit files in a directory,
So that I can ingest my complete run history efficiently.

**Acceptance Criteria:**

**Given** a directory with multiple .fit files
**When** I run `python -m run_intelligence --batch ./runs/`
**Then** each valid .fit file is processed independently
**And** one corrupt file does NOT stop the batch
**And** errors are logged to stderr with file identification
**And** successful runs are persisted to the database

**Given** batch processing
**When** I run `python -m run_intelligence --batch ./runs/ --dry-run`
**Then** all files are validated without writing to the database
**And** I see summary: N files would be processed, M errors

### Story 1.9: CLI Output Modes

As a user,
I want proper output separation and configuration options,
So that I can integrate with shell scripts and scheduled jobs.

**Acceptance Criteria:**

**Given** any CLI command
**When** I run with output redirection
**Then** normal output goes to stdout, errors/warnings go to stderr
**And** I can filter logs with `2>/dev/null`

**Given** the CLI
**When** I run `python -m run_intelligence --help`
**Then** I see all available commands and flags documented
**And** exit codes are: 0 for success, non-zero for errors

## Epic 2: Health Logging

The user can log health data interactively via CLI (morning peak flow, sleep quality, post-run RPE, asthma symptoms 0-3, rescue inhaler use, notes). Health log entries are associated with run data for cross-referencing and used as evidence in hypothesis lifecycle.

**FRs covered:** FR15, FR16, FR17

### Story 2.1: Health Log CLI Input

As a user,
I want to log health data interactively via CLI,
So that I can record my daily health metrics associated with my training.

**Acceptance Criteria:**

**Given** I invoke the health log command
**When** I run `python -m run_intelligence --log-health`
**Then** I am prompted interactively for:
- Morning peak flow (numeric, L/min)
- Sleep quality (1-5 scale)
- Post-run RPE (6-20 scale)
- Asthma symptoms (0-3 scale)
- Rescue inhaler use (boolean or count)
- Notes (free text, optional)

**Given** health log prompts
**When** I enter invalid data (out of range, wrong type)
**Then** I receive a validation error and can retry
**And** I can exit without saving with Ctrl+C

**Given** valid health log input
**When** I complete the entry
**Then** the data is saved to the `health_log` table
**And** I see confirmation output with date and key values
**And** the entry is associated with today's date

### Story 2.2: Health Log Association with Run

As a system,
I want to associate health log entries with corresponding run data,
So that cross-referencing is possible for hypothesis validation.

**Acceptance Criteria:**

**Given** a health log entry exists for today's date
**When** I process a .fit file for today
**Then** the run is linked to the health log entry via `run_id` foreign key
**And** the health log shows the associated run

**Given** multiple runs on the same day
**When** I process a .fit file
**Then** I am prompted to select which health log to associate (if multiple exist)
**Or** the most recent health log is associated by default

### Story 2.3: Health Log as Hypothesis Evidence

As a system,
I want to use subjective health log data as evidence in hypothesis lifecycle,
So that patterns can be validated with both objective and subjective data.

**Acceptance Criteria:**

**Given** a run with associated health log
**When** the Asthma Profile evaluates trigger hypotheses
**Then** symptom reports (0-3 scale) are included as supporting or contradicting evidence
**And** SABA use is recorded as a relevant factor
**And** peak flow values are factored into confidence calculations

## Epic 3: Profile Intelligence & Hypothesis Lifecycle

The user has two domain-isolated profiles (Asthma Profile and Runner Profile) that operate independently. Each profile proposes, tests, and confirms hypotheses using a lifecycle with evidence thresholds. The system detects conflicts between profiles and escalates to the user. Profiles are git-versioned markdown files the user can audit.

**FRs covered:** FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR18, FR19, FR20, FR21, FR22, FR23, FR24, FR44
**NFRs covered:** NFR17

### Story 3.1: Profile Storage Structure

As a system,
I want to store narrative profiles as markdown files,
So that users can read, version, and audit their profiles.

**Acceptance Criteria:**

**Given** the system is initialized
**When** profiles are created
**Then** they are stored as markdown files in `profiles/`
**And** files are named `asma_profile.md` and `runner_profile.md`
**And** each profile has deterministic sections: Active Triggers, Hypotheses, Key Metrics, Evolution History

### Story 3.2: Domain-Isolated Profile Agents

As a system,
I want Asthma Profile and Runner Profile to operate with domain-isolated boundaries,
So that asthma context never contaminates running analysis and vice versa.

**Acceptance Criteria:**

**Given** Asthma Profile agent
**When** it processes data
**Then** it reads only from: asthma_state, run_data, health_log_entry, asthma docs
**And** it writes only to: asthma_state

**Given** Runner Profile agent
**When** it processes data
**Then** it reads only from: runner_state, run_data, runner docs
**And** it writes only to: runner_state

**Given** profile agents
**When** they operate
**Then** they cannot access each other's domain state
**And** this isolation is enforced at the orchestrator level, not prompt level

### Story 3.3: Hypothesis Lifecycle State Machine

As a system,
I want hypotheses to progress through lifecycle states based on evidence thresholds,
So that patterns are only stated as confirmed when supported by sufficient data.

**Acceptance Criteria:**

**Given** a hypothesis
**When** it has 1 supporting data point
**Then** its state is "proposed" with confidence "low" (≤0.33)

**Given** a hypothesis in "proposed" state
**When** it accumulates ≥2 supporting data points with cross-referenced objective and subjective data
**Then** it advances to "testing" state with confidence "medium" (0.34-0.66)

**Given** a hypothesis in "testing" state
**When** it accumulates ≥5 supporting data points with consistent pattern
**Then** it advances to "confirmed" state with confidence "high" (≥0.67)

**Given** a hypothesis in "testing" state
**When** it accumulates ≥2 contradicting data points with stronger evidence
**Then** it advances to "contradicted" state

**Given** a hypothesis
**When** it cannot accumulate evidence within 10 runs
**Then** it remains "proposed" and is flagged for review
**And** it is never auto-promoted without meeting thresholds

**Given** hypothesis state transitions
**When** they occur
**Then** all transitions are checked in Python code BEFORE writing to profile
**And** evidence thresholds come from config.py constants

### Story 3.4: Clinical Threshold Seeding

As an Asthma Profile,
I want to seed with clinical thresholds from GINA 2024 and ACSM when data is sparse,
So that the system provides value even before personal patterns emerge.

**Acceptance Criteria:**

**Given** fewer than 3 runs with health logs have been processed
**When** the Asthma Profile generates recommendations
**Then** it uses clinical thresholds from GINA 2024 and ACSM as the basis
**And** it notes that recommendations are based on general clinical guidelines, not personal patterns

**Given** personal patterns emerge
**When** sufficient data accumulates
**Then** clinical scaffolding is progressively replaced by personal patterns
**And** the transition is documented in profile evolution history

### Story 3.5: Profile Conflict Detection

As a system,
I want to detect when Asthma Profile and Runner Profile produce contradictory recommendations,
So that the user can make informed decisions.

**Acceptance Criteria:**

**Given** Asthma Profile recommends "decrease intensity"
**And** Runner Profile recommends "increase intensity"
**When** the Synthesis node processes both profiles
**Then** `conflict_flag` is set to true
**And** `conflict_details` describes the contradiction with evidence from both profiles

**Given** conflicting recommendations
**When** the Coach presents to the user
**Then** both sides are presented with supporting evidence
**And** the user is asked to decide

### Story 3.6: Conflict Escalation & Decision Recording

As a system,
I want to escalate profile conflicts to the user and record their decision,
So that the system learns from user choices.

**Acceptance Criteria:**

**Given** a conflict between profiles
**When** the user makes a decision
**Then** the decision is recorded in the system
**And** the decision is fed back to both profiles as learning data
**And** the profile evolution history notes the user's choice

**Given** user decisions over time
**When** profiles are updated
**Then** past user decisions inform hypothesis confidence
**And** patterns in user choices are noted

### Story 3.7: Profile Evolution Tracking

As a user,
I want to inspect profile evolution via version-tracked files,
So that I can audit how my understanding of my patterns has changed.

**Acceptance Criteria:**

**Given** profile files are markdown
**When** the user inspects profiles
**Then** all content is human-readable and editable
**And** changes are trackable via git diff
**And** evolution history section shows key changes with dates

**Given** profile updates over time
**When** I run `git log profiles/`
**Then** I see a history of profile changes
**And** each change is attributable to a processed run or user correction

## Epic 4: Coaching & Decision Support

The user can interact with an AI Coach in conversational mode about training, asthma, and BIE risk. The Coach operates with a strict deterministic-generative boundary: all risk calculations are deterministic code, and the Coach only interprets and communicates pre-computed results. Every recommendation cites sources.

**FRs covered:** FR25, FR26, FR27, FR28, FR29, FR30, FR31, FR45
**NFRs covered:** NFR2, NFR3, NFR5

### Story 4.1: Coach Conversational Interface

As a user,
I want to interact with an AI Coach in conversational mode,
So that I can get personalized guidance about training and asthma management.

**Acceptance Criteria:**

**Given** I invoke coach mode
**When** I run `python -m run_intelligence --mode coach`
**Then** I enter an interactive conversation with the Coach
**And** I can ask questions about training, asthma, BIE risk, or my data

**Given** coach mode
**When** I type a question
**Then** I receive a response from the AI Coach
**And** the conversation is added to conversation history

### Story 4.2: Context Package Preparation

As a system,
I want to prepare a complete context package before Coach invocation,
So that recommendations are well-informed and hallucination risk is minimized.

**Acceptance Criteria:**

**Given** Coach mode is invoked
**When** the orchestrator prepares the context
**Then** the context package includes: both profile contents, relevant knowledge base docs, recent conversation history (up to MAX_CONVERSATION_HISTORY)
**And** context preparation completes in ≤2 seconds (NFR2)

**Given** context package
**When** it is assembled
**Then** no on-demand retrieval is performed
**And** all context is loaded from local data store

### Story 4.3: Evidence-Anchored Recommendations

As a Coach,
I want to present recommendations that cite their sources,
So that users can verify the basis for my guidance.

**Acceptance Criteria:**

**Given** a Coach recommendation
**When** it is generated
**Then** every recommendation cites its source: either a knowledge base document section, a profile data point, or a deterministic calculation result
**And** recommendations without traceable sources are not generated
**And** ≥90% of recommendations are traceable to cited sources

### Story 4.4: Deterministic BIE Risk Simulation

As a system,
I want BIE risk calculations to be deterministic,
So that results are reproducible and verifiable.

**Acceptance Criteria:**

**Given** BIE risk simulation inputs (temperature, humidity, SABA use, recent symptoms)
**When** I call `risk_engine.calculate_bie_risk(inputs)`
**Then** I receive a `RiskAssessment` with: risk_level (low/moderate/high/very_high), factors list, confidence score, sources list
**And** identical inputs always produce identical outputs
**And** computation completes in ≤1 second (NFR3)

**Given** risk_engine module
**When** it calculates
**Then** it contains NO LLM calls
**And** all logic is pure Python with thresholds from config.py

### Story 4.5: Coach Interpretation of Risk Assessments

As a Coach,
I want to translate structured risk assessments into natural language,
So that users understand their BIE risk in context.

**Acceptance Criteria:**

**Given** a `RiskAssessment` from risk_engine
**When** Coach presents the results to the user
**Then** the risk level is explained in natural language
**And** contributing factors are described with their weights
**And** confidence level is communicated
**And** sources are cited

**Given** risk assessment results
**When** Coach presents them
**Then** the user is reminded they make all health-performance tradeoff decisions
**And** the system never decides for the user

### Story 4.6: Deterministic-Generative Boundary Enforcement

As a system,
I want to enforce the boundary between deterministic computation and LLM generation,
So that clinical calculations are never delegated to the LLM.

**Acceptance Criteria:**

**Given** risk calculations
**When** they are performed
**Then** they happen in risk_engine.py (deterministic code)
**And** Coach receives pre-computed RiskAssessment as read-only context
**And** Coach NEVER recalculates risk levels or applies clinical thresholds

**Given** metric calculations
**When** they are performed
**Then** they happen in pipeline/metrics.py (deterministic code)
**And** Profile agents receive pre-computed metrics as read-only context
**And** Profile agents NEVER recalculate metrics

### Story 4.7: LangGraph Orchestration with Conditional Transitions

As a system,
I want to orchestrate the multi-agent pipeline with conditional transitions,
So that the right agents are invoked based on state.

**Acceptance Criteria:**

**Given** pipeline invocation
**When** state contains run_data
**Then** Pipeline node executes
**And** Asthma Profile and Runner Profile nodes execute
**And** Synthesis node executes

**Given** user asks about BIE risk
**When** Coach node is invoked
**Then** BIE Risk Simulator node executes first (conditionally)
**And** Coach receives RiskAssessment as context

**Given** orchestrator
**When** it routes between nodes
**Then** domain isolation is enforced at the routing level
**And** each node writes only to its designated state fields

## Epic 5: Medical Reporting

The user can generate monthly medical reports with structured sections (sessions, symptoms, rescue use, protocol adherence, recommendations, cited sources). Confirmed and testing-stage patterns are presented separately. The user controls sharing — no automatic transmission.

**FRs covered:** FR32, FR33, FR34, FR35

### Story 5.1: Monthly Medical Report Generation

As a user,
I want to generate a monthly medical report,
So that I can share structured data with my physician.

**Acceptance Criteria:**

**Given** I invoke report generation
**When** I run `python -m run_intelligence --report 2026-05`
**Then** a structured markdown report is generated for May 2026
**And** the report includes: sessions processed count, symptom patterns, rescue inhaler use summary, pattern status (confirmed vs testing)

**Given** report generation
**When** the report is created
**Then** output goes to stdout by default
**And** `--output <path>` redirects to a file

### Story 5.2: Clinical Source Citation in Reports

As a system,
I want reports to cite clinical sources with specific references,
So that physicians can verify the basis for observations.

**Acceptance Criteria:**

**Given** a medical report
**When** it references clinical guidelines
**Then** it cites GINA 2024 or ACSM with specific section references
**And** citations appear in context (not just a bibliography)

**Given** a report
**When** it mentions a pattern
**Then** it cites the supporting evidence from the user's profile or knowledge base

### Story 5.3: Pattern Status Separation in Reports

As a system,
I want confirmed and testing-stage patterns presented in separate sections,
So that physicians understand which patterns are established vs preliminary.

**Acceptance Criteria:**

**Given** a medical report
**When** it lists patterns
**Then** there is a "## Confirmed Patterns" section with patterns that have reached confirmed state
**And** there is a "## Patterns Under Investigation" section with testing and proposed patterns

**Given** pattern sections
**When** they are displayed
**Then** each pattern shows its confidence level and evidence count
**And** preliminary patterns are clearly labeled as not yet confirmed

### Story 5.4: User-Controlled Report Sharing

As a user,
I want to control how my medical report is shared,
So that I decide when and with whom my health data is communicated.

**Acceptance Criteria:**

**Given** a report is generated
**When** it is complete
**Then** no automatic transmission to any party occurs
**And** the user can: print the report, save to file, share manually

**Given** the CLI
**When** I generate a report
**Then** I can use `--output <path>` to save to a specific file
**And** the file is under my control in my filesystem

## Epic 6: System Integration & Security

The user has full data sovereignty: profiles are git-versioned, all data is local-first with no cloud dependency, API credentials are in .env files, an audit trail logs all data access, and a single purge command can delete all personal data. Wellness disclaimers appear in all Coach output and reports.

**FRs covered:** FR37, FR38, FR39, FR40
**NFRs covered:** NFR7, NFR8, NFR9, NFR10, NFR11, NFR13, NFR14, NFR15, NFR18

### Story 6.1: Profile Git Versioning

As a user,
I want profiles versioned via git,
So that I can track how my understanding of my patterns evolves.

**Acceptance Criteria:**

**Given** profiles are stored as markdown files
**When** I use git commands in the profiles directory
**Then** I can commit, view history, diff, and revert changes
**And** the system never auto-commits without user consent

**Given** profile updates
**When** they occur
**Then** I can manually run `git commit` to save the state
**And** `git log` shows the evolution of my profiles

### Story 6.2: Environment-Based Credential Management

As a system,
I want API credentials stored securely in .env files,
So that secrets are never exposed in code or version control.

**Acceptance Criteria:**

**Given** I set up the system
**When** I configure API credentials
**Then** they go in the `.env` file
**And** `.env` is in `.gitignore`
**And** credentials are never in: database, profile files, version-tracked files

**Given** the codebase
**When** I audit it
**Then** no credentials are hardcoded or embedded
**And** config.py loads credentials from environment variables

### Story 6.3: Wellness Disclaimer Enforcement

As a system,
I want wellness disclaimers in all Coach output and reports,
So that users understand this is not medical advice.

**Acceptance Criteria:**

**Given** a Coach session
**When** it is initialized
**Then** the wellness disclaimer is injected into the system prompt
**And** the disclaimer appears in: every Coach response header, every medical report

**Given** disclaimer text
**When** it is defined
**Then** it comes from config.py constants
**And** it is never hardcoded in agent prompts

### Story 6.4: Audit Trail Logging

As a system,
I want to log all data access and modifications,
So that users can audit who accessed their data and when.

**Acceptance Criteria:**

**Given** health data operations
**When** a run is processed, health log is accessed, or profile is updated
**Then** an entry is written to `audit_log` table
**And** the entry includes: timestamp, operation type, table/record affected, agent (which module performed the action)

**Given** audit log entries
**When** I query the audit log
**Then** I can see all data access history
**And** I can filter by: date range, operation type, agent

### Story 6.5: Data Purge Capability

As a user,
I want to delete all my personal data with a single command,
So that I can exercise my right to data deletion.

**Acceptance Criteria:**

**Given** I invoke the purge command
**When** I run `python -m run_intelligence --purge`
**Then** I am prompted to confirm deletion
**And** on confirmation, all data is deleted: runs, health logs, conversation history, profiles, audit log

**Given** purge is executed
**When** it completes
**Then** the database is cleared or deleted
**And** profile files are emptied or deleted
**And** I see confirmation of what was deleted

### Story 6.6: Deterministic Risk Engine (BIE Simulator)

As a system,
I want the BIE Risk Simulator to report probabilities from clinical thresholds,
So that users understand their risk without the system making medical claims.

**Acceptance Criteria:**

**Given** BIE risk inputs
**When** risk_engine calculates risk
**Then** results are framed as risk factor assessments
**And** no output contains: treatment prescriptions, diagnostic statements, or medical claims

**Given** risk assessment
**When** it is presented
**Then** it clearly states this is wellness guidance, not medical advice
**And** sources are cited from clinical literature (GINA 2024, ACSM)

### Story 6.7: CLI Help and Documentation

As a user,
I want comprehensive CLI help,
So that I can understand all available commands and options.

**Acceptance Criteria:**

**Given** the CLI
**When** I run `python -m run_intelligence --help`
**Then** I see all commands: --mode coach, --process, --batch, --log-health, --report, --purge
**And** each command shows its purpose and options

**Given** a specific command
**When** I run `python -m run_intelligence <command> --help`
**Then** I see detailed usage for that command
**And** examples are provided where helpful
