---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
  - step-12-complete
  - validation-edit-cycle-1
  - e-01-discovery
  - e-02-review
  - e-03-edit
inputDocuments:
  - /home/lpintos/proyectos/run-intelligence/_bmad-output/planning-artifacts/product-brief-run-intelligence.md
  - /home/lpintos/proyectos/run-intelligence/_bmad-output/planning-artifacts/product-brief-run-intelligence-distillate.md
  - /home/lpintos/proyectos/run-intelligence/_bmad-output/brainstorming/brainstorming-session-2026-05-09-204826.md
  - /home/lpintos/proyectos/run-intelligence/docs/base_cientifica_running.md
  - /home/lpintos/proyectos/run-intelligence/docs/asma_running_base_teorica.md
releaseMode: phased
workflowType: prd
documentCounts:
  briefCount: 2
  researchCount: 0
  brainstormingCount: 1
  projectDocsCount: 2
classification:
  projectType: cli_tool
  domain: healthcare
  complexity: high
  projectContext: brownfield
vision:
  coreInsight: 'Runners with chronic asthma face a false dichotomy: use a running app that ignores their condition (misreading HR spikes from bronchospasm as fitness deficits), or manage asthma in isolation from training. Run Intelligence closes that gap.'
  differentiators:
    - 'Asthma-aware metrics: HR/pace decoupling, HR variability as bronchospasm signal, cadence/stride compensations — no commercial platform calculates these'
    - 'Radical transparency: git-versioned markdown profiles, every recommendation cites sources (GINA 2024, ACSM, Seiler, Daniels)'
    - 'Never decides for you: separate profiles prevent context contamination; Coach escalates conflicts to user instead of auto-resolving'
    - 'Hypothesis lifecycle: profiles propose→test→confirm/contradict→archive patterns with confidence levels — they don''t hallucinate facts'
  futureState: 'When Run Intelligence succeeds, chronic conditions and athletic performance are no longer separate problems solved in separate tools — they are intertwined realities addressed by an integrated, evidence-based approach that generalizes to other conditions (diabetes, cardiac, post-COVID recovery).'
---

# Product Requirements Document - run-intelligence

**Author:** lpintos
**Date:** 2026-05-10

## Executive Summary

Run Intelligence is a health-aware running intelligence platform that integrates athletic performance analytics with chronic asthma management through a multi-agent AI system. It serves runners with exercise-induced bronchoconstriction (EIB) — 20-35% of distance runners — who currently face a painful choice: running apps that misinterpret HR spikes from bronchospasm as fitness deficits, or asthma management tools that know nothing about training load, periodization, or performance. Run Intelligence closes this gap by calculating asthma-aware metrics (HR/pace decoupling, HR variability as bronchospasm signal, cadence compensations) derived from clinical guidelines (GINA 2024, ACSM, Seiler, Daniels), maintaining separate profile agents that prevent context contamination, and escalating health-performance conflicts to the user rather than auto-resolving them.

The target user is a runner with chronic asthma who trains with a Coros watch and wants integrated evidence for both their training decisions and medical consultations. The system is local-first (SQLite, git-versioned markdown), CLI-driven, and delivers structured monthly medical reports the user controls sharing.

### What Makes This Special

- **Asthma-aware metrics framework**: No commercial platform calculates HR/pace decoupling as an early-warning signal, cross-references objective metrics with subjective symptom reports, or simulates BIE risk scenarios. These metrics benefit any runner — the condition-specific layer is what no competitor offers.

- **Radical transparency by design**: Profiles live in human-readable markdown versioned with git. Every recommendation cites its source. Users can `git log` to track how their profile evolved. In a market of AI health black boxes, this is a deliberate philosophical commitment to user auditability and sovereignty.

- **Never decides for you**: Separate asthma and running profile agents prevent context contamination. When profiles conflict ("push intervals" vs. "high BIE risk"), the Coach escalates to the user. The system refuses to make autonomous health-performance tradeoffs.

- **Hypothesis lifecycle over factual claims**: Profile agents propose patterns (trigger hypotheses) that progress through proposed → testing → confirmed/contradicted → archived states with confidence levels. Patterns aren't stated as facts until evidence confirms them. The user can audit, correct, and track reasoning evolution via git.

## Project Classification

- **Project Type:** CLI Tool — MVP is a command-line interface (`python run.py --mode coach`, `--log-health`) orchestrating LangGraph agents. No visual dashboard. 100% conversational + terminal interaction.
- **Domain:** Healthcare/Wellness — intersects sports analytics with chronic asthma management. Operates in a sensitive regulatory space: provides wellness coaching and education, not medical diagnosis. BIE risk simulator reports probabilities from clinical thresholds, not prescriptions.
- **Complexity:** High — multi-agent orchestration (6 LangGraph nodes with conditional transitions), clinically-grounded metric derivation, hypothesis lifecycle state machines, deterministic rules engine for BIE risk simulation, and LLM hallucination risk in health context.
- **Project Context:** Brownfield — existing product brief, technical distillate, brainstorming session with architectural decisions, and 1200+ lines of embedded scientific knowledge base.

## Success Criteria

### User Success

- **Consistent use**: User logs ≥3 runs/week for 8 consecutive weeks within 6 months of starting — indicating the system becomes part of their regular training routine, not a novelty that fades.
- **Trigger understanding**: Asthma Profile confirms ≥3 trigger patterns within 3 months (e.g., "cold air <10°C + no SABA → HR/pace drift >X%") — the system delivers on its core promise of making invisible patterns visible.
- **Coherence and trust**: ≥90% of Coach recommendations are traceable to a cited source in the knowledge base, verified by spot-checks — the user can verify any recommendation, building trust through transparency.
- **Profile evolution**: Both profiles show meaningful updates across ≥10 processed runs — not just data accumulation but observable pattern evolution tracked via git history.
- **Medical triad empowerment**: Physician rates the monthly report "useful" or above in structured feedback within the first 3 consultations — the system produces evidence that improves real medical conversations.

### Business Success

- **Single-user validation**: The primary user (runner with chronic asthma, Coros watch) consistently uses the system for ≥3 months and finds it indispensable enough to reshape training decisions.
- **Evidence output quality**: Monthly medical reports are rated "useful" by at least one healthcare provider — proving the system bridges the athlete-physician information gap.
- **Hypothesis reliability**: ≥3 confirmed trigger patterns within 3 months demonstrate the hypothesis lifecycle produces real, validated insights — not just AI-generated speculation.
- **Scope discipline**: MVP ships within M0–M6 milestones without scope creep into post-MVP features (no environmental API, no dashboard, no automated training plans).

### Technical Success

- **Data pipeline integrity**: .fit parsing produces valid, consistent metrics across ≥5 different run files with HR artifact detection and GPS drift validation operational.
- **Hypothesis lifecycle correctness**: Profile agents never present unconfirmed patterns as facts — every hypothesis carries a confidence level and lifecycle state that progresses only with accumulating evidence.
- **BIE Simulator auditability**: Deterministic risk engine produces identical results for identical inputs — results are `{risk_level, factors, confidence, sources}` structures that are reproducible and inspectable.
- **Context package determinism**: LangGraph orchestrator prepares complete context (profiles + docs + recent messages) before Coach invocation — no on-demand RAG, no missing context, fewer hallucination vectors.
- **Profile separation integrity**: Asthma Profile and Runner Profile operate with clean domain boundaries — asthma context never contaminates running analysis and vice versa. Conflicts are surfaced to the user, not silently resolved.

### Measurable Outcomes

| Outcome | Target | Timeframe |
|---|---|---|
| Runs processed without pipeline errors | ≥95% of .fit files | M1 |
| Trigger patterns with ≥3 supporting data points | ≥3 confirmed patterns | 3 months |
| Coach recommendations traceable to cited sources | ≥90% | Ongoing (spot-checks) |
| Profile evolution with observable pattern changes | ≥10 runs processed | M3–M4 |
| Physician rates monthly report "useful" or above | ≥1 positive rating | First 3 consultations |
| BIE Simulator reproducibility (same inputs → same output) | 100% | M6 |
| Context package completeness (no missing profile/docs) | 100% | M5 |
| Data sovereignty (all data local, no cloud except LLM API) | 100% | M1 (network audit) |
| CLI onboarding (first end-to-end workflow without docs) | ≤15 minutes | M2 |

## User Journeys

### Journey 1: Martín — The Core Discovery Path (Primary User, Success Path)

**Opening Scene:** Martín tiene 34 años, corre desde hace 5 años con asma crónico. Antes de Run Intelligence usaba Strava, donde sus picos de FC por broncoespasmo aparecían como "fitness deficits". Su médico le preguntaba "¿cómo te sentís cuando corrés en frío?" y Martín solo podía responder "mal" — sin datos, sin patrones, sin evidencia.

**Rising Action:** Martín instala Run Intelligence, configura su CLI, y procesa su primer archivo .fit de Coros. El Pipeline extrae métricas estándar (pace, FC, cadencia, zonas) y métricas asthma-aware (HR/pace drift, variabilidad de FC, distribución de zonas). Después de la carrera, completa su health log post-run: RPE 14/20, síntomas 2/3 (opresión moderada), usó SABA a los 8 minutos.

Los primeros 3-5 runs, los perfiles se siembran con umbrales clínicos generales de GINA 2024 — el sistema todavía no tiene datos personales suficientes. Pero en cada carrera, los datos de Martín empiezan a superponerse. El Asthma Profile propone su primera hipótesis: *"Las carreras <10°C sin SABA pre-ejercicio se asocian con HR/pace drift >8% y síntomas ≥2"*. Estado: Propuesta. Confianza: baja.

**Climax:** En la carrera 8, Martín corre a 7°C sin SABA. El Asthma Profile detecta el patrón por tercera vez y sube la hipótesis a "En prueba" con confianza media. La semana siguiente, Martín consulta al Coach: *"¿Qué pasa si hago intervalos mañana a 8°C sin SABA?"* El BIE Risk Simulator calcula: riesgo moderado-alto (3.5/5), factores: temperatura 8°C, sin SABA pre-ejercicio, 2 síntomas leves la semana pasada. El Coach presenta: *"Tu riesgo de BIE es moderado-alto. Si tomás SABA 15 min antes, baja a 2/5."* Martín decide. El sistema nunca decide por él.

**Resolution:** En la carrera 12, la hipótesis sube a "Confirmada" con 5 evidencias. Martín lleva el reporte mensual a su médico — por primera vez, tiene datos estructurados: 12 carreras, 3 triggers confirmados, correlaciones objetivas, uso de rescate por sesión. Su médico califica el reporte como "útil". Martín ya no entrena con incertidumbre — entrena con evidencia.

### Journey 2: Martín — The Conflict Moment (Primary User, Edge Case)

**Opening Scene:** Martín está en la semana 6 de entrenamiento. Su Runner Profile muestra progreso: VDOT subió 3 puntos, ACWR en zona segura (0.95). Es momento de empujar intervalos según el plan.

**Rising Action:** Pero el Asthma Profile tiene una hipótesis en estado "En prueba": las últimas 3 carreras en temperatura <12°C mostraron HR/pace drift creciente. Y el pronóstico de mañana es 9°C. El Runner Profile dice "empujá", el Asthma Profile dice "cuidado".

**Climax:** En la sesión de Coach, el Synthesis Node fusiona: *"🟢 Fitness improving (VDOT +3), 🟠 Asthma alert (3 consecutive cold-weather runs with drift), 🔵 Load stable (ACWR 0.95)."* El Coach presenta el dilema explícitamente: tu rendimiento mejora pero tu patrón asmático reciente sugiere riesgo. No elige por Martín. Le presenta ambos lados con evidencia y le pregunta qué prefiere.

**Resolution:** Martín decide intentar los intervalos con SABA pre-ejercicio. El Coach registra la decisión y el resultado post-run alimentará ambos perfiles. Si los intervalos salen bien con SABA, es un dato más. Si no, el Asthma Profile lo registra y ajusta la hipótesis. El sistema respeta la agencia del usuario y aprende de la decisión.

### Journey 3: Dra. Vargas — The Physician Consumer (Secondary User)

**Opening Scene:** La Dra. Vargas es neumonóloga. Su paciente Martín llega a la consulta con un reporte impreso: 12 carreras procesadas, 3 triggers confirmados con evidencia, correlaciones HR/pace drift vs temperatura, uso de SABA por sesión, y un ACQ simplificado semanal. Nunca antes un paciente le trajo datos estructurados de su condición respiratoria durante ejercicio.

**Rising Action:** El reporte no es una pantalla genérica de app — es un documento estructurado, citando GINA 2024, con patrones confirmados vs. patrones en prueba, y métricas derivadas específicas para asma inducida por ejercicio. La Dra. Vargas puede ver exactamente qué triggered los síntomas de Martín y con qué frecuencia.

**Climax:** La Dra. Vargas califica el reporte como "útil" — por primera vez, tiene datos objetivos y subjetivos correlacionados que le permiten ajustar el plan de acción de Martín con evidencia, no solo con el relato del paciente. Le pide a Martín que siga trayendo reportes mensuales.

**Resolution:** El sistema logra uno de sus criterios de éxito: el médico del usuario califica el reporte como útil. La brecha athlete-physician se cierra con datos que ninguno de los dos tenía antes.

### Journey 4: Martín — Pipeline Error Recovery (Primary User, Technical Edge Case)

**Opening Scene:** Martín vuelve de un trail run de 15km con su Coros y ejecuta el pipeline. El parser lee el .fit pero detecta anomalías: picos de FC >220 bpm imposibles, y un segmento de GPS que salta 800m en 2 segundos.

**Rising Action:** El pipeline no silencia los errores — los marca. HR artifacts >220 bpm son flaggeados como sospechosos (podrían ser artifactos del sensor durante un episodio de broncoespasmo o simplemente ruido). GPS drift es marcado como low-confidence para cálculos de pace. Las métricas derivadas que dependen de estos datos se calculan con flags de baja confianza.

**Climax:** El Asthma Profile recibe los datos flaggeados y nota: "HR variability alto en segmento con artifacts sospechosos — no se puede confirmar si esto es bronchospasm real o sensor noise. Hipótesis pendiente de más datos." El perfil no afirma lo que no puede confirmar.

**Resolution:** Martín revé los flags en su reporte, entiende qué datos son confiables y cuáles no, y el sistema mantiene su integridad: no alucina conclusiones sobre datos ruidosos. La hipótesis queda en espera hasta que más evidencia llegue.

### Journey Requirements Summary

| Journey | Key Capabilities Revealed |
|---|---|
| Martín — Core Discovery | .fit parsing, asthma-aware metrics, hypothesis lifecycle (propose→test→confirm), health log input, Coach with context package, BIE risk simulation |
| Martín — Conflict Moment | Separate profile agents, Synthesis Node (preserves tension), conflict escalation to user, decision recording |
| Dra. Vargas — Physician Consumer | Monthly medical report generation, structured data presentation, clinical source citation, user-controlled sharing |
| Martín — Error Recovery | Data validation pipeline, HR artifact detection, GPS drift flagging, low-confidence metric flags, hypothesis restraint on noisy data |

## Domain-Specific Requirements

### Compliance & Regulatory

- **Wellness positioning, not medical device**: Run Intelligence provides wellness coaching and education, not medical diagnosis or treatment. The BIE risk simulator reports probabilities from clinical thresholds, not prescriptions. Clear disclaimers separate coaching guidance from medical advice. The system explicitly escalates health-performance conflicts to the user rather than making decisions on their behalf. Positioning avoids FDA 21 CFR / EU MDR medical device classification by not prescribing treatment or diagnosing conditions.
- **Local-first data sovereignty**: All structured data lives in SQLite. Narrative profiles are git-versioned markdown. No cloud dependency. No third-party has access to asthma symptoms, medication use, or peak-flow readings. Health data sovereignty is non-negotiable.
- **LLM data handling**: Conversation context and profile data flow through the LLM provider via an OpenAI API-compatible endpoint. No persistent data is stored by the LLM provider. Data sent to the LLM includes health metrics, symptoms, and coaching context — this is a deliberate tradeoff accepted by the user for coaching capability.

### Technical Constraints

- **Deterministic-deterministic boundary**: All clinical risk calculations and threshold-based logic are implemented as deterministic code (rules engine), never delegated to LLM generation. The LLM's role is limited to interpreting, explaining, and communicating results produced by deterministic components. Specifically: the BIE Risk Simulator is a rules engine (`risk_engine.py`) that receives structured inputs and returns `{risk_level, factors, confidence, sources}` — the Coach then receives this structured result and translates it into natural language. This principle extends to all future risk or health calculations: deterministic computation, LLM communication.

### LLM Hallucination Mitigation

- **Architectural separation of deterministic vs. generative**: All metrics, risk scores, and clinical threshold calculations are performed by deterministic code. The LLM never calculates risk levels, derives metrics, or applies clinical thresholds. The pipeline (`pipeline.py`) calculates all running and asthma-aware metrics deterministically. The risk engine (`risk_engine.py`) produces structured risk assessments deterministically. The LLM (Coach, Profile agents) is restricted to interpreting, narrating, and communicating results that originate from deterministic sources or from the embedded scientific knowledge base.

- **Evidence anchoring for Coach recommendations**: The Coach receives a prepared context package (profiles + relevant docs + recent messages) injected by the LangGraph orchestrator before invocation. The Coach must not generate recommendations that cannot trace to a source within the context package. Every recommendation must cite its source — either a specific document section (e.g., "GINA 2024, Track 1"), a data point from the user's profile, or a deterministic calculation result. Recommendations without traceable sources are considered unanchored and fall outside the system's quality contract.

- **Minimum evidence thresholds for hypothesis lifecycle states**: Profile agents must meet minimum evidence requirements before advancing hypothesis states:
  - **Proposed**: 1 supporting data point. Confidence: low. Hypothesis is noted but not acted upon in coaching recommendations.
  - **Testing**: 2-3 supporting data points with cross-referencing between objective metrics and subjective reports. Confidence: medium. Hypothesis may be referenced in coaching context with appropriate hedging.
  - **Confirmed**: ≥5 supporting data points with consistent pattern across objective metrics and/or subjective reports. Confidence: high. Hypothesis may be stated as an established pattern in profiles and coaching.
  - **Contradicted**: ≥2 data points that contradict the hypothesis with stronger evidence than supporting points. Confidence: low. Hypothesis is archived with explanation.
  - A hypothesis that cannot accumulate evidence within 10 runs remains in "Proposed" state and is flagged for review — it is never promoted without meeting evidence thresholds.

### Risk Mitigations

- **Hypothesis lifecycle prevents factual claims**: Profiles never assert patterns as facts until evidence confirms them. Every claim carries a lifecycle state and confidence level. The user can audit reasoning evolution via git.
- **Cold-start scaffolding as ongoing risk, not solved mitigation**: Profiles seed with clinical thresholds from GINA 2024 and ACSM, then immediately overlay the user's own data from run 1. However, cold-start value remains an ongoing risk to validate: clinical scaffolding must provide sufficient coaching value before personal patterns accumulate. If personal patterns don't emerge within 10 runs, profiles remain in "Proposed" state and the user is informed that recommendations are based on general thresholds. This risk must be empirically validated during M1-M3.
- **HR sensor accuracy during bronchospasm**: Coros HR sensor accuracy during BIE episodes is a specific technical risk. Motion artifact and poor perfusion during bronchospasm could corrupt HR data feeding into asthma-aware derived metrics — precisely the data that matters most. FR3 (HR artifact detection) and FR5 (low-confidence flagging) mitigate this, but the risk that the primary measurement device produces unreliable data during the condition being monitored deserves explicit acknowledgment and empirical validation during M1.
- **Context package determinism**: The orchestrator prepares ALL context before Coach invocation — no on-demand retrieval that could retrieve irrelevant or misinterpreted content. Fewer retrieval steps, fewer hallucination vectors.
- **Conflict escalation to user**: When Asthma Profile and Runner Profile produce contradictory recommendations, the system escalates to the user rather than attempting to auto-resolve. This prevents the LLM from synthesizing a compromise that could be harmful in a health context.

## Innovation & Novel Patterns

### Detected Innovation Areas

- **Category creation: health-aware running intelligence**: No commercial platform integrates running analytics with chronic condition management. The 20-35% of distance runners with EIB have zero specialized tooling. Run Intelligence creates a new category: not a running app with a health bolt-on, not a health app with running features — an integrated system from the ground up.

- **Scientific hypothesis lifecycle for AI profiles**: Profile agents propose patterns as hypotheses (not facts) that advance through proposed → testing → confirmed/contradicted → archived states with confidence levels and minimum evidence thresholds. This is a novel approach to LLM hallucination mitigation in health contexts: the system structurally prevents unfounded claims by requiring evidence accumulation before promotion.

- **Deterministic-generative architectural boundary**: All clinical risk calculations and threshold-based logic are performed by deterministic code (rules engine). The LLM is restricted to interpreting, narrating, and communicating results it never generated. No other health app establishes this boundary explicitly — most let the LLM generate assertions freely.

- **Conflict escalation as a feature, not a bug**: When asthma and running profiles produce contradictory recommendations, the system escalates to the user rather than synthesizing a compromise. In a market of apps that say "push harder" or "rest more," refusing to auto-resolve health-performance tradeoffs is a deliberate ethical commitment to user agency.

### Market Context & Competitive Landscape

| Competitor | What It Does | What It Lacks |
|---|---|---|
| TrainAsONE | ML-based adaptive training plans | No asthma/chronic condition awareness, no HR/pace decoupling, no respiratory-trigger analysis |
| Runna (Strava) | Coach-designed plans with AI adaptation | No chronic health profiling; Strava acquisition raises data sovereignty concerns for health-sensitive users |
| AI Endurance | Deep physiological modeling (DFA a1, VO2 predictions) | No condition-specific coaching or conversational AI; treats all athletes with same metric paradigm |
| COROS Training Hub | Hardware-locked training intelligence | Monitoring-only, not prescriptive coaching; zero chronic-condition intelligence; no asthma-aware metrics |
| NXT RUN / RunPeak | GPT-powered conversational coaching | No respiratory or chronic condition profiles, no scientific evidence citation, no BIE risk simulation |

**Key gap**: No platform anywhere integrates running analytics with chronic condition management for the EIB-affected running population.

### Validation Approach

- **Progressive milestone validation (M0–M6)**: Each milestone includes a decision point validating its component. M1 validates that the pipeline produces correct, consistent metrics from .fit files. M3 validates that the Asthma Profile detects real patterns from user data. M5 validates that the Coach integrates both domains coherently. Each decision point has explicit pass/fail criteria before proceeding.

- **Cold-start scaffold fallback**: If confirmed patterns don't emerge within the initial runs, profiles remain seeded with clinical thresholds from GINA 2024 and ACSM. The system never invents patterns — it uses evidence-based scaffolding until personal data displaces generic thresholds.

- **Spot-check auditability**: ≥90% of Coach recommendations must trace to a cited source. This is validated by manual spot-checks, not automated testing — a human verifies that recommendations anchor to real evidence in the knowledge base.

- **BIE Simulator reproducibility**: The deterministic engine produces identical outputs for identical inputs, validated by unit tests. The LLM interpretation layer is tested separately for coherence, not calculation accuracy.

## Rejected Decisions

The following ideas were explicitly evaluated and rejected during ideation. They are documented here to prevent scope creep and preserve architectural reasoning.

| Decision | Rationale | Replaced By |
|---|---|---|
| RAG on-demand retrieval by Coach | Unpredictable retrieval introduces hallucination risk in health context; less deterministic context for LLM | Context-package injection — orchestrator prepares all context before Coach invocation, reducing hallucination vectors |
| Visual dashboard / HTML interface | User prefers 100% conversational interface; dashboard adds complexity without core value | CLI-only interface for MVP; dashboard explicitly rejected for foreseeable roadmap |
| Multi-athlete support / scalability | Strictly personal, single-user product by design; multi-user adds architectural complexity without validating core hypothesis | Single-user MVP; multi-athlete support only if core hypothesis validated first |
| Automatic safety guardrails (stop training) | User prefers final decision authority; system escalates conflicts but never acts autonomously on health decisions | Conflict escalation to user — Coach presents both sides with evidence, user decides |
| System as tutorial / onboarding-first | System learns from data, not from teaching; tutorial mode assumes knowledge the system should derive | Cold-start scaffolding with clinical thresholds that immediately overlay personal data from run 1 |
| System-initiated dialogue | Coach responds to user queries, does not proactively start conversations; respects user agency and avoids notification fatigue | User-initiated interaction via CLI; system updates profiles silently after each run |
| Pre-run profiles (pre-run analysis) | Focus is post-run analysis and coaching; pre-run scenario planning is post-MVP | BIE risk simulation answers "what if" questions on demand; pre-run planning is Phase 2 territory |
| Environmental context module (weather, pollen, AQI APIs) | Overkill for MVP; adds API dependencies, cost, and complexity before core pipeline is validated | Post-MVP enhancement; temperature and humidity captured per-run via user input in health log |
| Automated weekly training plan pipeline | Requires scheduling, notifications, and training plan generation — too complex before core validation | Coach provides on-demand coaching; automated plans are Phase 2 after hypothesis lifecycle and Coach are validated |

## CLI Tool Specific Requirements

### Project-Type Overview

Run Intelligence is a CLI-first application with two primary interaction modes: an interactive conversational Coach mode and a scriptable data processing mode. The CLI serves as the sole user interface for the MVP — no dashboard, no web UI. All data flows through the terminal.

### Command Structure

**Primary commands:**

| Command | Mode | Description |
|---|---|---|
| `python run.py --mode coach` | Interactive | Launches LangGraph orchestration with Coach agent. User converses with AI Coach about training, asthma, BIE risk, etc. Context package (profiles + docs + recent messages) injected before Coach invocation. |
| `python run.py --log-health` | Interactive (prompts) | Launches CLI prompts for health log input: morning peak flow, sleep quality, post-run RPE, asthma symptoms (0-3), rescue inhaler use, notes. Saves to `health_log` table. |
| `python run.py --process <file.fit>` | Scriptable | Processes a single .fit file through the pipeline. Extracts standard + asthma-aware metrics. Saves to `runs` table. Triggers profile agent updates if new data available. |
| `python run.py --batch <directory>` | Scriptable | Processes all .fit files in a directory. Enables cron scheduling for automatic ingestion. Each file processed independently — one corrupt file doesn't stop the batch. |
| `python run.py --report <month>` | Scriptable | Generates monthly medical report for specified month. Outputs structured markdown to stdout or specified file path. |

**Flags:**

| Flag | Description |
|---|---|
| `--verbose` | Print detailed processing output (pipeline stages, metric calculations, profile update summaries) |
| `--dry-run` | Process files and calculate metrics without writing to database. Useful for validation. |
| `--output <path>` | Redirect report output to file instead of stdout |

### Output Formats

| Output | Format | Description |
|---|---|---|
| Profile updates (`asma_profile.md`, `runner_profile.md`) | Markdown | Human-readable narrative profiles, git-versioned. Written to `profiles/` directory. |
| BIE Risk Simulator results | JSON | Structured: `{risk_level, factors, confidence, sources}`. Consumed by Coach as deterministic input, never generated by LLM. |
| Monthly medical report | Markdown | Structured report with sections: sessions, symptoms, rescue use, protocol adherence, recommendations, cited sources. User-controlled sharing. |
| Pipeline metrics output | stdout (text) | Summary of processed run: standard metrics, asthma-aware metrics, data quality flags. |
| Health log confirmation | stdout (text) | Confirmation of saved health log entry with date and key values. |
| Error/validation output | stderr (text) | HR artifact warnings, GPS drift flags, low-confidence metric alerts. |

### Configuration Schema

All configuration via `.env` environment variables. No YAML/TOML config files for MVP.

| Variable | Description | Default |
|---|---|---|
| `LLM_API_KEY` | API key for LLM provider (OpenAI API-compatible) | Required |
| `DB_PATH` | Path to SQLite database | `data/run_intelligence.db` |
| `PROFILES_DIR` | Path to git-versioned profile directory | `profiles/` |
| `DOCS_DIR` | Path to scientific knowledge base | `docs/` |
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `MAX_CONVERSATION_HISTORY` | Number of recent messages injected into Coach context | `10` |

### Scripting Support

- **Batch processing**: `--batch` mode enables cron scheduling (e.g., `0 */6 * * * python run.py --batch /data/new_runs/` processes all .fit files every 6 hours)
- **Exit codes**: Non-zero exit on pipeline errors, validation failures, or database write failures. Zero on success.
- **Stdout/stderr separation**: Normal output to stdout, errors and validation warnings to stderr. Enables piping and log filtering.
- **Dry-run mode**: `--dry-run` processes files without database writes for validation before committing data.

### Implementation Considerations

- **LangGraph state management**: Each CLI invocation initializes LangGraph state from database (runs, health_log, conversation_history). State is not held across invocations — each session starts fresh from persisted data.
- **Git operations for profiles**: Profile agents write markdown files. Git commits are triggered explicitly by the user or after profile updates (configurable). No automatic git commits in MVP — user controls version control.
- **Concurrent access**: SQLite WAL mode for read concurrency. Single-writer constraint acceptable for single-user MVP. No multi-process contention expected.
- **Error resilience**: Batch mode processes files independently — one corrupt .fit file produces an error and skip, not a batch failure. All errors logged to stderr with file identification.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-Solving — resolve the core problem of the runner with chronic asthma who currently has no integrated tooling. The shortest path to validated learning: process real runs and verify that the hypothesis lifecycle detects real patterns, not fabricated ones.

**Resource Requirements:** 1 developer with knowledge of LangGraph, running metrics, and clinical asthma. MVP is single-user by design. No multi-person team required.

### Phase 1: MVP (M0–M6) — Problem-Solving Core

**Core User Journeys Supported:**
- Journey 1 (Martín — Core Discovery Path): .fit parsing, asthma-aware metrics, hypothesis lifecycle, health log, Coach with context package, BIE risk simulation
- Journey 2 (Martín — Conflict Moment): Separate profile agents, Synthesis Node, conflict escalation, decision recording
- Journey 3 (Dra. Vargas — Physician Consumer): Monthly medical report generation, structured data presentation, clinical source citation, user-controlled sharing
- Journey 4 (Martín — Pipeline Error Recovery): Data validation pipeline, HR artifact detection, GPS drift flagging, low-confidence metric flags, hypothesis restraint

**Must-Have Capabilities:**
- .fit file parsing pipeline with standard + asthma-aware derived metrics
- SQLite database (runs, health_log, conversation_history, runner_metrics_history)
- CLI health log input (`python run.py --log-health`)
- Asthma Profile sub-agent with hypothesis lifecycle (proposed → testing → confirmed/contradicted → archived, with confidence levels)
- Runner Profile sub-agent with hypothesis lifecycle
- Synthesis node (unified status, preserves profile tension)
- AI Coach with prepared context package injection
- BIE risk simulator (deterministic rules engine + Coach interpretation layer)
- Monthly medical report (user-controlled sharing)
- LangGraph orchestration with 6 nodes + conditional transitions
- Git-versioned markdown profiles
- Data validation for .fit ingestion (HR artifacts, GPS drift, cadence inconsistencies)

### Phase 2: Growth (Post-MVP) — Deepening & Automation

- Scientific review sub-agent that cross-references profile hypotheses against docs/
- 3-layer profiles (summary ~200 tokens / detail ~1000 / raw evidence)
- User-correctable profile annotations
- Automated weekly training plan pipeline
- Conversational health log input (Coach-mediated)

### Phase 3: Vision (Future) — Expansion

- Multi-athlete support and scaling
- Visual dashboard (explicitly rejected — user prefers 100% conversational interface)
- Condition-specific modules for other chronic conditions (diabetes, cardiac, post-COVID recovery)
- Extension to other watch platforms beyond Coros (.FIT is an open standard)
- Environmental context module (weather API, pollen, AQI)
- Pre-run scenario planning and real-time coaching

### Risk Mitigation Strategy

**Technical Risks:**
- HR/pace drift as an asthma signal may be indistinguishable from noise (heat, fatigue, hills). Mitigation: hypothesis lifecycle with minimum evidence thresholds, cross-referencing with subjective symptom reports, and hypotheses without sufficient evidence remain in "Proposed" state without promotion. MVP starts with simpler asthma-aware metrics and evolves toward sophisticated decoupling.
- LLM hallucination in health context. Mitigation: deterministic-generative separation, evidence anchoring, and hypothesis lifecycle with evidence thresholds.

**Market Risks:**
- Physicians may dismiss AI-generated reports as "app data." Mitigation: reports cite clinical sources (GINA 2024), position themselves as patient-provided data rather than medical advice, and the explicit success criterion is that a physician rates them as "useful."
- Validated learning: if the physician rates the report as useful, the athlete-physician gap is demonstrated to be closable.

**Resource Risks:**
- Minimum team: 1 developer. If fewer resources (less time) are available, the BIE Simulator and monthly report are the most costly but also the most differentiating components — do not cut them without explicit validation. Simplifiable components at initial release: health log minimum viable fields are (date, RPE, asthma symptoms 0-3, rescue inhaler use); monthly report minimum viable format is (sessions count, trigger summary, rescue use count). Profiles and Coach are non-negotiable.

## Functional Requirements

### Run Data Ingestion

- FR1: User can process .fit files from Coros watches to extract standard running metrics (pace, HR, cadence, zones)
- FR2: User can process .fit files to derive asthma-aware metrics (HR/pace drift, HR variability as bronchospasm signal, HR zone distribution anomalies, cadence compensations)
- FR3: System can detect and flag HR artifacts (values exceeding physiological plausibility thresholds of >220 bpm or exhibiting sudden spikes inconsistent with adjacent data points) during data ingestion
- FR4: System can detect and flag GPS drift anomalies (position jumps exceeding 50 meters per second not consistent with recorded pace) during data ingestion
- FR5: System can flag derived metrics as low-confidence (confidence score below 0.5 on a 0-1 scale) when underlying data contains flagged artifacts or anomalies
- FR46: System can detect and flag cadence inconsistencies (sudden cadence changes exceeding 20% between consecutive data segments not attributable to pace changes) during data ingestion, as cadence compensation patterns are asthma-aware metrics that depend on cadence data integrity
- FR6: User can process individual .fit files via dedicated processing command
- FR7: User can batch process all .fit files in a specified directory

### Asthma-Aware Analytics

- FR8: Asthma Profile can propose trigger hypotheses from run data and health logs spanning ≥3 processed runs with corresponding symptom reports
- FR9: Asthma Profile can advance hypothesis lifecycle states (proposed → testing → confirmed/contradicted → archived) based on minimum evidence thresholds (≥5 supporting data points with cross-referenced objective and subjective data for promotion to confirmed)
- FR10: Asthma Profile can cross-reference objective metrics (HR/pace drift percentage) with subjective symptom reports (user-reported 0-3 scale) to validate or contradict hypotheses
- FR11: Asthma Profile can seed with clinical thresholds from embedded knowledge base (GINA 2024, ACSM) when fewer than 3 runs with health logs have been processed
- FR12: Runner Profile can propose, test, and confirm performance and training patterns using the same hypothesis lifecycle with confidence levels (low: 1-2 data points, medium: 3-4, high: ≥5)
- FR13: System can maintain hypothesis confidence levels quantified on a defined scale (low: ≤0.33, medium: 0.34-0.66, high: ≥0.67) reflecting the number and consistency of supporting evidence
- FR14: System can prevent hypothesis promotion to confirmed state without meeting minimum evidence thresholds (≥5 supporting data points with consistent patterns across objective metrics and/or subjective reports)
- FR44: System can downgrade or withhold hypothesis promotion when underlying data contains flagged artifacts, anomalies, or confidence scores below the minimum threshold for that lifecycle state

### Health Logging

- FR15: User can log health data interactively including morning peak flow, sleep quality, post-run RPE, asthma symptoms (0-3 scale), rescue inhaler use, and notes
- FR16: System can associate health log entries with corresponding run data for cross-referencing
- FR17: System can use subjective health log data as evidence in hypothesis lifecycle alongside objective metrics

### Profile Intelligence

- FR18: System can maintain separate Asthma Profile and Runner Profile that operate with domain-isolated boundaries — asthma context appears only in Asthma Profile and running metrics context appears only in Runner Profile
- FR19: System can produce a Synthesis that presents unified status (fitness trend, asthma alert level, load status) while preserving tensions between profiles
- FR20: System can detect when Asthma Profile and Runner Profile produce contradictory recommendations (e.g., one profile recommends intensity increase while the other recommends intensity decrease for the same time window)
- FR21: System can escalate profile conflicts to the user for resolution, presenting both sides with supporting evidence
- FR22: System can record user decisions when conflicts are escalated, feeding outcomes back to both profiles for learning
- FR23: User can inspect profile evolution via version-tracked text files
- FR24: System can track profile changes over time with observable pattern evolution across processed runs

### Coaching & Decision Support

- FR25: User can interact with AI Coach in conversational mode about training, asthma, and BIE risk
- FR26: System can prepare and inject a context package containing all profiles, relevant documents, and recent messages before generating coaching recommendations
- FR27: Coach can present recommendations that trace to cited sources (knowledge base documents, profile data, or deterministic calculation results)
- FR28: System can simulate BIE risk scenarios using deterministic computation that produces structured risk assessments (risk level, factors, confidence, sources)
- FR29: System can present BIE risk simulation results to the user, emphasizing that the user makes all health-performance tradeoff decisions
- FR30: Coach can translate structured risk assessment results into natural language explanations
- FR31: System can restrict all risk calculations to deterministic computation, limiting the AI coach to interpreting and communicating pre-computed results without generating risk calculations or clinical thresholds

### Medical Reporting

- FR32: System can generate monthly medical reports with structured sections (sessions processed, symptom patterns, rescue inhaler use, protocol adherence, recommendations, cited sources)
- FR33: System can cite clinical sources (GINA 2024, ACSM) in medical reports with specific section references
- FR34: System can present confirmed and testing-stage patterns in separate labeled sections in medical reports, distinguishing established patterns from preliminary observations
- FR35: User can control sharing of monthly medical reports (generate, export, print) without automatic transmission to any party

### Data Management & Configuration

- FR36: System can persist all structured data in a local relational data store (runs, health_log, conversation_history, runner_metrics_history)
- FR37: System can store narrative profiles as text-based profile files in a configurable directory
- FR38: User can run pipeline in verbose mode to see processing output including pipeline stages, metric calculations, and profile update summaries
- FR39: User can run pipeline in dry-run mode to validate data processing without writing to the data store
- FR40: User can redirect monthly report output to a specified file path
- FR41: System can process batch files independently so one corrupt file does not stop the batch
- FR42: System can separate normal output from error and validation warnings for piping and log filtering in scheduled workflows
- FR43: System can maintain conversation history across sessions by reading from persisted state on each invocation

### Orchestration

- FR45: System can orchestrate multi-agent data pipeline with context package preparation, Asthma Profile, Runner Profile, Synthesis, BIE Risk Simulator, and Coach stages with conditional transitions between them

## Non-Functional Requirements

### Performance

- NFR1: The .fit processing pipeline processes a single file in ≤5 seconds for a typical run (≤2 hours, ≤1000 data records) as measured by end-to-end timing on a standard development machine (8-core CPU, 16GB RAM, SSD storage)
- NFR2: Context package preparation (loading profiles + docs + history from local data store) completes in ≤2 seconds as measured by timer instrumentation in the orchestrator, ensuring Coach invocation latency is dominated by LLM response time
- NFR3: The BIE Risk Simulator produces identical results for identical inputs in ≤1 second as measured by unit test execution time, guaranteeing deterministic reproducibility for any input combination
- NFR4: Batch mode processes .fit files independently — one corrupt or slow file does not block processing of remaining files, measured by verifying that a batch containing one invalid file processes all other files successfully
- NFR5: Profile update latency (time from new run processed to updated profile available for Coach) is bounded by LLM response time rather than local processing, measurable by timestamping profile write completion relative to pipeline completion

### Security & Privacy

- NFR6: All user data (runs, health logs, conversation history, profile data) resides in a local structured data store with no cloud dependency or external API calls for data persistence, measured by confirming zero network calls to external storage services during data operations
- NFR7: Narrative profiles are stored as human-readable text files under user-controlled version tracking in a local directory, with no remote repository sync in MVP, measured by confirming profiles are readable in any text editor and version-tracked via standard version control commands
- NFR8: Health data (asthma symptoms, medication use, peak flow, trigger patterns) is sent to the AI service provider as conversation context only when the user initiates a coaching session — this is a deliberate privacy tradeoff explicitly accepted by the user and documented in the system's privacy notice, verified by confirming no background data transmission occurs
- NFR9: API credentials are stored in environment configuration files excluded from version control, never embedded in the database, profile files, or version-tracked files, measured by grep audit of the codebase and data directory confirming no credential exposure
- NFR10: The system positions all output as wellness coaching and patient-provided data, explicitly disclaiming medical diagnosis or treatment — disclaimers appear in Coach output and monthly medical reports, measured by confirming disclaimer text is present in every report generation and every new Coach session initialization
- NFR11: The BIE Risk Simulator reports probabilities derived from clinical thresholds, never prescribes treatment or diagnoses conditions — the system frames results as risk factor assessments for user decision-making, measured by confirming no output contains treatment recommendations or diagnostic statements
- NFR12: All structured data is encrypted at rest using standard database encryption, measured by confirming encrypted storage is enabled by default and plaintext access is not possible without the user's encryption key
- NFR13: Access to the system requires local authentication tied to the operating system user account — no separate login mechanism in MVP, measured by confirming the application does not start or expose data without OS-level user session access
- NFR14: All data access and modification events are logged in an audit trail within the local data store, enabling the user to review who (which agent or process) accessed or modified data and when, measured by confirming audit log entries exist for each health data read, write, and profile update operation
- NFR15: The user can delete all personal data (runs, health logs, profiles, conversation history) through a single purge command, and the system provides clear documentation of data retention periods and deletion procedures, measured by confirming that the purge command removes all user data and that retention policies are documented

### Integration

- NFR16: The system parses `.fit` files conforming to the Garmin FIT protocol for activity data — compatible with Coros watch exports, measured by successful parsing and metric extraction from ≥5 different Coros .fit files with zero data loss
- NFR17: The AI service integration uses a provider-interchangeable API endpoint format that allows switching providers by changing the endpoint URL and authentication credentials without code changes, measured by confirming that a provider swap (endpoint URL + credentials) produces functional equivalence without source modifications
- NFR18: Profiles are version-tracked through the user's local version control system — user controls when and how to commit, revert, or branch profile updates, measured by confirming profile changes appear in version control diffs and the system never auto-commits without user consent
- NFR19: The local data store operates with read concurrency support to allow simultaneous read operations during background processing, measured by confirming that a Coach query and a pipeline write can execute concurrently without data corruption or locking errors
- NFR20: All normal processing output routes to standard output and all error and validation warnings route to standard error, enabling shell piping and log filtering in scheduled workflows, measured by confirming that `--verbose` output goes to stdout and error messages go to stderr when tested with shell redirection