# run-intelligence

Local CLI coaching agent for beginner runners targeting their first 5K or 10K.

Ingests Strava GPX exports → computes evidence-based metrics → persists in SQLite → surfaces a compressed context to a Claude Code agent that prescribes training sessions based on real data and scientific periodization.

---

## Requirements

- Python 3.11+
- [Claude Code CLI](https://claude.ai/code)

```bash
pip install -r requirements.txt
```

---

## Setup (one time)

```bash
# Create your profile and generate the training plan
python plan.py --goal 10k --weeks 12 --days 3 --age 32
```

Options:
- `--goal` — `5k` or `10k`
- `--weeks` — `8` (5K) or `12` (10K)
- `--days` — `3` or `4` sessions per week
- `--age` — used for Tanaka FCmax estimate (`208 - 0.7 × age`)

---

## Importing runs

```bash
# Bulk import historical GPX exports (no wellness prompts)
python ingest.py --folder ./gpx_exports/

# Import a single run (triggers post-run wellness questionnaire)
python ingest.py mi_carrera.gpx
```

Export GPX files from Strava: **Activity → ··· → Export GPX**.

After each import `data/context.md` is regenerated automatically.

---

## Daily wellness check-in

Run every morning (rest days included):

```bash
python wellness.py
```

Logs resting HR, sleep, mood, soreness, motivation, energy. Detects overtraining signals automatically.

---

## Chat with the agent

```bash
claude
```

The agent reads `data/context.md` at session start — current fitness-fatigue state, latest session, plan week, and active signals. No manual setup needed.

Example interactions:
- *"¿Qué hago hoy?"* → prescribes today's session with DELTA vs fixed plan
- *"Me siento muy cansado"* → adjusts based on TSB + wellness trends
- *"¿Cuándo hago el taper?"* → explains based on your race date

---

## How it works

```
GPX files → ingest.py → pipeline/ → SQLite (db/runs.db)
                                          ↓
                                     context.py
                                          ↓
                                   data/context.md  ←  CLAUDE.md loads this
                                          ↓
                                    claude (agent)
```

### Metrics computed per session

| Metric | Method |
|--------|--------|
| Distance | Haversine between GPS points |
| Pace splits | Per-km with interpolation |
| HR zones (Z1–Z5) | % of FCmax (Tanaka formula) |
| RPE estimate | Dominant HR zone midpoint |
| Training load | Foster: `RPE × duration_min` |
| Aerobic decoupling | Friel: EF ratio H1 vs H2 |
| Cardiac drift | Linear HR trend at constant pace |
| ATL / CTL / TSB | Banister exponential decay (7d / 42d) |

### FCmax priority chain

1. **Manual** (HIGH) — from a hill or 2km max-effort protocol
2. **Observed** (MEDIUM) — p95 of all session HR data, if > estimated
3. **Estimated** (LOW) — Tanaka: `208 - 0.7 × age`

### Training plan structure

| Phase | Weeks (12w) | Content |
|-------|-------------|---------|
| Base | 1–4 | 100% easy runs — build habit and aerobic base |
| Build | 5–8 | 80/20 split — add one tempo per week |
| Peak | 9–11 | 80/20 + intervals — race-specific quality |
| Taper | 12 | −40–50% volume, maintain intensity |

Deload week auto-inserted at weeks 4 and 8 (30% volume reduction).

---

## File structure

```
run-intelligence/
├── ingest.py          # GPX import: single file or --folder bulk
├── wellness.py        # Daily morning wellness questionnaire
├── context.py         # Generates data/context.md + data/session_log.md
├── plan.py            # Generates initial fixed training plan
├── db/
│   ├── schema.py      # SQLite schema + init_db + get_connection
│   └── queries.py     # All CRUD functions
├── pipeline/
│   ├── fcmax.py       # FCmax priority chain + Tanaka + p95
│   ├── gpx_parser.py  # GPX parsing + HR artifact filtering
│   └── metrics.py     # All metric calculations (Layers A, B, C)
├── data/
│   ├── context.md     # Generated — agent reads this (gitignored)
│   └── session_log.md # One line per session, last 12 weeks (gitignored)
├── CLAUDE.md          # Agent system prompt
└── tests/             # 75 tests
```

---

## Scientific basis

Coaching rules derive from six frameworks:

- **SAID** — progression limited by connective tissue adaptation (~10 days/increment), not cardiovascular feel
- **SRA cycle** (Yakovlev) — hard-easy alternation, 3:1 load/deload paradigm
- **SFR** (Israetel) — prioritize Zone 1-2 sessions (high stimulus, low fatigue); avoid Zone 3
- **Fitness-Fatigue model** (Banister/Zatsiorsky) — TSB-based readiness for quality sessions
- **Residual effects** (Issurin) — aerobic base persists 30±5 days; speed fades in 5±3 days
- **Polarized 80/20** (Seiler) — 80% easy, 20% high intensity; skip the grey zone
