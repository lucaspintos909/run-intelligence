# Run Intelligence

Health-aware running intelligence platform that integrates athletic performance analytics with chronic asthma management through a multi-agent AI system.

## What It Does

Run Intelligence serves runners with exercise-induced bronchoconstriction (EIB) — 20-35% of distance runners — who currently face a painful choice: running apps that misinterpret HR spikes from bronchospasm as fitness deficits, or asthma management tools that know nothing about training load.

**Core capabilities:**

- **Asthma-aware metrics** — HR/pace decoupling, HR variability as bronchospasm signal, cadence compensations derived from clinical guidelines (GINA 2024, ACSM, Seiler, Daniels)
- **Hypothesis lifecycle** — Profiles propose patterns that advance through proposed → testing → confirmed/contradicted → archived states with evidence thresholds, never stating facts until evidence confirms them
- **Separate profile agents** — Asthma Profile and Runner Profile operate with domain-isolated boundaries; conflicts are escalated to the user, never auto-resolved
- **BIE risk simulator** — Deterministic rules engine calculates risk from clinical thresholds; Coach interprets and communicates results in natural language
- **Radical transparency** — Git-versioned markdown profiles, every recommendation cites its source

## Architecture

```
.fit file → Pipeline → Asthma Profile ─┐
                       Runner Profile  ─┤→ Synthesis → [BIE Risk?] → Coach → response
                                         ↑──── conflict detection ────────↑
```

- **Deterministic-generative boundary**: All clinical calculations (risk scores, metrics, thresholds) are pure Python. LLM agents interpret and narrate — never calculate.
- **Channel-level domain isolation**: Asthma Profile cannot access Runner Profile state, and vice versa. Enforced at the orchestrator level.
- **Context-package injection**: Orchestrator prepares ALL context before Coach invocation. No on-demand RAG. Fewer hallucination vectors.

## CLI Usage

```bash
# Process a .fit file from your Coros watch
python run.py --process data/runs/morning_run.fit

# Batch process all .fit files in a directory
python run.py --batch data/runs/

# Interactive coaching session
python run.py --mode coach

# Log health data (peak flow, symptoms, RPE, SABA use)
python run.py --log-health

# Generate monthly medical report
python run.py --report 2026-05

# Validate processing without writing to DB
python run.py --process data/runs/test.fit --dry-run

# Verbose processing output
python run.py --process data/runs/test.fit --verbose
```

## Project Structure

```
run-intelligence/
├── src/run_intelligence/
│   ├── cli.py                  # Typer entry point
│   ├── config.py                # BaseSettings, thresholds, constants, disclaimers
│   ├── pipeline/                # .fit parsing, metrics, validation
│   ├── db/                      # SQLAlchemy models, repository, session
│   ├── risk_engine/             # Deterministic BIE risk calculator
│   ├── agents/                  # Asthma Profile, Runner Profile, Synthesis, Coach
│   ├── orchestrator/            # LangGraph state, graph, context builder
│   ├── reports/                 # Monthly medical report generator
│   ├── health_log/              # Interactive CLI health log
│   └── profiles/                # Markdown profile reader/writer
├── profiles/                    # Git-versioned markdown profiles
├── docs/                        # Scientific knowledge base
├── alembic/                     # Database migrations
└── tests/                       # Mirror of src/ structure
```

## Setup

```bash
# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your LLM_API_KEY

# Initialize database
poetry run alembic upgrade head

# Run tests
poetry run pytest

# Lint and format
poetry run ruff check . && poetry run ruff format .
```

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| CLI | Typer |
| Package manager | Poetry |
| ORM / DB | SQLAlchemy + SQLite (WAL) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Agent orchestration | LangGraph |
| .fit parsing | fitparse |
| Testing | pytest |
| Linting / Formatting | Ruff |
| Profiles | Git-versioned Markdown |
| LLM API | OpenAI-compatible |

## Documentation

- [`docs/base_cientifica_running.md`](docs/base_cientifica_running.md) — Running science knowledge base (Daniels, Seiler, ACSM)
- [`docs/asma_running_base_teorica.md`](docs/asma_running_base_teorica.md) — Asthma science knowledge base (GINA 2024, Anderson BIE protocol)
- [`_bmad-output/planning-artifacts/product-brief-run-intelligence.md`](_bmad-output/planning-artifacts/product-brief-run-intelligence.md) — Product brief
- [`_bmad-output/planning-artifacts/prd.md`](_bmad-output/planning-artifacts/prd.md) — Product requirements document
- [`_bmad-output/planning-artifacts/architecture.md`](_bmad-output/planning-artifacts/architecture.md) — Architecture decision document

## Design Principles

1. **Never decides for you** — When asthma and performance goals conflict, the system escalates to the user
2. **Evidence over assertion** — Hypotheses carry lifecycle states and confidence levels; patterns aren't facts until confirmed
3. **Deterministic where it matters** — Risk calculations, metrics, and thresholds are pure Python. The LLM interprets — never calculates
4. **Local-first data sovereignty** — All data in SQLite, profiles in git-versioned markdown, no cloud dependency
5. **Every recommendation cites its source** — GINA 2024, ACSM, Seiler, Daniels — never opaque assertions

## Regulatory Positioning

This tool provides **wellness coaching and education**, not medical diagnosis or treatment. The BIE risk simulator reports probabilities from clinical thresholds, not prescriptions. Clear disclaimers separate coaching guidance from medical advice.

## License

Private project. All rights reserved.