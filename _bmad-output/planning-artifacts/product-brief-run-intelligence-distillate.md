---
title: "Product Brief Distillate: Run Intelligence"
type: llm-distillate
source: "product-brief-run-intelligence.md"
created: "2026-05-10"
purpose: "Token-efficient context for downstream PRD creation"
---

# Product Brief Distillate: Run Intelligence

## Architecture & Technical Context

- **LangGraph orchestration** with 6 nodes: Pipeline → Asthma Profile → Runner Profile → Synthesis → Coach → BIE Risk Simulator (hybrid: deterministic rules engine + Coach interpretation)
- **SQLite** (`data/run_intelligence.db`) as structured truth with 4 tables: `runs` (raw + calculated metrics including subjective fields), `health_log` (morning peak flow, sleep quality, asthma control score), `conversation_history` (session messages), `runner_metrics_history` (VO2, VDOT, ACWR snapshots)
- **Markdown profiles** versioned in git: `profiles/asma_profile.md` and `profiles/runner_profile.md` — narrative views written by agents, not sources of truth. User can manually edit and agents respect annotations
- **Context-package injection** (no RAG on-demand): LangGraph orchestrator prepares ALL context (profiles + docs + recent messages) before invoking Coach. More deterministic, less hallucination risk
- **Coros .fit parsing** via Python (garmin-fit-sdk or similar). .FIT is an open standard — multi-platform extension is straightforward post-MVP
- **CLI-first MVP**: `python run.py --mode coach`, `python run.py --log-health`. Conversational health logging is post-MVP
- **BIE Risk Simulator architecture**: `risk_engine.py` deterministic module receives (temperature, humidity, SABA timing, recent symptoms, planned intensity, profile data) → applies clinical threshold tables → returns `{risk_level, factors, confidence, sources}`. Coach receives this structured result and interprets/communicates in natural language. Calculation is auditable and reproducible; communication is conversational

## Pipeline Metrics (Derived from Both Theoretical Bases)

### Running Metrics (from base_cientifica_running.md — Daniels, Seiler, ACSM exercise guidelines)

- **VDOT estimation**: VO2 = -4.60 + 0.182258v + 0.000104v²; %VO2 sustainable from Daniels' formulas
- **ACWR (Acute:Chronic Workload Ratio)**: Safe zone 0.8–1.3; for asthmatics, progression should be 5-8%/week (not standard 10%) to avoid exceeding symptom threshold
- **Zone distribution**: Time in zone 1/2/3 (percentage and absolute) — polarized 80/20 also minimizes BIE risk since sustained LT1-LT2 intensities maximize ventilation
- **Running economy**: Pace at fixed %VO2max, cadence vs stride length evolution over time
- **Estimated VO2max**: From Cooper test or 5K time trial equivalency
- **HR/pace decoupling (running performance)**: Drift in last 20% of run — signals fatigue, overtraining, or fitness gains when tracked longitudinally

### Asthma-Aware Metrics (from asma_running_base_teorica.md — GINA 2024, Anderson BIE protocol)

- **HR/pace drift (asthma signal)**: Desacoplamiento between HR and pace in conditions known to trigger BIE (cold, dry, high intensity). Distinct from normal fatigue drift — cross-referenced with subjective symptom reports
- **HR variability during run (SD)**: Surges that don't correlate with terrain or effort changes — potential bronchospasm indicator
- **Cadence/stride compensations**: Changes in biomechanics (shorter stride, higher cadence) that may compensate for respiratory distress
- **Cross-referencing objective + subjective**: HR variability correlated with self-reported asthma symptoms (0-3 scale), RPE, and rescue inhaler use to validate or reject trigger hypotheses
- **Environmental trigger correlation**: Temperature, humidity stored per run; future integration with weather API/pollen/AQI data to strengthen trigger detection (post-MVP)
- **Peak flow zones for athletes**: Green >80% personal best (continue), Yellow 60-80% (reduce intensity + rescue med), Red <60% (stop, rescue, seek urgent care) — from GINA 2024

## Hypothesis Lifecycle (MVP Feature, Not Post-MVP)

- **States**: Proposed → Testing → Confirmed/Contradicted → Archived
- **Confidence levels**: Each hypothesis carries a confidence score that increases or decreases as evidence accumulates
- **Evidence**: Every hypothesis links to supporting data points (specific runs, subjective reports, environmental conditions)
- **Git as time machine**: User can `git log`/`git diff` to see how profile evolved, which hypotheses were added, confirmed, or discarded
- **Cold-start**: Profiles seed with general clinical thresholds from GINA 2024/ACSM but immediately overlay user's own data from run 1. Clinical guidelines are initial scaffold; personal data displaces them as patterns emerge. System never stays on generic thresholds once personal data is available
- **Post-MVP enhancement**: Scientific review sub-agent cross-references profile hypotheses against docs/ (GINA 2024, ACSM) and labels them: "Revisada — compatible con literatura" / "Revisada — evidencia insuficiente" / "Revisada — contradictoria"

## Health Log Data Model

- **Input moments**: Morning (peak flow, sleep quality), Post-run (RPE 6-20, asthma symptoms 0-3, rescue inhaler use, notes), Weekly optional (simplified ACQ, observations)
- **CLI input**: `python run.py --log-health` → interactive prompts. Post-MVP: conversational input via Coach
- **Consumers**: Asthma Profile (checks morning peak flow zone before interpreting run data), Runner Profile (detects correlations like "days with sleep <3/5 correlate with resting HR +8bpm"), Coach (includes latest health_log for current state context)

## Rejected Ideas (Do Not Re-propose)

- **Environmental context module (weather API, pollen, AQI)**: Overkill for MVP. Can integrate later if core works. Re-confirmed as post-MVP scope
- **Automated weekly training plan pipeline**: Too complex for current architecture. Requires scheduling, notifications. Post-MVP
- **RAG on-demand retrieval by Coach**: Replaced by context-package injection. More deterministic, better coherence
- **Dashboard visual/HTML**: User prefers 100% conversational interface. No dashboard in roadmap
- **Multi-athlete / scalability**: Strictly personal, single user. Not in scope
- **Automatic safety guardrails (stop training)**: User prefers to make final decision. System escalates, never acts autonomously on health decisions
- **System as tutorial / onboarding-first**: Rejected in brainstorming. System learns from data, doesn't teach
- **System-initiated dialogue**: Coach responds to user queries, doesn't proactively start conversations. Post-MVP may change
- **Pre-run profiles**: Rejected — focus is post-run analysis and coaching

## Competitor Landscape

- **TrainAsONE**: ML-based adaptive training plans. No asthma/chronic condition awareness, no HR/pace decoupling or respiratory-trigger analysis
- **Runna (acquired by Strava)**: Coach-designed plans with AI adaptation. No chronic health profiling. Strava acquisition raises data sovereignty concerns for health-sensitive users
- **AI Endurance**: Deep physiological modeling (DFA a1, VO2 predictions). Integrates Garmin/Coros/Polar. No condition-specific coaching or conversational AI. Treats all athletes with same metric paradigm
- **COROS Training Hub**: Hardware-locked training intelligence. Monitoring-only, not prescriptive coaching. Zero chronic-condition intelligence. No .fit file parsing for derived asthma-aware metrics
- **NXT RUN / RunRight / PeakRunner**: GPT-powered conversational coaching. No respiratory or chronic condition profiles, no scientific evidence citation, no BIE risk simulation
- **Key gap**: No platform integrates running analytics with chronic condition management. The 20-35% of distance runners with EIB and up to 90% of asthmatics during exercise have zero specialized tooling

## User Scenarios

- **Trigger detection**: "Here's what happened to my HR when I ran in cold air, and here's the pattern across 15 runs" — structured evidence for physician consultations
- **BIE risk simulation**: User asks Coach "¿Qué pasa si hago intervalos mañana a 8°C sin SABA?" → Rules engine calculates risk (e.g., moderado-alto, 3.5/5) based on clinical thresholds + personal profile data → Coach presents: "Tu riesgo de BIE es moderado-alto. Factores: temperatura 8°C (factor 4), sin SABA pre-ejercicio (factor 3), 2 síntomas leves última semana. Si tomás SABA 15 min antes, baja a 2/5."
- **Conflict escalation**: Runner Profile says "push intervals, VO2 improving" → Asthma Profile says "BIE risk elevated last 3 cold runs" → Coach presents both sides, asks user to decide
- **Monthly medical report**: Structured report (sessions, symptoms, rescue use, protocol adherence, coach recommendations) generated on demand. User controls whether to share with physician. No automated transmission

## Regulatory Positioning

- **Wellness coaching and education**, NOT medical diagnosis or treatment
- BIE risk simulator reports probabilities based on clinical thresholds, not medical prescriptions
- Clear disclaimers separate coaching guidance from medical advice
- System explicitly escalates health-performance conflicts to user — never makes autonomous health decisions
- Positioning avoids FDA 21 CFR / EU MDR medical device classification by not prescribing treatment or diagnosing conditions

## Scientific References (Embedded Knowledge Base)

- **GINA 2024** (Global Initiative for Asthma): Track 1 ICS+formoterol as rescue (replaces SABA-only). Peak flow zones. BIE warm-up protocol (Anderson et al.): 5-8min easy jog → 6-8×30s sprint 90-100% HRmax, 90s recovery → 5min easy jog. Produces 30-50% BIE severity reduction via refractory period exploitation
- **ACSM exercise guidelines**: Training zone prescription, exercise-induced asthma management, periodization principles
- **Daniels' VDOT**: Running economy, VO2max estimation, training pace prescription
- **Seiler's polarized training (80/20)**: Also the safest distribution for asthmatic runners — sustained LT1-LT2 intensities maximize BIE risk
- **Anderson BIE protocol**: Refractory period 2-4 hours post-BIE stimulus where second stimulus causes less bronchoconstriction — scientific basis for specific warm-up protocol
- **Environmental risk thresholds**: Cold <5-10°C = 5/5 risk, dry humidity <40% = 4/5, PM2.5>35µg/m³ or ozone >70ppb = 5/5 (cancel outdoor session), high pollen = 4/5 (shift to evening)

## Open Questions

- **Metric validation**: HR/pace decoupling as asthma early-warning signal needs validation against the user's actual data. If drift has other common causes (heat, fatigue, hills), the asthma signal may be indistinguishable from noise — this is an empirical question to answer during M1-M3
- **Physician receptivity**: Will physicians find AI-generated monthly reports valuable, or dismiss them as non-clinical? The success criterion of "physician rates useful" is the test
- **LLM hallucination in health context**: Asthma Profile Agent could fabricate patterns or miss real ones. The hypothesis lifecycle (propose → test → confirm/contradict) mitigates this by requiring evidence, but early runs before pattern confirmation carry higher hallucination risk. Mitigation: profiles start with clinical scaffold and evolve with data
- **Coros HR sensor accuracy during bronchospasm**: Motion artifact and poor perfusion during BIE episodes could corrupt HR data feeding into derived metrics. Pipeline data validation (HR artifacts detection) is in scope

## Scope Boundaries (Explicit)

### MVP In
- .fit parsing + standard metrics + asthma-aware derived metrics
- SQLite with 4 tables
- CLI health log input
- Both profile agents with full hypothesis lifecycle
- Synthesis node (preserves profile tension)
- Coach with context-package injection
- BIE risk simulator (hybrid: rules engine + Coach interpretation)
- Monthly medical report (user-controlled)
- LangGraph 6-node orchestration
- Git-versioned markdown profiles
- Data validation for .fit ingestion

### MVP Out (Post-MVP)
- Scientific review sub-agent (validates hypotheses against docs/)
- 3-layer profiles (summary ~200 tokens / detail ~1000 / raw evidence)
- User-correctable profile annotations
- Environmental context (weather, pollen, AQI APIs)
- Automated weekly training plan pipeline
- Conversational health log input
- Multi-athlete support
- Visual dashboard