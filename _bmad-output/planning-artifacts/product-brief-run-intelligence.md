---
title: "Product Brief: Run Intelligence"
status: "complete"
created: "2026-05-10"
updated: "2026-05-10"
inputs:
  - "_bmad-output/brainstorming/brainstorming-session-2026-05-09-204826.md"
  - "docs/asma_running_base_teorica.md"
  - "docs/base_cientifica_running.md"
---

# Product Brief: Run Intelligence

## Executive Summary

Run Intelligence is the first health-aware running intelligence platform — a personal AI coach that integrates athletic performance analytics with chronic asthma management. The asthma-aware metrics framework (HR/pace decoupling, variability analysis, trigger detection) benefits any runner — not just those with diagnosed asthma — but the condition-specific layer is what no competitor offers. The 20-35% of distance runners who experience exercise-induced bronchoconstriction (EIB) currently face a painful choice: use a running app that ignores their respiratory condition entirely (misreading HR spikes from bronchospasm as fitness deficits), or manage their asthma in isolation from training. Run Intelligence parses .fit files from a Coros watch, calculates metrics derived from clinical guidelines (GINA 2024, ACSM, Seiler, Daniels), and uses specialized AI agents to maintain evolving narrative profiles — with a hypothesis lifecycle that proposes, tests, confirms, or discards patterns as evidence accumulates. When asthma and performance goals conflict, the system escalates to the user — it never decides for you. Every recommendation cites its source. Every profile is auditable via git.

## The Problem

Runners with chronic asthma manage two parallel but deeply intertwined realities every time they train. A hard interval session that builds VO2max might also trigger a bronchospasm. Cold air that improves running economy simultaneously inflames airways. Yet every tool available forces them to choose: Strava, TrainingPeaks, and Garmin Connect offer rich running analytics but treat asthma as invisible — HR spikes from bronchospasm are misread as fitness deficits, and "training status" scores become meaningless. Meanwhile, asthma management apps track medication and symptoms but know nothing about pace, training load, or periodization.

The cost of this gap is not just inconvenience. It's poor decisions: the runner who pushes through symptoms because their app says they're "recovering well," or the runner who avoids intensity because they can't distinguish normal exertion from an asthma episode. GINA 2024 guidelines emphasize individualized action plans and shared decision-making — but without integrated data, neither the runner nor their physician has the evidence base to inform those decisions.

No commercial platform calculates HR/pace decoupling as an asthma early-warning signal. None cross-references subjective symptom reports with objective training metrics. None simulates BIE risk scenarios ("What happens if I do intervals at 5°C without SABA?"). Run Intelligence exists to close this gap.

## The Solution

A multi-agent system orchestrated by LangGraph with five specialized nodes:

1. **Pipeline** — Parses Coros .fit files and calculates both standard running metrics (pace, HR, cadence, stride) and asthma-aware derived metrics (HR/pace drift, HR variability, zone distribution, cadence compensations) grounded in the theoretical foundations of running physiology and asthma pathophysiology.

2. **Asthma Profile Agent** — After each run, analyzes the relationship between objective metrics and subjective symptom reports (RPE, asthma symptoms 0–3, rescue inhaler use) to detect triggers, establish thresholds, and propose patterns. Writes a human-readable, git-versioned narrative profile (`asma_profile.md`).

3. **Runner Profile Agent** — Independently tracks running performance evolution (estimated VO2max, VDOT, running economy, training load, ACWR) without asthma context "contaminating" the analysis. Writes `runner_profile.md`.

4. **Synthesis Node** — Fuses both profiles into a concise unified status (~200 tokens): "Fitness improving, mild asthma alert, load stable."

5. **AI Coach** — Receives a prepared context package (profiles + relevant scientific docs + recent conversations), converses with the athlete, and presents conflict dilemmas when asthma and performance goals clash.

6. **BIE Risk Simulator (hybrid)** — A deterministic rules engine calculates risk scores from clinical thresholds + user profile data (temperature, humidity, SABA timing, recent symptoms, planned intensity), producing a structured result `{risk_level, factors, confidence, sources}`. The AI Coach then interprets and communicates this result in natural language, adding context and actionable recommendations. The calculation is auditable and reproducible; the communication is conversational and explanatory.

All structured data lives in SQLite. Narrative profiles are human-readable markdown, versioned with git — the user can audit, correct, and track their evolution over time. The system cites its sources (GINA 2024, ACSM, Seiler, Daniels) rather than generating opaque recommendations.

## What Makes This Different

- **Asthma-aware metrics**: No platform calculates HR/pace decoupling, HR variability correlation with respiratory symptoms, or cadence compensations as biomechanical asthma proxies. These metrics are derived from the same clinical and physiological literature (GINA 2024, ACSM exercise guidelines, Anderson's BIE warm-up protocol, Daniels' VDOT, Seiler's polarized training) that informs medical practice. Profiles use a hypothesis lifecycle (proposed → testing → confirmed/contradicted → archived) with confidence levels — patterns aren't stated as facts until evidence confirms or contradicts them, and the user can see the reasoning evolve via git.

- **Transparency by design**: Profiles live in human-readable markdown, versioned with git. Every recommendation traces to a cited source. The user can audit, correct, and track evolution via `git log`. In a market where AI health tools are black boxes, this is a deliberate philosophical stance: you should never have to trust the system blindly.

- **We never decide for you**: Separate asthma and running profiles prevent context contamination. When they conflict (push intervals vs. high BIE risk), the Coach escalates to the user instead of auto-resolving. In a market of apps that say "push harder," refusing to auto-resolve health-performance tradeoffs is a deliberate commitment to user agency.

- **Evidence-based, not opaque**: The sub-agents consult the embedded scientific knowledge base (719+ lines on asthma pathophysiology and GINA 2024, 499+ lines on running science) before generating profile conclusions or coaching advice. Every claim has a source.

- **Local-first, privacy-respecting**: SQLite database, git-versioned markdown, no cloud dependency. The athlete owns their data — no third-party has access to asthma symptoms, medication use, or peak-flow readings. Health data sovereignty is non-negotiable.

## Who This Serves

**Primary user**: A runner with chronic asthma who trains with a Coros watch and wants to understand how their respiratory condition interacts with their performance — not as separate concerns, but as one integrated system. They've tried generic running apps and found them blind to their reality. They want evidence they can bring to their physician: "Here's what happened to my HR when I ran in cold air, and here's the pattern across 15 runs."

Success for this user means: understanding their personal asthma triggers with data, training with confidence that their plan accounts for their condition, and having structured information that improves their medical consultations.

## Success Criteria

- **Consistent use**: ≥3 runs/week logged for 8 consecutive weeks within 6 months of starting.
- **Deeper understanding**: ≥3 confirmed trigger patterns identified by the asthma profile within 3 months (e.g., "cold air <10°C + no SABA → HR/pace drift >X%").
- **Coach coherence**: ≥90% of Coach recommendations traceable to a cited source in the knowledge base, verified by spot-checks.
- **Profile evolution**: Both profiles show meaningful updates across ≥10 processed runs — not just data accumulation but observable pattern evolution.
- **Medical triad empowerment**: Physician rates the monthly report "useful" or above in structured feedback within the first 3 consultations.

## Risks & Considerations

- **Regulatory positioning**: This tool provides wellness coaching and education, not medical diagnosis or treatment. The BIE risk simulator reports probabilities based on clinical thresholds, not medical prescriptions. Clear disclaimers separate coaching guidance from medical advice. The system explicitly escalates health-performance conflicts to the user rather than making decisions on their behalf.
- **Cold-start value**: Before pattern detection is possible (runs 1–5), the system seeds profiles with general clinical thresholds from GINA 2024 and ACSM, but immediately overlays the user's own data — subjective symptoms, peak-flow readings, HR responses — to start personalizing from run 1. Clinical guidelines provide the starting scaffold; the user's data displaces them as patterns emerge. The system never stays on generic thresholds once personal data is available.
- **Data quality**: .fit file ingestion includes validation for HR sensor artifacts, GPS drift, and cadence inconsistencies. Derived metrics flag low-confidence calculations rather than presenting them as ground truth.
- **Coros specificity**: MVP targets Coros .fit files because that is the primary user's device. The .FIT protocol is an open standard — multi-platform ingestion is a straightforward extension once the core pipeline is validated.

## Scope

### In (MVP — Milestones M0–M6)

- .fit file parsing pipeline with standard + asthma-aware derived metrics
- SQLite database (runs, health_log, conversation_history, runner_metrics_history)
- CLI health log input
- Asthma Profile sub-agent with hypothesis lifecycle (proposed → testing → confirmed/contradicted → archived, with confidence levels)
- Runner Profile sub-agent with hypothesis lifecycle
- Synthesis node (unified status, preserves tension between profiles rather than averaging)
- AI Coach with prepared context package
- BIE risk simulator — deterministic rules engine + Coach interpretation layer
- Monthly medical report (user-controlled sharing)
- LangGraph orchestration with 6 nodes + conditional transitions
- Git-versioned markdown profiles
- Data validation for .fit ingestion (HR artifacts, GPS drift, cadence inconsistencies)

### Out (Post-MVP)

- Scientific review sub-agent that cross-references profile hypotheses against docs/
- 3-layer profiles (summary/detail/raw evidence)
- User-correctable profile annotations
- Environmental context module (weather API, pollen, AQI)
- Automated weekly training plan pipeline
- Conversational health log input (Coach-mediated)
- Multi-athlete support
- Visual dashboard

## Vision

If Run Intelligence succeeds for one athlete, it proves a principle: that chronic conditions and athletic performance are not separate problems to solve in separate tools — they are intertwined realities that demand an integrated, evidence-based approach. The architecture — specialized profile agents, synthesis, conflict escalation — generalizes. The evidence base swaps in. In 2–3 years, this could serve any chronic condition that intersects with endurance training: diabetes, cardiac conditions, post-COVID respiratory recovery. What doesn't change is the core insight: people with chronic conditions deserve coaching that sees the whole athlete, not just the healthy part.

The asthma-aware metrics framework (HR/pace decoupling, variability analysis, trigger detection) is useful for any runner — not just those with diagnosed asthma. HR/pace drift signals overtraining and illness onset in healthy athletes too. This creates a natural top-of-funnel expansion: every runner benefits from smarter metrics, while the condition-specific layer remains the differentiator that no competitor offers.