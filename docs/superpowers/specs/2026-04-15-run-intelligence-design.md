# Run Intelligence — Design Spec
**Date:** 2026-04-15
**Goal:** Local CLI coaching agent for beginner runners targeting first 5K or 10K

---

## Overview

Pipeline that converts raw GPX files from Strava into scientifically-grounded metrics,
persists them in SQLite, and surfaces a compressed context document to a Claude Code CLI
agent that prescribes training sessions based on the user's real data and evidence-based
periodization principles.

---

## Architecture

### Two worlds, one bridge

- **World 1 — Raw data**: GPX files, timestamps, GPS coordinates, HR streams
- **World 2 — Knowledge**: derived metrics, fitness-fatigue state, structured plan
- **Bridge**: Python pipeline (ingest → metrics engine → SQLite → context builder)

The Claude Code agent lives exclusively in World 2. It never sees raw GPX data.

### Project structure

```
run-intelligence/
├── ingest.py          # GPX import: single file or --folder bulk
├── wellness.py        # Daily morning wellness questionnaire
├── context.py         # Generates data/context.md + data/session_log.md
├── plan.py            # Generates initial fixed training plan
├── db/
│   └── runs.db        # SQLite database
├── data/
│   ├── context.md     # Dynamic state snapshot (< 2000 tokens)
│   └── session_log.md # One line per session, last 12 weeks
├── CLAUDE.md          # Agent system prompt + loads data/context.md
└── base_teorica_running.md
```

---

## Commands

```bash
# One-time setup
python plan.py --goal 10k --weeks 12 --days 3

# Bulk historical import (no wellness, non-interactive)
python ingest.py --folder ./gpx_exports/

# Post-run ingest (pipeline + wellness questionnaire)
python ingest.py mi_carrera.gpx

# Daily morning wellness (rest days)
python wellness.py

# Manual context regeneration
python context.py

# Chat with agent
claude
```

`context.py` runs automatically at the end of `ingest.py` and `wellness.py` so
`data/context.md` is always fresh before a chat session.

---

## Database Schema

### `profile` — single row, user configuration
```sql
CREATE TABLE profile (
    id INTEGER PRIMARY KEY DEFAULT 1,
    age INTEGER NOT NULL,
    goal TEXT NOT NULL,              -- '5k' | '10k'
    plan_start_date TEXT,            -- ISO date
    plan_weeks INTEGER,              -- 8 | 12
    days_per_week INTEGER,           -- 3 | 4
    fcmax_manual INTEGER,            -- from protocol test
    fcmax_observed INTEGER,          -- highest p95 from history
    fcmax_estimated INTEGER,         -- Tanaka: 208 - (0.7 * age)
    fcmax_confidence TEXT            -- 'HIGH' | 'MEDIUM' | 'LOW'
);
```

**Active FCmax logic** (priority: manual > observed > estimated):
```sql
COALESCE(
    fcmax_manual,
    CASE WHEN fcmax_observed > fcmax_estimated THEN fcmax_observed ELSE NULL END,
    fcmax_estimated
)
```

### `sessions` — one row per run
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    source TEXT DEFAULT 'gpx',       -- 'gpx' | 'manual'
    distance_km REAL,
    duration_min REAL,
    avg_pace_sec_km REAL,
    avg_hr INTEGER,
    max_hr INTEGER,
    zone1_pct REAL, zone2_pct REAL, zone3_pct REAL,
    zone4_pct REAL, zone5_pct REAL,
    rpe_estimated REAL,              -- derived from avg HR zone midpoint
    rpe_actual REAL,                 -- from post-ingest wellness (NULL for bulk import)
    training_load REAL,              -- Foster: COALESCE(rpe_actual, rpe_estimated) × duration_min
    decoupling_pct REAL,             -- Friel: pace:HR ratio h1 vs h2
    cardiac_drift_bpm REAL,          -- HR linear trend at constant pace
    splits_json TEXT,                -- JSON: pace per km
    elevation_gain_m REAL,
    is_bulk_import INTEGER DEFAULT 0 -- 1 = historical, no wellness data
);
```

**RPE flow**: ingest computes `rpe_estimated` from HR zones immediately. Post-ingest
wellness asks actual RPE → updates `rpe_actual` and recalculates `training_load`.
Bulk import uses only `rpe_estimated` — training_load is approximate but consistent.

### `wellness` — daily subjective metrics
```sql
CREATE TABLE wellness (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    resting_hr INTEGER,
    sleep_quality INTEGER,           -- 1-5
    sleep_hours REAL,
    mood INTEGER,                    -- 1-5
    muscle_soreness INTEGER,         -- 1-5
    motivation INTEGER,              -- 1-5
    energy INTEGER,                  -- 1-5
    session_rpe REAL,                -- NULL when has_session = 0
    has_session INTEGER DEFAULT 0
);
```

### `metrics_snapshot` — daily fitness-fatigue state
```sql
CREATE TABLE metrics_snapshot (
    date TEXT PRIMARY KEY,
    atl REAL,   -- Acute Training Load (7-day exponential decay)
    ctl REAL,   -- Chronic Training Load (42-day exponential decay)
    tsb REAL    -- Training Stress Balance = CTL - ATL
);
```

### `plan_sessions` — immutable reference plan
```sql
CREATE TABLE plan_sessions (
    id INTEGER PRIMARY KEY,
    week INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,       -- 'mon' | 'wed' | 'fri' | etc.
    session_type TEXT NOT NULL,      -- 'easy' | 'tempo' | 'intervals' | 'long'
    target_distance_km REAL,
    target_duration_min REAL,
    target_rpe_min REAL,
    target_rpe_max REAL,
    target_zone TEXT,                -- 'Z1-2' | 'Z3-4' | 'Z4-5'
    notes TEXT
);
```

---

## Metrics Engine

### Layer A — Basic session metrics
- **Distance**: Haversine between consecutive GPS points
- **Splits**: exact pace per km
- **Elevation**: 30-second smoothing window to eliminate GPS noise
- **HR artifact filtering**: discard spikes > 220 bpm or changes > 30 bpm/s

### Layer B — Physiological metrics
- **HR zones**: calculated against active FCmax from `profile`
- **RPE estimate**: avg HR → zone → zone midpoint RPE (e.g. Z2 → RPE 3)
- **Training load (Foster)**: `session_rpe × duration_min`
- **Aerobic decoupling**: `(pace_hr_ratio_2nd_half / pace_hr_ratio_1st_half - 1) × 100`
  - < 5%: good | 5–8%: moderate | > 8%: fatigue signal
- **Cardiac drift**: linear regression slope of HR vs time at constant pace (±5%)

### Layer C — Fitness-fatigue model (Banister/Zatsiorsky)
- **ATL**: `Σ load_i × e^(-(t-i)/7)` — 7-day exponential decay
- **CTL**: `Σ load_i × e^(-(t-i)/42)` — 42-day exponential decay
- **TSB**: `CTL - ATL`
  - TSB > +10: fresh, ready for quality session
  - TSB -10/+10: normal training zone
  - TSB < -10: accumulated fatigue, prioritize easy
  - TSB < -30: red flag, consider rest day

### FCmax auto-update
After each ingest: if `percentile_95(session_hr) > fcmax_observed`, update `profile` and
notify user: "HR sostenido de Xbpm supera tu FCmax observada anterior. Zonas actualizadas."

---

## Context Document Format

### `data/context.md` (< 2000 tokens, regenerated automatically)

```markdown
# Estado actual — YYYY-MM-DD

## Perfil
- Objetivo: 10K | Plan: 12 semanas | Fase: Construcción (Semana 6/12)
- FCmax: 183 lpm (observada, confianza: MEDIA)
- Días/semana: 3

## Sesión más reciente — YYYY-MM-DD
- Distancia: 5.2 km | Duración: 32 min | Ritmo: 6:09/km
- HR: 152 prom / 171 máx → 83% FCmax → Zona 3 predominante (68%)
- Carga Foster: 224 AU | Decoupling: 4.2% ✓ | Drift: +8 lpm
- Plan decía: Carrera fácil 5 km Zona 1-2 (RPE 3-4)
- DELTA: corriste en Zona 3 — 13% sobre target de HR

## Estado de fatiga
- ATL: 187 | CTL: 156 | TSB: -31 ⚠️ (carga alta)
- Wellness hoy: sueño 4/5 | dolor muscular 2/5 | motivación 4/5

## Tendencias 4 semanas
- Volumen: ↑ 18% vs semana anterior (límite: 30%) ✓
- Decoupling: mejorando 7.1% → 4.2% ✓
- RPE creep: no detectado
- FC reposo: estable (promedio 7d: 52 lpm)

## Plan semana actual (Semana 6)
- ✅ Lun 13/4: Fácil 5 km — completada (desviación: Zona 3)
- ⬜ Mié 15/4: Tempo 10-15 min dentro de carrera 6 km
- ⬜ Vie 17/4: Larga 7 km Zona 1-2

## Principios activos
- TSB -31: priorizar recuperación. Considerar convertir tempo en fácil.
- Decoupling <5%: base aeróbica sólida.
- Semana 6/12: bloque Construcción, distribución 80/20 activa.
- Próxima descarga: Semana 8 (reducir 30% volumen).
```

### `data/session_log.md` (historical reference, ~300 tokens for 12 weeks)

```
fecha      | km   | min | pace  | HR avg/max | Z2%  | load | decoup | plan_type | delta
2026-04-13 | 5.2  | 32  | 6:09  | 152/171    | 12%  | 224  | 4.2%   | easy      | +zona
2026-04-10 | 6.1  | 38  | 6:14  | 148/165    | 71%  | 190  | 5.8%   | easy      | ok
```

---

## CLAUDE.md — Agent System Prompt

Two parts loaded automatically when `claude` starts in this directory:

### Part 1 — Static instructions (~800 tokens)

```markdown
# Run Intelligence — Agente de Coaching

Sos un coach de running para principiantes basado en evidencia científica.
Tu usuario tiene como objetivo completar su primera carrera de 5K o 10K.

## Principios que gobiernan toda prescripción

**SAID**: progresión limitada por tejido conectivo (tendones ~10 días/incremento),
no por sensación cardiovascular. "Sentirse capaz" ≠ "tendones listos".

**SRA**: regla hard-easy obligatoria. Máximo 2 sesiones duras/semana.
Descarga automática cada 3-4 semanas (reducir 30% volumen).

**SFR**: priorizar Zona 1-2 (SFR alto). Evitar Zona 3 (peor SFR posible).
Distribución 80/20 estricta.

**Fitness-Fatiga (Zatsiorsky/Banister)**:
TSB > +10 → apto calidad | TSB -10/+10 → normal | TSB < -30 → descanso.
Taper pre-carrera: reducir volumen 40-50%, 7-10 días, mantener intensidad.

**Efectos residuales (Issurin)**:
Resistencia aeróbica: 30±5 días. Velocidad: 5±3 días.

## Reglas de prescripción

1. Siempre mostrar DELTA entre plan fijo y prescripción real del día.
2. Nunca incrementar distancia + frecuencia + intensidad simultáneamente.
3. Si TSB < -30 o señal roja en wellness: convertir calidad en fácil.
4. Alertar si volumen semanal proyectado supera 30% de semana anterior.
5. Nunca prescribir test FCmax antes de 4-6 semanas de base aeróbica.
6. Máximo 2 sesiones de calidad por semana (tempo, intervalos, carrera larga).

## Contexto del estado actual
Lee: data/context.md
Para sesiones específicas: data/session_log.md
```

### Part 2 — Dynamic context
`CLAUDE.md` instructs Claude Code to read `data/context.md` at session start.
No manual intervention required — agent always has fresh state.

---

## FCmax Handling

### Priority chain
```
fcmax_manual (protocol test)          → confidence: HIGH
fcmax_observed (p95 from history)     → confidence: MEDIUM  (only if > estimated)
fcmax_estimated (Tanaka formula)      → confidence: LOW
```

### Default formula: Tanaka (2001, JACC)
`FCmax = 208 - (0.7 × age)`
More accurate than Fox (220 - age) for active adults 30–60.

### Manual calibration protocols
Blocked until user has 4–6 weeks of aerobic base in history.
- **Hill protocol**: 3 × uphill at increasing effort, p95 HR = FCmax
- **2km max effort**: 2km at absolute max sustainable pace, peak HR = FCmax

---

## Plan Generation (plan.py)

Generates `plan_sessions` table following evidence-based periodization:

| Phase | Weeks | Volume | Intensity | Sessions/week |
|-------|-------|--------|-----------|---------------|
| Base | 1-4 | 8-16 km | 100% easy (RPE 3-4) | 3-4 easy |
| Build | 5-8 | 15-25 km | 80/20 split | 2-3 easy + 1 tempo |
| Peak | 9-11 | 20-30 km | 80/20 + intervals | 2 easy + 1 quality |
| Taper | 12 | -40-50% | Maintain intensity | 2 easy + strides |

Deload week auto-inserted at weeks 4, 8 (30% volume reduction).
Progression: duration first, then frequency, then intensity — never simultaneously.

---

## Plan Model: Static Reference + Dynamic Override

The static plan (`plan_sessions`) is **never modified** after generation.
The agent prescribes the actual session based on current TSB, wellness, and trends,
always showing the delta vs the plan:

```
Plan decía:  Tempo 10-15 min dentro de carrera 6 km (RPE 6-7)
TSB hoy:     -31 (carga alta)
Prescripción: Carrera fácil 5 km Zona 1-2 (RPE 3-4)
Razón:        TSB < -30, tejido conectivo necesita recuperación
```

---

## Overtraining Detection (Meeusen et al. 2013)

Red flag triggers (any combination → agent recommends rest or medical consult):
- Resting HR consistently > 7-10 bpm above 7-day baseline for 3+ days
- Sleep quality ≤ 2/5 consistently
- RPE for easy runs rising to 6+/10
- Muscle soreness ≥ 3/5 for 3+ consecutive days
- 2+ wellness scores trending down simultaneously for 5+ days

---

## Tech Stack

- **Python 3.11+**: `gpxpy`, `numpy`, `sqlite3` (stdlib)
- **Agent**: Claude Code CLI — no Anthropic SDK required in pipeline
- **Storage**: SQLite (single file, zero overhead, local only)
- **No cloud dependencies**: 100% local execution
