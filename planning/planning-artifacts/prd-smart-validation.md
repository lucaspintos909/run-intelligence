# SMART Requirements Validation — Functional Requirements (FR1–FR43)

**Date:** 2026-05-11
**Scorer:** AI Analysis
**Scale:** 1–5 per criterion (5=excellent, 1=poor)
**Flag threshold:** Any score < 3 triggers an improvement suggestion.

---

## Scoring Table

| FR | S | M | A | R | T | Total | Flags |
|----|---|---|---|---|---|-------|-------|
| FR1 | 4 | 4 | 5 | 5 | 5 | 23 | |
| FR2 | 3 | 3 | 4 | 5 | 5 | 20 | S<3: vague "anomalies" |
| FR3 | 3 | 3 | 5 | 5 | 5 | 21 | S<5,M<5: subjective thresholds |
| FR4 | 2 | 2 | 5 | 4 | 5 | 18 | **S<3,M<3**: no drift threshold defined |
| FR5 | 3 | 2 | 5 | 5 | 4 | 19 | **M<3**: "low-confidence" undefined |
| FR6 | 5 | 5 | 5 | 5 | 5 | 25 | |
| FR7 | 5 | 5 | 5 | 5 | 5 | 25 | |
| FR8 | 4 | 3 | 4 | 5 | 5 | 21 | M: quality of "propose" hard to validate |
| FR9 | 5 | 4 | 4 | 5 | 5 | 23 | |
| FR10 | 4 | 3 | 4 | 5 | 5 | 21 | |
| FR11 | 4 | 4 | 5 | 5 | 5 | 23 | Impl leak: "embedded knowledge base" |
| FR12 | 3 | 3 | 4 | 5 | 4 | 19 | S: "performance and training patterns" vague |
| FR13 | 3 | 2 | 3 | 5 | 4 | 17 | **M<3**: no confidence scale defined |
| FR14 | 5 | 5 | 5 | 5 | 5 | 25 | Gold standard FR |
| FR15 | 5 | 5 | 5 | 5 | 5 | 25 | |
| FR16 | 4 | 3 | 5 | 5 | 4 | 21 | M: "corresponding" is vague linkage |
| FR17 | 3 | 3 | 4 | 5 | 4 | 19 | S: "alongside" vague integration |
| FR18 | 3 | 2 | 4 | 5 | 5 | 19 | **M<3**: "clean"/"never contaminates" untestable |
| FR19 | 3 | 2 | 4 | 5 | 5 | 19 | **M<3**: "preserving tensions" untestable |
| FR20 | 3 | 2 | 3 | 5 | 5 | 18 | **M<3,A<5**: contradiction detection unreliable |
| FR21 | 4 | 4 | 5 | 5 | 5 | 23 | Neg spec: "rather than auto-resolving" |
| FR22 | 4 | 4 | 4 | 5 | 5 | 22 | |
| FR23 | 5 | 5 | 5 | 5 | 5 | 25 | Impl leak: "git-versioned markdown" |
| FR24 | 3 | 3 | 4 | 5 | 4 | 19 | S: "observable" subjective |
| FR25 | 4 | 3 | 4 | 5 | 5 | 21 | Impl leak: "via CLI" |
| FR26 | 3 | 3 | 4 | 5 | 5 | 20 | S: "relevant docs" vague quantifier |
| FR27 | 4 | 4 | 4 | 5 | 5 | 22 | Impl leak: "deterministic" |
| FR28 | 5 | 5 | 4 | 5 | 5 | 24 | Impl leak: "deterministic rules engine" |
| FR29 | 4 | 4 | 5 | 5 | 5 | 23 | Neg spec: "without making" |
| FR30 | 3 | 3 | 4 | 4 | 4 | 18 | S: "natural language explanations" vague |
| FR31 | 4 | 2 | 3 | 5 | 5 | 19 | **M<3,A<3**: "never generating" untestable; LLM restriction hard |
| FR32 | 5 | 4 | 5 | 5 | 5 | 24 | |
| FR33 | 5 | 5 | 5 | 5 | 5 | 25 | |
| FR34 | 4 | 4 | 5 | 5 | 4 | 22 | |
| FR35 | 4 | 4 | 5 | 5 | 5 | 23 | |
| FR36 | 5 | 5 | 5 | 5 | 5 | 25 | Impl leak: "SQLite" |
| FR37 | 4 | 4 | 5 | 5 | 5 | 23 | Impl leak: "markdown files" |
| FR38 | 4 | 4 | 5 | 4 | 4 | 21 | |
| FR39 | 5 | 5 | 5 | 5 | 5 | 25 | |
| FR40 | 5 | 5 | 5 | 4 | 4 | 23 | |
| FR41 | 5 | 5 | 5 | 5 | 5 | 25 | |
| FR42 | 5 | 5 | 5 | 4 | 4 | 23 | |
| FR43 | 4 | 4 | 5 | 5 | 4 | 22 | Impl leak: "persisted state" |

---

## Flagged FRs (Any Score < 3)

### FR2 — Asthma-Aware Metrics Derivation
**Score:** S=3, M=3 | **Flag:** S<5
- **Issue (Subjective adjective):** "HR zone distribution anomalies" — no threshold for what constitutes an anomaly. "Anomalies" is a judgment call without a quantitative definition.
- **Improvement:** Replace "anomalies" with a specific statistical definition: "HR zone distribution deviations exceeding ±1 zone from expected distribution for >20% of run duration." Add: "Anomaly thresholds are configurable per runner profile."

### FR4 — GPS Drift Anomaly Detection
**Score:** S=2, M=2 | **Flag:** S<3, M<3
- **Issue (Vague quantifier):** "GPS drift anomalies" has no threshold. What distance/time deviation constitutes drift?
- **Improvement:** Rewrite: "System can detect and flag GPS positions where point-to-point displacement exceeds 15 m/s (equivalent to >54 km/h — faster than humanly possible) or where consecutive points show heading changes >90° within 2 seconds." Add config note: "Drift thresholds configurable via environment variables."

### FR5 — Low-Confidence Metric Flagging
**Score:** M=2 | **Flag:** M<3
- **Issue (Subjective adjective):** "Low-confidence" is undefined. What percentage of artifact-contaminated data shifts a metric from "confident" to "low-confidence"? This creates an untestable binary from what should be a graduated scale.
- **Improvement:** Define the threshold: "System can flag derived metrics as low-confidence when >30% of underlying source data points contain detected artifacts or anomalies. Confidence level is a graduated scale (high/medium/low) reported alongside each derived metric."

### FR13 — Hypothesis Confidence Levels
**Score:** M=2 | **Flag:** M<3
- **Issue (Subjective adjective):** "Strength and consistency of supporting evidence" is unmeasurable. No confidence scale is specified (numeric? categorical?).
- **Improvement:** Define the confidence scale: "System can maintain hypothesis confidence levels on a 3-tier scale (low/medium/high) derived from: (1) count of supporting data points (≥1=low, ≥3=medium, ≥5=high per FR9 thresholds), and (2) cross-validation rate between objective and subjective evidence sources."

### FR18 — Profile Domain Separation
**Score:** M=2 | **Flag:** M<3
- **Issue (Subjective adjective + negative specification):** "Clean domain boundaries" is untestable. "Never contaminates" is a negative specification — you cannot verify "never."
- **Improvement:** Rewrite as a positive, testable specification: "System can isolate profile context such that: (a) Asthma Profile agent receives only asthma-relevant context (symptoms, triggers, respiratory metrics, health logs); (b) Runner Profile agent receives only running-relevant context (training metrics, performance data, load indicators); (c) each profile's context package is logged and auditable for cross-domain leakage in test suites."

### FR19 — Synthesis Preserving Tensions
**Score:** M=2 | **Flag:** M<3
- **Issue (Subjective adjective):** "Preserving tensions between profiles" is unmeasurable. What counts as a "tension" and how do you verify it was "preserved"?
- **Improvement:** Rewrite: "System can produce a Synthesis that: (a) reports each profile's recommendation independently; (b) explicitly flags cases where recommendations diverge; (c) presents both positions with their supporting evidence rather than merging into a single compromise. Synthesis must not suppress or soften a profile's position."

### FR20 — Contradictory Recommendation Detection
**Score:** M=2, A=3 | **Flag:** M<3
- **Issue (Subjective adjective):** "Contradictory" is inherently subjective in natural language — two recommendations can be "in tension" without being logically contradictory, and LLM-based detection of contradiction is unreliable.
- **Improvement:** Make the detection deterministic rather than LLM-judged: "System can detect profile conflicts when Asthma Profile and Runner Profile produce recommendations that affect the same training decision (e.g., same run session, same time period) with opposing directives (one recommending 'push', one recommending 'rest'). Conflict detection rules are defined in a deterministic rules layer, not delegated to LLM judgment."

### FR31 — LLM Restriction to Interpretive Role
**Score:** M=2, A=3 | **Flag:** M<3, A<3
- **Issue (Negative specification + implementation leakage):** "Never generating risk calculations" is a negative specification that's untestable (you can never prove "never"). Delegating enforcement to prompt engineering ("restrict the LLM") is architecturally fragile — prompt compliance is probabilistic, not guaranteed.
- **Improvement:** Rewrite as a positive architectural constraint: "System can ensure that all risk calculations and clinical threshold applications are performed exclusively by deterministic modules (`risk_engine.py`, `pipeline.py`), with the generative layer restricted to receiving pre-computed results as structured input and producing natural-language output. Risk calculation modules expose a defined interface that the generative layer calls but cannot override. Compliance is verified via integration tests asserting that no LLM-generated output contains risk scores not present in the deterministic input."

---

## Issue Category Summary

### Subjective Adjectives (9 FRs — expanded from original 7)

| FR | Subjective Term | Replacement |
|----|----------------|-------------|
| FR2 | "anomalies" | Statistical threshold deviation (>X% from expected) |
| FR3 | "impossible values, sensor noise" | Explicit thresholds (e.g., HR >220 bpm, HR change >80 bpm in 1 sec) |
| FR4 | "drift anomalies" | Quantified drift (displacement >15 m/s or heading change >90°/2s) |
| FR5 | "low-confidence" | Graduated confidence scale with defined threshold (>30% artifact-contaminated) |
| FR13 | "strength and consistency" | 3-tier scale with numeric data-point count mapping |
| FR18 | "clean" / "never contaminates" | Specified per-profile context scope; auditable context packages |
| FR19 | "preserving tensions" | Explicit conflict flagging; no merging/suppression |
| FR20 | "contradictory" | Deterministic conflict rules on same decision, opposing directives |
| FR24 | "observable" | "inspectable via git log with per-run diff summaries" |

### Vague Quantifiers (4 FRs — expanded from original 3)

| FR | Vague Term | Replacement |
|----|-----------|-------------|
| FR4 | "drift anomalies" | Quantified threshold (see above) |
| FR9 | "minimum evidence thresholds" (defined elsewhere, not self-contained) | Inline: "≥5 data points for Confirmed, 2-3 for Testing, 1 for Proposed" |
| FR16 | "corresponding run data" | "run data from the same calendar date or within ±6 hours of the health log timestamp" |
| FR26 | "relevant docs" | "docs matching trigger keywords from the current query and profile context, up to MAX_CONTEXT_DOCS (default: 5)" |

### Implementation Leakage (13 FRs)

| FR | Implementation Detail | Should Be |
|----|----------------------|-----------|
| FR6 | `` `--process` `` CLI flag | "User can process an individual .fit file" (flag is CLI spec, acceptable for CLI tool, but FR should describe capability) |
| FR7 | `` `--batch` `` CLI flag | "User can batch process all .fit files in a directory" |
| FR11 | "embedded knowledge base" | "clinical thresholds from authoritative medical guidelines" |
| FR15 | "via CLI prompts" | "User can log health data interactively" |
| FR23 | "git-versioned markdown files" | "User can inspect profile evolution through version-tracked human-readable files" |
| FR25 | "via CLI" | "in conversational mode" |
| FR26 | "inject" context package | "System can assemble and provide" context package |
| FR27 | "deterministic calculation results" | "computed results" |
| FR28 | "deterministic rules engine" | "rules-based simulation engine" |
| FR30 | "deterministic risk assessment results" | "computed risk assessment results" |
| FR31 | "LLM", "deterministic sources" | "generative layer", "computed sources" |
| FR36 | "SQLite" | "structured data store" |
| FR37 | "human-readable markdown files" | "human-readable text files" |

### Negative Specification (3 FRs)

| FR | Negative Form | Positive Rewrite |
|----|--------------|-----------------|
| FR18 | "asthma context never contaminates running analysis" | "Asthma Profile and Runner Profile each receive only their domain-specific context" |
| FR29 | "without making autonomous health-performance tradeoffs" | "presenting both positions for user decision" |
| FR31 | "never generating risk calculations" | "producing risk calculations exclusively via deterministic modules" |

---

## Top 5 Most Critical FRs to Fix

1. **FR4** (S=2, M=2): No threshold for GPS drift — completely untestable as written.
2. **FR5** (M=2): "Low-confidence" is a binary flag for what should be a graduated scale; untestable.
3. **FR13** (M=2): Confidence levels defined with subjective terms instead of a numeric/categorical scale; core hypothesis lifecycle FR is unmeasurable.
4. **FR18** (M=2): "Clean boundaries" and "never contaminates" are untestable — this is the #1 architectural differentiator and it's specified as a negative with no test criteria.
5. **FR20** (M=2, A=3): Contradiction detection delegated to LLM judgment is unreliable; should be deterministic rules.

---

## FRs That Are Well-Specified (Gold Standards)

| FR | Why |
|----|-----|
| FR14 | Exact numeric threshold (≥5 data points), clear state transition, fully testable. |
| FR6/FR7 | Clear capability, measurable, trivially achievable. |
| FR15 | All fields specified with data types and scales (0-3 for symptoms). |
| FR23 | Trivially testable (git log shows changes). |
| FR33 | Clear, measurable citation presence. |
| FR39 | Dry-run = no DB writes. Binary testable. |
| FR41 | Corrupt file → skip, batch continues. Binary testable. |

---

## Statistical Summary

| Metric | Value |
|--------|-------|
| Total FRs | 43 |
| Average Total Score | 21.9 / 25 |
| FRs with any score < 3 | 8 (FR2, FR4, FR5, FR13, FR18, FR19, FR20, FR31) |
| FRs with score = 25 (perfect) | 6 (FR6, FR7, FR14, FR15, FR23, FR33, FR36, FR39, FR41) |
| Subjective adjective issues | 9 FRs |
| Vague quantifier issues | 4 FRs |
| Implementation leakage issues | 13 FRs |
| Negative specification issues | 3 FRs |