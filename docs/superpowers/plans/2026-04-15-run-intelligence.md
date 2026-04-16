# Run Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Local CLI pipeline that ingests Strava GPX files, computes evidence-based running metrics, persists them in SQLite, and surfaces a compressed context document to a Claude Code coaching agent.

**Architecture:** Four-script CLI system (`ingest.py`, `wellness.py`, `plan.py`, `context.py`) backed by a SQLite database. A `pipeline/` package handles all metric computation. A generated `data/context.md` file is loaded by `CLAUDE.md` each time the user runs `claude` in this directory.

**Tech Stack:** Python 3.11+, `gpxpy` (GPX parsing), `numpy` (linear regression for cardiac drift), `sqlite3` (stdlib), Claude Code CLI (agent — no Anthropic SDK needed)

---

## File Map

```
run-intelligence/
├── db/
│   ├── schema.py          # CREATE TABLE + init_db() + get_connection()
│   └── queries.py         # All CRUD functions — single source of SQL truth
├── pipeline/
│   ├── fcmax.py           # FCmax priority chain + Tanaka formula + p95
│   ├── gpx_parser.py      # GPX parsing + HR artifact filtering
│   └── metrics.py         # All metric calculations (Layers A, B, C)
├── ingest.py              # CLI: single GPX or --folder bulk import
├── wellness.py            # CLI: daily wellness questionnaire
├── plan.py                # CLI: generate initial training plan
├── context.py             # CLI: regenerate data/context.md + data/session_log.md
├── data/
│   ├── context.md         # Generated — never edit manually
│   └── session_log.md     # Generated — never edit manually
├── CLAUDE.md              # Agent system prompt
├── tests/
│   ├── conftest.py        # Shared fixtures (tmp DB path, sample GPX)
│   ├── test_db.py
│   ├── test_fcmax.py
│   ├── test_gpx_parser.py
│   ├── test_metrics.py
│   ├── test_ingest.py
│   ├── test_wellness.py
│   ├── test_plan.py
│   └── test_context.py
├── requirements.txt
└── .gitignore
```

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `tests/conftest.py`
- Create: `.gitignore`
- Create: empty `__init__.py` files in `db/`, `pipeline/`, `tests/`

- [ ] **Step 1: Create requirements.txt**

```
gpxpy==1.6.2
numpy==2.2.4
pytest==8.3.5
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: all three packages install without errors.

- [ ] **Step 3: Create package init files**

```bash
mkdir -p db pipeline tests data
touch db/__init__.py pipeline/__init__.py tests/__init__.py
```

- [ ] **Step 4: Create conftest.py**

```python
# tests/conftest.py
import pytest
import os
import sqlite3

SAMPLE_GPX = """<?xml version="1.0"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
  <trk><trkseg>
    <trkpt lat="40.4165" lon="-3.7026">
      <ele>667</ele><time>2026-04-13T09:00:00Z</time>
      <extensions><gpxtpx:TrackPointExtension><gpxtpx:hr>140</gpxtpx:hr></gpxtpx:TrackPointExtension></extensions>
    </trkpt>
    <trkpt lat="40.4255" lon="-3.7026">
      <ele>669</ele><time>2026-04-13T09:06:00Z</time>
      <extensions><gpxtpx:TrackPointExtension><gpxtpx:hr>148</gpxtpx:hr></gpxtpx:TrackPointExtension></extensions>
    </trkpt>
    <trkpt lat="40.4345" lon="-3.7026">
      <ele>670</ele><time>2026-04-13T09:12:00Z</time>
      <extensions><gpxtpx:TrackPointExtension><gpxtpx:hr>152</gpxtpx:hr></gpxtpx:TrackPointExtension></extensions>
    </trkpt>
  </trkseg></trk>
</gpx>"""

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")

@pytest.fixture
def gpx_file(tmp_path):
    path = tmp_path / "test.gpx"
    path.write_text(SAMPLE_GPX)
    return str(path)
```

- [ ] **Step 5: Create .gitignore**

```
data/context.md
data/session_log.md
db/runs.db
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt tests/conftest.py .gitignore db/__init__.py pipeline/__init__.py tests/__init__.py
git commit -m "chore: project setup — deps, structure, test fixtures"
```

---

## Task 2: Database Module

**Files:**
- Create: `db/schema.py`
- Create: `db/queries.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_db.py
import pytest
import sqlite3
from db.schema import init_db, get_connection

def test_init_db_creates_all_tables(db_path):
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    assert tables == {'profile', 'sessions', 'wellness', 'metrics_snapshot', 'plan_sessions'}

def test_get_connection_returns_row_factory(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    conn.execute("INSERT INTO profile (age, goal, fcmax_estimated) VALUES (32, '10k', 186)")
    conn.commit()
    row = conn.execute("SELECT * FROM profile").fetchone()
    conn.close()
    assert row['age'] == 32
    assert row['goal'] == '10k'

def test_profile_fcmax_fields_nullable(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    conn.execute("INSERT INTO profile (age, goal, fcmax_estimated) VALUES (32, '10k', 186)")
    conn.commit()
    row = conn.execute("SELECT fcmax_manual, fcmax_observed FROM profile").fetchone()
    conn.close()
    assert row['fcmax_manual'] is None
    assert row['fcmax_observed'] is None
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_db.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'db.schema'`

- [ ] **Step 3: Implement db/schema.py**

```python
# db/schema.py
import sqlite3

CREATE_PROFILE = """
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY DEFAULT 1,
    age INTEGER NOT NULL,
    goal TEXT NOT NULL,
    plan_start_date TEXT,
    plan_weeks INTEGER,
    days_per_week INTEGER,
    fcmax_manual INTEGER,
    fcmax_observed INTEGER,
    fcmax_estimated INTEGER NOT NULL,
    fcmax_confidence TEXT DEFAULT 'LOW'
)"""

CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    source TEXT DEFAULT 'gpx',
    distance_km REAL,
    duration_min REAL,
    avg_pace_sec_km REAL,
    avg_hr INTEGER,
    max_hr INTEGER,
    zone1_pct REAL, zone2_pct REAL, zone3_pct REAL,
    zone4_pct REAL, zone5_pct REAL,
    rpe_estimated REAL,
    rpe_actual REAL,
    training_load REAL,
    decoupling_pct REAL,
    cardiac_drift_bpm REAL,
    splits_json TEXT,
    elevation_gain_m REAL,
    is_bulk_import INTEGER DEFAULT 0
)"""

CREATE_WELLNESS = """
CREATE TABLE IF NOT EXISTS wellness (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    resting_hr INTEGER,
    sleep_quality INTEGER,
    sleep_hours REAL,
    mood INTEGER,
    muscle_soreness INTEGER,
    motivation INTEGER,
    energy INTEGER,
    session_rpe REAL,
    has_session INTEGER DEFAULT 0
)"""

CREATE_METRICS_SNAPSHOT = """
CREATE TABLE IF NOT EXISTS metrics_snapshot (
    date TEXT PRIMARY KEY,
    atl REAL NOT NULL,
    ctl REAL NOT NULL,
    tsb REAL NOT NULL
)"""

CREATE_PLAN_SESSIONS = """
CREATE TABLE IF NOT EXISTS plan_sessions (
    id INTEGER PRIMARY KEY,
    week INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,
    session_type TEXT NOT NULL,
    target_distance_km REAL,
    target_duration_min REAL,
    target_rpe_min REAL,
    target_rpe_max REAL,
    target_zone TEXT,
    notes TEXT
)"""


def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    for stmt in [CREATE_PROFILE, CREATE_SESSIONS, CREATE_WELLNESS,
                 CREATE_METRICS_SNAPSHOT, CREATE_PLAN_SESSIONS]:
        conn.execute(stmt)
    conn.commit()
    conn.close()


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
```

- [ ] **Step 4: Implement db/queries.py**

```python
# db/queries.py
import json
import sqlite3
from typing import Optional


def get_profile(conn: sqlite3.Connection) -> Optional[dict]:
    row = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    return dict(row) if row else None


def upsert_profile(conn: sqlite3.Connection, data: dict) -> None:
    existing = get_profile(conn)
    if existing:
        fields = ', '.join(f"{k}=?" for k in data)
        conn.execute(f"UPDATE profile SET {fields} WHERE id=1", list(data.values()))
    else:
        data.setdefault('id', 1)
        fields = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        conn.execute(f"INSERT INTO profile ({fields}) VALUES ({placeholders})", list(data.values()))
    conn.commit()


def update_fcmax_observed(conn: sqlite3.Connection, fcmax: int) -> None:
    conn.execute("UPDATE profile SET fcmax_observed=? WHERE id=1", (fcmax,))
    conn.commit()


def insert_session(conn: sqlite3.Connection, data: dict) -> int:
    fields = ', '.join(data.keys())
    placeholders = ', '.join('?' * len(data))
    cursor = conn.execute(
        f"INSERT INTO sessions ({fields}) VALUES ({placeholders})",
        list(data.values())
    )
    conn.commit()
    return cursor.lastrowid


def update_session_rpe(conn: sqlite3.Connection, session_id: int, rpe_actual: float) -> None:
    conn.execute(
        "UPDATE sessions SET rpe_actual=?, training_load=COALESCE(?,rpe_estimated)*duration_min WHERE id=?",
        (rpe_actual, rpe_actual, session_id)
    )
    conn.commit()


def get_latest_session(conn: sqlite3.Connection) -> Optional[dict]:
    row = conn.execute("SELECT * FROM sessions ORDER BY date DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def get_sessions_for_period(conn: sqlite3.Connection, start_date: str, end_date: str) -> list:
    rows = conn.execute(
        "SELECT * FROM sessions WHERE date BETWEEN ? AND ? ORDER BY date",
        (start_date, end_date)
    ).fetchall()
    return [dict(r) for r in rows]


def get_all_sessions_loads(conn: sqlite3.Connection) -> list:
    """Returns [(date, training_load)] sorted by date ASC."""
    rows = conn.execute(
        "SELECT date, COALESCE(training_load, 0) as load FROM sessions ORDER BY date"
    ).fetchall()
    return [(r['date'], r['load']) for r in rows]


def insert_wellness(conn: sqlite3.Connection, date: str, data: dict) -> None:
    data['date'] = date
    fields = ', '.join(data.keys())
    placeholders = ', '.join('?' * len(data))
    conn.execute(
        f"INSERT OR REPLACE INTO wellness ({fields}) VALUES ({placeholders})",
        list(data.values())
    )
    conn.commit()


def get_wellness_for_date(conn: sqlite3.Connection, date: str) -> Optional[dict]:
    row = conn.execute("SELECT * FROM wellness WHERE date=?", (date,)).fetchone()
    return dict(row) if row else None


def get_wellness_history(conn: sqlite3.Connection, days: int = 14) -> list:
    rows = conn.execute(
        "SELECT * FROM wellness ORDER BY date DESC LIMIT ?", (days,)
    ).fetchall()
    return [dict(r) for r in rows]


def insert_metrics_snapshot(conn: sqlite3.Connection, date: str,
                             atl: float, ctl: float, tsb: float) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO metrics_snapshot (date,atl,ctl,tsb) VALUES (?,?,?,?)",
        (date, atl, ctl, tsb)
    )
    conn.commit()


def get_latest_metrics_snapshot(conn: sqlite3.Connection) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM metrics_snapshot ORDER BY date DESC LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


def insert_plan_sessions(conn: sqlite3.Connection, sessions: list) -> None:
    conn.execute("DELETE FROM plan_sessions")
    for s in sessions:
        fields = ', '.join(s.keys())
        placeholders = ', '.join('?' * len(s))
        conn.execute(f"INSERT INTO plan_sessions ({fields}) VALUES ({placeholders})",
                     list(s.values()))
    conn.commit()


def get_plan_week(conn: sqlite3.Connection, week: int) -> list:
    rows = conn.execute(
        "SELECT * FROM plan_sessions WHERE week=? ORDER BY id", (week,)
    ).fetchall()
    return [dict(r) for r in rows]
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_db.py -v`
Expected: 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add db/schema.py db/queries.py tests/test_db.py
git commit -m "feat: database schema and query module"
```

---

## Task 3: FCmax Module

**Files:**
- Create: `pipeline/fcmax.py`
- Create: `tests/test_fcmax.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_fcmax.py
from pipeline.fcmax import fcmax_tanaka, p95_hr, get_active_fcmax, should_update_fcmax_observed

def test_tanaka_age_32():
    # 208 - 0.7 * 32 = 208 - 22.4 = 185.6 → 186
    assert fcmax_tanaka(32) == 186

def test_tanaka_age_40():
    # 208 - 0.7 * 40 = 208 - 28 = 180
    assert fcmax_tanaka(40) == 180

def test_p95_hr_basic():
    hr = list(range(100, 200))  # 100 values: 100..199
    # index 95 of sorted = value 195
    assert p95_hr(hr) == 195

def test_p95_hr_filters_spike():
    hr = [140, 142, 141, 143, 142]
    result = p95_hr(hr)
    assert result <= 143

def test_get_active_fcmax_manual_priority():
    profile = {'fcmax_manual': 195, 'fcmax_observed': 185, 'fcmax_estimated': 186}
    fcmax, confidence = get_active_fcmax(profile)
    assert fcmax == 195
    assert confidence == 'HIGH'

def test_get_active_fcmax_observed_when_higher_than_estimated():
    profile = {'fcmax_manual': None, 'fcmax_observed': 188, 'fcmax_estimated': 186}
    fcmax, confidence = get_active_fcmax(profile)
    assert fcmax == 188
    assert confidence == 'MEDIUM'

def test_get_active_fcmax_estimated_when_observed_lower():
    profile = {'fcmax_manual': None, 'fcmax_observed': 180, 'fcmax_estimated': 186}
    fcmax, confidence = get_active_fcmax(profile)
    assert fcmax == 186
    assert confidence == 'LOW'

def test_get_active_fcmax_estimated_fallback():
    profile = {'fcmax_manual': None, 'fcmax_observed': None, 'fcmax_estimated': 186}
    fcmax, confidence = get_active_fcmax(profile)
    assert fcmax == 186
    assert confidence == 'LOW'

def test_should_update_fcmax_observed_true():
    hr_values = list(range(150, 195))  # p95 = 193
    assert should_update_fcmax_observed(hr_values, current_observed=185) is True

def test_should_update_fcmax_observed_false():
    hr_values = list(range(130, 170))  # p95 = 168
    assert should_update_fcmax_observed(hr_values, current_observed=185) is False
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_fcmax.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.fcmax'`

- [ ] **Step 3: Implement pipeline/fcmax.py**

```python
# pipeline/fcmax.py
from typing import Optional


def fcmax_tanaka(age: int) -> int:
    """Tanaka (2001, JACC): 208 - 0.7 × age. More accurate than Fox for adults 30-60."""
    return round(208 - 0.7 * age)


def p95_hr(hr_values: list[int]) -> int:
    """95th percentile HR — robust FCmax estimator from submaximal efforts."""
    if not hr_values:
        return 0
    sorted_hr = sorted(hr_values)
    idx = int(len(sorted_hr) * 0.95)
    return sorted_hr[idx]


def get_active_fcmax(profile: dict) -> tuple[int, str]:
    """
    Priority chain:
    1. fcmax_manual (HIGH) — from protocol test
    2. fcmax_observed (MEDIUM) — only if > estimated
    3. fcmax_estimated (LOW) — Tanaka formula
    """
    if profile.get('fcmax_manual'):
        return profile['fcmax_manual'], 'HIGH'
    observed = profile.get('fcmax_observed')
    estimated = profile.get('fcmax_estimated', 0)
    if observed and observed > estimated:
        return observed, 'MEDIUM'
    return estimated, 'LOW'


def should_update_fcmax_observed(hr_values: list[int], current_observed: Optional[int]) -> bool:
    """Return True if p95 of current session exceeds known fcmax_observed."""
    session_p95 = p95_hr(hr_values)
    if current_observed is None:
        return session_p95 > 0
    return session_p95 > current_observed
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_fcmax.py -v`
Expected: 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/fcmax.py tests/test_fcmax.py
git commit -m "feat: FCmax module — Tanaka formula, p95, priority chain"
```

---

## Task 4: GPX Parser

**Files:**
- Create: `pipeline/gpx_parser.py`
- Create: `tests/test_gpx_parser.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_gpx_parser.py
import pytest
from pipeline.gpx_parser import parse_gpx, filter_hr_artifacts

def test_parse_gpx_returns_four_streams(gpx_file):
    coords, elevations, hr_values, timestamps = parse_gpx(gpx_file)
    assert len(coords) == 3
    assert len(elevations) == 3
    assert len(hr_values) == 3
    assert len(timestamps) == 3

def test_parse_gpx_coords_are_lat_lon_tuples(gpx_file):
    coords, _, _, _ = parse_gpx(gpx_file)
    lat, lon = coords[0]
    assert 40.41 < lat < 40.42
    assert -3.71 < lon < -3.70

def test_parse_gpx_timestamps_are_seconds(gpx_file):
    _, _, _, timestamps = parse_gpx(gpx_file)
    assert timestamps[0] == 0
    assert timestamps[1] == 360   # 6 minutes = 360 seconds
    assert timestamps[2] == 720

def test_parse_gpx_hr_values(gpx_file):
    _, _, hr_values, _ = parse_gpx(gpx_file)
    assert hr_values == [140, 148, 152]

def test_parse_gpx_no_hr_returns_empty_list(tmp_path):
    gpx_no_hr = """<?xml version="1.0"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="40.4165" lon="-3.7026"><ele>667</ele><time>2026-04-13T09:00:00Z</time></trkpt>
    <trkpt lat="40.4255" lon="-3.7026"><ele>668</ele><time>2026-04-13T09:01:00Z</time></trkpt>
  </trkseg></trk>
</gpx>"""
    f = tmp_path / "no_hr.gpx"
    f.write_text(gpx_no_hr)
    coords, elevs, hr_values, timestamps = parse_gpx(str(f))
    assert hr_values == []
    assert len(coords) == 2

def test_filter_hr_artifacts_removes_above_220():
    hr = [140, 142, 221, 141]
    assert 221 not in filter_hr_artifacts(hr)

def test_filter_hr_artifacts_removes_fast_changes():
    # 140 → 175 in 1 second = 35 bpm/s (threshold: 30 bpm/s)
    hr = [140, 175, 141]
    filtered = filter_hr_artifacts(hr)
    assert 175 not in filtered

def test_filter_hr_artifacts_keeps_valid():
    hr = [140, 142, 144, 143, 145]
    filtered = filter_hr_artifacts(hr)
    assert filtered == [140, 142, 144, 143, 145]
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_gpx_parser.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement pipeline/gpx_parser.py**

```python
# pipeline/gpx_parser.py
import gpxpy
import gpxpy.gpx
from datetime import timezone


def parse_gpx(path: str) -> tuple[list, list, list, list]:
    """
    Parse GPX file into four synchronized streams.
    Returns:
        coords:     [(lat, lon), ...]
        elevations: [float, ...]  in meters
        hr_values:  [int, ...]    bpm, empty list if no HR data
        timestamps: [int, ...]    seconds from first point
    """
    with open(path, 'r') as f:
        gpx = gpxpy.parse(f)

    coords, elevations, hr_raw, times_abs = [], [], [], []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                coords.append((point.latitude, point.longitude))
                elevations.append(point.elevation or 0.0)
                times_abs.append(point.time.replace(tzinfo=timezone.utc).timestamp()
                                  if point.time else 0)
                # HR is stored in Garmin TrackPointExtension
                hr = None
                if point.extensions:
                    for ext in point.extensions:
                        for child in ext:
                            if 'hr' in child.tag.lower():
                                try:
                                    hr = int(child.text)
                                except (ValueError, TypeError):
                                    pass
                hr_raw.append(hr)

    if not times_abs:
        return [], [], [], []

    t0 = times_abs[0]
    timestamps = [int(t - t0) for t in times_abs]

    # Return empty list if no HR data at all
    has_hr = any(h is not None for h in hr_raw)
    hr_values = [h if h is not None else 0 for h in hr_raw] if has_hr else []

    return coords, elevations, hr_values, timestamps


def filter_hr_artifacts(hr_values: list[int],
                         max_bpm: int = 220,
                         max_change_per_sec: int = 30) -> list[int]:
    """
    Remove physiologically impossible HR values.
    - Discard any value > max_bpm
    - Discard values where change from previous > max_change_per_sec
    """
    if not hr_values:
        return []

    filtered = [hr_values[0]] if hr_values[0] <= max_bpm else []

    for i in range(1, len(hr_values)):
        hr = hr_values[i]
        if hr > max_bpm:
            continue
        if filtered and abs(hr - filtered[-1]) > max_change_per_sec:
            continue
        filtered.append(hr)

    return filtered
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_gpx_parser.py -v`
Expected: 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/gpx_parser.py tests/test_gpx_parser.py
git commit -m "feat: GPX parser with HR artifact filtering"
```

---

## Task 5: Metrics Layer A — Distance, Splits, Elevation

**Files:**
- Create: `pipeline/metrics.py`
- Create: `tests/test_metrics.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_metrics.py
import pytest
from pipeline.metrics import (
    haversine, calculate_distance, calculate_speed_stream,
    calculate_splits, smooth_elevation, calculate_elevation_gain_loss
)

def test_haversine_known_distance():
    # Two points ~1km apart (north-south in Madrid)
    dist = haversine(40.4165, -3.7026, 40.4255, -3.7026)
    assert 990 < dist < 1010

def test_haversine_same_point():
    assert haversine(40.0, -3.0, 40.0, -3.0) == 0.0

def test_calculate_distance_sums_segments(gpx_file):
    from pipeline.gpx_parser import parse_gpx
    coords, _, _, _ = parse_gpx(gpx_file)
    # Two ~1km segments
    dist = calculate_distance(coords)
    assert 1900 < dist < 2100  # ~2km total

def test_calculate_speed_stream_length(gpx_file):
    from pipeline.gpx_parser import parse_gpx
    coords, _, _, timestamps = parse_gpx(gpx_file)
    speeds = calculate_speed_stream(coords, timestamps)
    assert len(speeds) == len(coords) - 1

def test_calculate_speed_stream_value(gpx_file):
    from pipeline.gpx_parser import parse_gpx
    coords, _, _, timestamps = parse_gpx(gpx_file)
    speeds = calculate_speed_stream(coords, timestamps)
    # ~1000m in 360s ≈ 2.78 m/s
    assert 2.5 < speeds[0] < 3.1

def test_calculate_splits_pace(gpx_file):
    from pipeline.gpx_parser import parse_gpx
    coords, _, _, timestamps = parse_gpx(gpx_file)
    splits = calculate_splits(coords, timestamps)
    # ~360 sec/km
    assert len(splits) >= 1
    assert 340 < splits[0] < 380

def test_smooth_elevation_reduces_variance():
    import statistics
    elevations = [100, 105, 98, 103, 97, 104, 100, 102, 99, 101]
    timestamps = list(range(10))
    smoothed = smooth_elevation(elevations, timestamps, window_sec=3)
    assert len(smoothed) == len(elevations)
    assert statistics.stdev(smoothed) < statistics.stdev(elevations)

def test_calculate_elevation_gain():
    # 0 → 10 → 5 → 15 → 12: gain = 10 + 10 = 20, loss = 5 + 3 = 8
    elevations = [0.0, 10.0, 5.0, 15.0, 12.0]
    gain, loss = calculate_elevation_gain_loss(elevations)
    assert gain == pytest.approx(20.0)
    assert loss == pytest.approx(8.0)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_metrics.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.metrics'`

- [ ] **Step 3: Implement Layer A in pipeline/metrics.py**

```python
# pipeline/metrics.py
import math
from typing import Optional


# ─── Layer A: Basic session metrics ──────────────────────────────────────────

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in meters between two GPS coordinates."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def calculate_distance(coords: list[tuple]) -> float:
    """Total distance in meters."""
    return sum(haversine(*coords[i-1], *coords[i]) for i in range(1, len(coords)))


def calculate_speed_stream(coords: list[tuple], timestamps: list[int]) -> list[float]:
    """Speed in m/s between consecutive GPS points."""
    speeds = []
    for i in range(1, len(coords)):
        dist = haversine(*coords[i-1], *coords[i])
        dt = timestamps[i] - timestamps[i-1]
        speeds.append(dist / dt if dt > 0 else 0.0)
    return speeds


def calculate_splits(coords: list[tuple], timestamps: list[int]) -> list[int]:
    """
    Pace in seconds/km for each complete kilometer.
    Returns list of sec/km values.
    """
    splits = []
    km_start_time = timestamps[0]
    km_start_dist = 0.0
    cumulative_dist = 0.0
    km_count = 0

    for i in range(1, len(coords)):
        seg_dist = haversine(*coords[i-1], *coords[i])
        cumulative_dist += seg_dist

        while cumulative_dist >= (km_count + 1) * 1000:
            km_count += 1
            # Interpolate time at exactly km boundary
            overshoot = cumulative_dist - km_count * 1000
            seg_time = timestamps[i] - timestamps[i-1]
            fraction = 1 - (overshoot / seg_dist) if seg_dist > 0 else 1
            km_end_time = timestamps[i-1] + seg_time * fraction
            splits.append(round(km_end_time - km_start_time))
            km_start_time = km_end_time

    return splits


def smooth_elevation(elevations: list[float],
                      timestamps: list[int],
                      window_sec: int = 30) -> list[float]:
    """Moving average over a time window to remove GPS noise."""
    smoothed = []
    for i, t in enumerate(timestamps):
        window = [
            elevations[j]
            for j, ts in enumerate(timestamps)
            if abs(ts - t) <= window_sec // 2
        ]
        smoothed.append(sum(window) / len(window))
    return smoothed


def calculate_elevation_gain_loss(elevations: list[float]) -> tuple[float, float]:
    """Total elevation gain and loss in meters."""
    gain, loss = 0.0, 0.0
    for i in range(1, len(elevations)):
        delta = elevations[i] - elevations[i-1]
        if delta > 0:
            gain += delta
        else:
            loss += abs(delta)
    return round(gain, 1), round(loss, 1)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_metrics.py -v`
Expected: 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/metrics.py tests/test_metrics.py
git commit -m "feat: metrics Layer A — haversine, splits, elevation"
```

---

## Task 6: Metrics Layer B — Zones, RPE, Foster, Decoupling, Drift

**Files:**
- Modify: `pipeline/metrics.py` (add Layer B functions)
- Modify: `tests/test_metrics.py` (add Layer B tests)

- [ ] **Step 1: Write failing tests (append to test_metrics.py)**

```python
# Append to tests/test_metrics.py
from pipeline.metrics import (
    calculate_zones, estimate_rpe, foster_load,
    aerobic_decoupling, cardiac_drift
)

def test_calculate_zones_all_zone2():
    fcmax = 180
    # Z2: 60–72% FCmax → 108–130 bpm
    hr_values = [115] * 100
    zones = calculate_zones(hr_values, fcmax)
    assert zones[1] == pytest.approx(100.0)  # index 1 = Z2
    assert zones[0] == pytest.approx(0.0)

def test_calculate_zones_split():
    fcmax = 180
    # 50 points Z2 (115 bpm), 50 points Z4 (157 bpm)
    hr_values = [115] * 50 + [157] * 50
    zones = calculate_zones(hr_values, fcmax)
    assert zones[1] == pytest.approx(50.0)
    assert zones[3] == pytest.approx(50.0)

def test_calculate_zones_empty_hr():
    zones = calculate_zones([], fcmax=180)
    assert zones == [0.0, 0.0, 0.0, 0.0, 0.0]

def test_estimate_rpe_zone1():
    zone_pcts = [100.0, 0.0, 0.0, 0.0, 0.0]
    assert estimate_rpe(zone_pcts) == 1.5

def test_estimate_rpe_zone2():
    zone_pcts = [0.0, 100.0, 0.0, 0.0, 0.0]
    assert estimate_rpe(zone_pcts) == 3.0

def test_foster_load():
    assert foster_load(rpe=3.0, duration_min=40) == pytest.approx(120.0)

def test_aerobic_decoupling_no_drift():
    # Identical speed and HR throughout → 0%
    speed = [3.0] * 100
    hr = [150.0] * 100
    assert aerobic_decoupling(speed, hr) == pytest.approx(0.0)

def test_aerobic_decoupling_positive_when_efficiency_drops():
    # H1: EF = 3/150 = 0.02. H2: same speed but higher HR → EF < 0.02 → decoupling > 0
    speed = [3.0] * 100
    hr = [140.0] * 50 + [160.0] * 50
    result = aerobic_decoupling(speed, hr)
    assert result > 0

def test_cardiac_drift_positive_trend():
    import numpy as np
    # HR increases steadily at constant speed
    times = list(range(100))
    hr = [140 + i * 0.2 for i in range(100)]  # +0.2 bpm/sec = +720 bpm/hr
    speed = [3.0] * 100
    drift = cardiac_drift(times, hr, speed)
    assert drift is not None
    assert drift > 0

def test_cardiac_drift_none_when_insufficient_data():
    times = list(range(5))
    hr = [140, 141, 142, 143, 144]
    speed = [3.0] * 5
    assert cardiac_drift(times, hr, speed, speed_tolerance=0.05) is None
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_metrics.py -k "zone or rpe or foster or decoupling or drift" -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement Layer B (append to pipeline/metrics.py)**

```python
# Append to pipeline/metrics.py

import numpy as np

# ─── Layer B: Physiological metrics ──────────────────────────────────────────

ZONE_BOUNDS = [
    (0.00, 0.60),   # Z1: < 60% FCmax
    (0.60, 0.72),   # Z2: 60–72%
    (0.72, 0.82),   # Z3: 72–82%
    (0.82, 0.90),   # Z4: 82–90%
    (0.90, 1.01),   # Z5: > 90%
]

ZONE_RPE_MIDPOINTS = {1: 1.5, 2: 3.0, 3: 5.0, 4: 7.0, 5: 9.0}


def calculate_zones(hr_values: list[int], fcmax: int) -> list[float]:
    """Returns [z1_pct, z2_pct, z3_pct, z4_pct, z5_pct]."""
    if not hr_values:
        return [0.0] * 5
    total = len(hr_values)
    result = []
    for low, high in ZONE_BOUNDS:
        count = sum(1 for hr in hr_values if low * fcmax <= hr < high * fcmax)
        result.append(round(count / total * 100, 1))
    return result


def estimate_rpe(zone_pcts: list[float]) -> float:
    """RPE estimate from dominant HR zone. Uses zone midpoint RPE values."""
    dominant_zone = zone_pcts.index(max(zone_pcts)) + 1
    return ZONE_RPE_MIDPOINTS[dominant_zone]


def foster_load(rpe: float, duration_min: float) -> float:
    """Foster Session RPE load: RPE (CR-10) × duration in minutes."""
    return round(rpe * duration_min, 1)


def aerobic_decoupling(speed_values: list[float], hr_values: list[float]) -> float:
    """
    Friel aerobic decoupling: efficiency factor degradation from H1 to H2.
    EF = avg_speed / avg_hr. Positive = efficiency dropped. < 5% = good.
    """
    if len(speed_values) < 4:
        return 0.0
    mid = len(speed_values) // 2
    ef_h1 = (sum(speed_values[:mid]) / mid) / (sum(hr_values[:mid]) / mid)
    ef_h2 = (sum(speed_values[mid:]) / (len(speed_values) - mid)) / \
            (sum(hr_values[mid:]) / (len(hr_values) - mid))
    return round((ef_h1 - ef_h2) / ef_h1 * 100, 2)


def cardiac_drift(times_sec: list[int], hr_values: list[float],
                   speed_values: list[float],
                   speed_tolerance: float = 0.05,
                   min_points: int = 10) -> Optional[float]:
    """
    HR linear trend at constant pace (±speed_tolerance of mean speed).
    Returns bpm/hour. Positive = HR drifting up. None if insufficient stable data.
    """
    if not speed_values:
        return None
    mean_speed = sum(speed_values) / len(speed_values)
    low = mean_speed * (1 - speed_tolerance)
    high = mean_speed * (1 + speed_tolerance)

    stable = [(t, h) for t, s, h in zip(times_sec, speed_values, hr_values)
              if low <= s <= high]

    if len(stable) < min_points:
        return None

    t_arr = np.array([p[0] for p in stable], dtype=float)
    h_arr = np.array([p[1] for p in stable], dtype=float)
    slope = np.polyfit(t_arr, h_arr, 1)[0]  # bpm/second
    return round(float(slope) * 3600, 2)     # convert to bpm/hour
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_metrics.py -v`
Expected: all tests PASS (Layer A + B combined).

- [ ] **Step 5: Commit**

```bash
git add pipeline/metrics.py tests/test_metrics.py
git commit -m "feat: metrics Layer B — zones, RPE, Foster load, decoupling, cardiac drift"
```

---

## Task 7: Metrics Layer C — ATL, CTL, TSB

**Files:**
- Modify: `pipeline/metrics.py` (add Layer C functions)
- Modify: `tests/test_metrics.py` (add Layer C tests)

- [ ] **Step 1: Write failing tests (append to test_metrics.py)**

```python
# Append to tests/test_metrics.py
from pipeline.metrics import calculate_atl_ctl

def test_atl_ctl_empty():
    atl, ctl = calculate_atl_ctl([])
    assert atl == 0.0
    assert ctl == 0.0

def test_atl_ctl_single_session_same_day():
    # e^(0/7) = 1, e^(0/42) = 1 → ATL = CTL = 200
    atl, ctl = calculate_atl_ctl([("2026-04-15", 200.0)], reference_date="2026-04-15")
    assert atl == pytest.approx(200.0, rel=0.01)
    assert ctl == pytest.approx(200.0, rel=0.01)

def test_atl_decays_faster_than_ctl():
    # Session from 10 days ago
    sessions = [("2026-04-05", 200.0)]
    atl, ctl = calculate_atl_ctl(sessions, reference_date="2026-04-15")
    # ATL: 200 * e^(-10/7) ≈ 47.8
    # CTL: 200 * e^(-10/42) ≈ 157.2
    assert atl < ctl

def test_tsb_negative_after_big_session():
    # Big session yesterday → ATL > CTL → TSB < 0
    sessions = [("2026-04-14", 500.0)]
    atl, ctl = calculate_atl_ctl(sessions, reference_date="2026-04-15")
    tsb = ctl - atl
    assert tsb < 0

def test_atl_ctl_defaults_to_last_session_date():
    sessions = [("2026-04-10", 150.0), ("2026-04-13", 200.0)]
    atl, ctl = calculate_atl_ctl(sessions)  # no reference_date → uses 2026-04-13
    # Both sessions contribute; ATL > 0
    assert atl > 0
    assert ctl > 0
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_metrics.py -k "atl or ctl or tsb" -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement Layer C (append to pipeline/metrics.py)**

```python
# Append to pipeline/metrics.py
from datetime import datetime

# ─── Layer C: Fitness-Fatigue model (Banister/Zatsiorsky) ────────────────────

def calculate_atl_ctl(sessions_loads: list[tuple[str, float]],
                       reference_date: Optional[str] = None,
                       decay_atl: int = 7,
                       decay_ctl: int = 42) -> tuple[float, float]:
    """
    Exponential decay fitness-fatigue model.
    sessions_loads: [(date_iso, load), ...] sorted ascending.
    reference_date: date to calculate ATL/CTL for. Defaults to last session date.
    Returns (ATL, CTL).
    """
    if not sessions_loads:
        return 0.0, 0.0

    ref = reference_date or sessions_loads[-1][0]
    ref_dt = datetime.fromisoformat(ref)

    atl, ctl = 0.0, 0.0
    for date_str, load in sessions_loads:
        days_ago = (ref_dt - datetime.fromisoformat(date_str)).days
        if days_ago < 0:
            continue  # future sessions (shouldn't happen)
        atl += load * math.exp(-days_ago / decay_atl)
        ctl += load * math.exp(-days_ago / decay_ctl)

    return round(atl, 2), round(ctl, 2)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_metrics.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/metrics.py tests/test_metrics.py
git commit -m "feat: metrics Layer C — ATL/CTL/TSB fitness-fatigue model"
```

---

## Task 8: Ingest Pipeline

**Files:**
- Create: `ingest.py`
- Create: `tests/test_ingest.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_ingest.py
import pytest
import os
from db.schema import init_db, get_connection
from db.queries import get_profile, get_latest_session, get_all_sessions_loads
from ingest import process_gpx_file, recalculate_metrics_snapshots

PROFILE = {
    'age': 32,
    'goal': '10k',
    'fcmax_estimated': 186,
    'fcmax_observed': None,
    'fcmax_manual': None,
}

def test_process_gpx_file_returns_session_dict(db_path, gpx_file):
    init_db(db_path)
    conn = get_connection(db_path)
    from db.queries import upsert_profile
    upsert_profile(conn, PROFILE)
    conn.close()
    session = process_gpx_file(gpx_file, fcmax=186)
    assert 'distance_km' in session
    assert 'duration_min' in session
    assert 'avg_hr' in session
    assert 'rpe_estimated' in session
    assert 'training_load' in session
    assert session['distance_km'] > 0

def test_process_gpx_file_distance_approx_2km(db_path, gpx_file):
    session = process_gpx_file(gpx_file, fcmax=186)
    assert 1.8 < session['distance_km'] < 2.2

def test_process_gpx_file_zone_pcts_sum_to_100(gpx_file):
    session = process_gpx_file(gpx_file, fcmax=186)
    total = sum([session['zone1_pct'], session['zone2_pct'], session['zone3_pct'],
                 session['zone4_pct'], session['zone5_pct']])
    assert total == pytest.approx(100.0, abs=1.0)

def test_recalculate_metrics_snapshots(db_path, gpx_file):
    init_db(db_path)
    conn = get_connection(db_path)
    from db.queries import insert_session, upsert_profile
    upsert_profile(conn, PROFILE)
    insert_session(conn, {
        'date': '2026-04-10', 'distance_km': 5.0, 'duration_min': 32.0,
        'rpe_estimated': 3.0, 'training_load': 96.0,
        'zone1_pct': 0, 'zone2_pct': 80, 'zone3_pct': 20,
        'zone4_pct': 0, 'zone5_pct': 0, 'avg_hr': 145, 'max_hr': 160,
    })
    insert_session(conn, {
        'date': '2026-04-13', 'distance_km': 6.0, 'duration_min': 38.0,
        'rpe_estimated': 3.0, 'training_load': 114.0,
        'zone1_pct': 0, 'zone2_pct': 75, 'zone3_pct': 25,
        'zone4_pct': 0, 'zone5_pct': 0, 'avg_hr': 148, 'max_hr': 163,
    })
    conn.close()
    recalculate_metrics_snapshots(db_path)
    conn = get_connection(db_path)
    snap = conn.execute(
        "SELECT * FROM metrics_snapshot ORDER BY date DESC LIMIT 1"
    ).fetchone()
    conn.close()
    assert snap is not None
    assert snap['atl'] > 0
    assert snap['ctl'] > 0
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_ingest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ingest'`

- [ ] **Step 3: Implement ingest.py**

```python
# ingest.py
import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import date as date_cls

from db.schema import init_db, get_connection
from db.queries import (
    get_profile, upsert_profile, insert_session, update_session_rpe,
    insert_wellness, get_all_sessions_loads, insert_metrics_snapshot,
    update_fcmax_observed
)
from pipeline.gpx_parser import parse_gpx, filter_hr_artifacts
from pipeline.fcmax import (
    fcmax_tanaka, get_active_fcmax, should_update_fcmax_observed, p95_hr
)
from pipeline.metrics import (
    calculate_distance, calculate_speed_stream, calculate_splits,
    smooth_elevation, calculate_elevation_gain_loss,
    calculate_zones, estimate_rpe, foster_load,
    aerobic_decoupling, cardiac_drift, calculate_atl_ctl
)

DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'runs.db')


def process_gpx_file(gpx_path: str, fcmax: int) -> dict:
    """
    Parse GPX and compute all metrics. Pure function — no DB side effects.
    Returns a dict ready to pass to insert_session().
    """
    coords, elevations, hr_raw, timestamps = parse_gpx(gpx_path)
    hr_values = filter_hr_artifacts(hr_raw) if hr_raw else []

    distance_m = calculate_distance(coords)
    distance_km = round(distance_m / 1000, 2)
    duration_min = round(timestamps[-1] / 60, 1) if timestamps else 0.0
    avg_pace_sec_km = round(timestamps[-1] / (distance_m / 1000), 1) if distance_m > 0 else 0

    speed_stream = calculate_speed_stream(coords, timestamps)
    splits = calculate_splits(coords, timestamps)

    smoothed_elev = smooth_elevation(elevations, timestamps)
    elev_gain, _ = calculate_elevation_gain_loss(smoothed_elev)

    avg_hr = round(sum(hr_values) / len(hr_values)) if hr_values else None
    max_hr = max(hr_values) if hr_values else None

    zone_pcts = calculate_zones(hr_values, fcmax) if hr_values else [0.0] * 5
    rpe_estimated = estimate_rpe(zone_pcts) if hr_values else 5.0
    training_load = foster_load(rpe_estimated, duration_min)

    decoupling = None
    drift = None
    if hr_values and len(speed_stream) >= 4:
        hr_aligned = hr_values[1:] if len(hr_values) > len(speed_stream) else hr_values
        hr_aligned = hr_aligned[:len(speed_stream)]
        decoupling = aerobic_decoupling(speed_stream, hr_aligned)
        drift = cardiac_drift(timestamps[1:], hr_aligned, speed_stream)

    return {
        'date': str(date_cls.today()),
        'source': 'gpx',
        'distance_km': distance_km,
        'duration_min': duration_min,
        'avg_pace_sec_km': avg_pace_sec_km,
        'avg_hr': avg_hr,
        'max_hr': max_hr,
        'zone1_pct': zone_pcts[0], 'zone2_pct': zone_pcts[1],
        'zone3_pct': zone_pcts[2], 'zone4_pct': zone_pcts[3],
        'zone5_pct': zone_pcts[4],
        'rpe_estimated': rpe_estimated,
        'rpe_actual': None,
        'training_load': training_load,
        'decoupling_pct': decoupling,
        'cardiac_drift_bpm': drift,
        'splits_json': json.dumps(splits),
        'elevation_gain_m': elev_gain,
        'is_bulk_import': 0,
    }, hr_values


def recalculate_metrics_snapshots(db_path: str) -> None:
    """Recalculate ATL/CTL/TSB for every session date. Used after bulk import."""
    conn = get_connection(db_path)
    sessions_loads = get_all_sessions_loads(conn)
    for i, (session_date, _) in enumerate(sessions_loads):
        loads_up_to = sessions_loads[:i + 1]
        atl, ctl = calculate_atl_ctl(loads_up_to, reference_date=session_date)
        tsb = round(ctl - atl, 2)
        insert_metrics_snapshot(conn, session_date, atl, ctl, tsb)
    conn.close()


def _ask_wellness_post_run() -> dict:
    print("\n=== Bienestar post-carrera ===")
    rpe = float(input("RPE de la sesión (1-10): "))
    sleep_quality = int(input("Calidad de sueño anoche (1-5): "))
    sleep_hours = float(input("Horas de sueño: "))
    mood = int(input("Estado de ánimo (1-5): "))
    soreness = int(input("Dolor muscular (1-5): "))
    motivation = int(input("Motivación (1-5): "))
    energy = int(input("Energía (1-5): "))
    return {
        'sleep_quality': sleep_quality,
        'sleep_hours': sleep_hours,
        'mood': mood,
        'muscle_soreness': soreness,
        'motivation': motivation,
        'energy': energy,
        'session_rpe': rpe,
        'has_session': 1,
    }, rpe


def run_single_ingest(gpx_path: str, db_path: str, interactive: bool = True) -> None:
    init_db(db_path)
    conn = get_connection(db_path)
    profile = get_profile(conn)
    if not profile:
        print("ERROR: Run 'python plan.py' first to set up your profile.")
        conn.close()
        sys.exit(1)

    fcmax, confidence = get_active_fcmax(profile)
    print(f"Using FCmax: {fcmax} bpm ({confidence} confidence)")

    session_data, hr_values = process_gpx_file(gpx_path, fcmax)
    session_id = insert_session(conn, session_data)
    print(f"Session ingested: {session_data['distance_km']} km, "
          f"{session_data['duration_min']} min, load {session_data['training_load']} AU")

    # FCmax auto-update
    if hr_values:
        current_observed = profile.get('fcmax_observed')
        if should_update_fcmax_observed(hr_values, current_observed):
            new_obs = p95_hr(hr_values)
            update_fcmax_observed(conn, new_obs)
            print(f"FCmax observed updated: {current_observed} → {new_obs} bpm")

    # ATL/CTL/TSB snapshot
    sessions_loads = get_all_sessions_loads(conn)
    atl, ctl = calculate_atl_ctl(sessions_loads)
    tsb = round(ctl - atl, 2)
    insert_metrics_snapshot(conn, session_data['date'], atl, ctl, tsb)
    print(f"ATL: {atl} | CTL: {ctl} | TSB: {tsb}")
    if tsb < -30:
        print("⚠️  TSB < -30: alta carga acumulada. Considera descanso o sesión fácil.")

    if interactive:
        try:
            wellness, rpe_actual = _ask_wellness_post_run()
            update_session_rpe(conn, session_id, rpe_actual)
            insert_wellness(conn, session_data['date'], wellness)
        except (ValueError, KeyboardInterrupt):
            print("\nWellness skipped.")

    conn.close()
    subprocess.run([sys.executable, 'context.py'], check=False)


def run_folder_ingest(folder_path: str, db_path: str) -> None:
    init_db(db_path)
    gpx_files = sorted(glob.glob(os.path.join(folder_path, '*.gpx')))
    if not gpx_files:
        print(f"No GPX files found in {folder_path}")
        return

    conn = get_connection(db_path)
    profile = get_profile(conn)
    if not profile:
        print("ERROR: Run 'python plan.py' first to set up your profile.")
        conn.close()
        sys.exit(1)
    fcmax, _ = get_active_fcmax(profile)
    conn.close()

    print(f"Importing {len(gpx_files)} GPX files (no wellness prompts)...")
    for i, gpx_path in enumerate(gpx_files, 1):
        try:
            conn = get_connection(db_path)
            session_data, hr_values = process_gpx_file(gpx_path, fcmax)
            session_data['is_bulk_import'] = 1
            insert_session(conn, session_data)
            if hr_values and should_update_fcmax_observed(hr_values, profile.get('fcmax_observed')):
                new_obs = p95_hr(hr_values)
                update_fcmax_observed(conn, new_obs)
                profile['fcmax_observed'] = new_obs
            conn.close()
            print(f"  [{i}/{len(gpx_files)}] {os.path.basename(gpx_path)} — "
                  f"{session_data['distance_km']} km")
        except Exception as e:
            print(f"  [{i}/{len(gpx_files)}] SKIP {os.path.basename(gpx_path)}: {e}")

    print("Recalculating ATL/CTL/TSB for all sessions...")
    recalculate_metrics_snapshots(db_path)
    subprocess.run([sys.executable, 'context.py'], check=False)
    print("Done. Run 'claude' to chat with the agent.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest GPX files into run-intelligence')
    parser.add_argument('gpx_file', nargs='?', help='Single GPX file to ingest')
    parser.add_argument('--folder', help='Folder of GPX files for bulk import')
    parser.add_argument('--db', default=DB_PATH, help='SQLite database path')
    args = parser.parse_args()

    if args.folder:
        run_folder_ingest(args.folder, args.db)
    elif args.gpx_file:
        run_single_ingest(args.gpx_file, args.db)
    else:
        parser.print_help()
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_ingest.py -v`
Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ingest.py tests/test_ingest.py
git commit -m "feat: ingest pipeline — single GPX, bulk folder, FCmax auto-update, ATL/CTL/TSB"
```

---

> **Milestone:** Core pipeline complete. `python ingest.py --folder ./gpx_exports/` is fully functional. SQLite has real data. Verify with: `sqlite3 db/runs.db "SELECT date, distance_km, training_load FROM sessions LIMIT 5;"`

---

## Task 9: Wellness Module

**Files:**
- Create: `wellness.py`
- Create: `tests/test_wellness.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_wellness.py
import pytest
from wellness import validate_wellness, build_wellness_dict

def test_validate_wellness_valid():
    data = {
        'resting_hr': 52,
        'sleep_quality': 4,
        'sleep_hours': 7.5,
        'mood': 4,
        'muscle_soreness': 2,
        'motivation': 5,
        'energy': 4,
    }
    errors = validate_wellness(data)
    assert errors == []

def test_validate_wellness_hr_out_of_range():
    data = {'resting_hr': 250, 'sleep_quality': 3, 'sleep_hours': 7,
            'mood': 3, 'muscle_soreness': 3, 'motivation': 3, 'energy': 3}
    errors = validate_wellness(data)
    assert any('resting_hr' in e for e in errors)

def test_validate_wellness_scale_out_of_range():
    data = {'resting_hr': 55, 'sleep_quality': 6, 'sleep_hours': 7,
            'mood': 3, 'muscle_soreness': 3, 'motivation': 3, 'energy': 3}
    errors = validate_wellness(data)
    assert any('sleep_quality' in e for e in errors)

def test_build_wellness_dict_no_session():
    result = build_wellness_dict(
        resting_hr=52, sleep_quality=4, sleep_hours=7.5,
        mood=4, muscle_soreness=2, motivation=5, energy=4,
        session_rpe=None
    )
    assert result['has_session'] == 0
    assert result['session_rpe'] is None

def test_build_wellness_dict_with_session():
    result = build_wellness_dict(
        resting_hr=52, sleep_quality=4, sleep_hours=7.5,
        mood=4, muscle_soreness=2, motivation=5, energy=4,
        session_rpe=3.5
    )
    assert result['has_session'] == 1
    assert result['session_rpe'] == 3.5
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_wellness.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'wellness'`

- [ ] **Step 3: Implement wellness.py**

```python
# wellness.py
import subprocess
import sys
from datetime import date as date_cls

from db.schema import init_db, get_connection
from db.queries import insert_wellness

DB_PATH = 'db/runs.db'


def build_wellness_dict(resting_hr: int, sleep_quality: int, sleep_hours: float,
                         mood: int, muscle_soreness: int, motivation: int,
                         energy: int, session_rpe=None) -> dict:
    return {
        'resting_hr': resting_hr,
        'sleep_quality': sleep_quality,
        'sleep_hours': sleep_hours,
        'mood': mood,
        'muscle_soreness': muscle_soreness,
        'motivation': motivation,
        'energy': energy,
        'session_rpe': session_rpe,
        'has_session': 1 if session_rpe is not None else 0,
    }


def validate_wellness(data: dict) -> list[str]:
    errors = []
    hr = data.get('resting_hr', 0)
    if not (30 <= hr <= 200):
        errors.append(f"resting_hr {hr} out of range 30-200")
    for field in ['sleep_quality', 'mood', 'muscle_soreness', 'motivation', 'energy']:
        val = data.get(field, 0)
        if not (1 <= val <= 5):
            errors.append(f"{field} {val} out of range 1-5")
    rpe = data.get('session_rpe')
    if rpe is not None and not (1 <= rpe <= 10):
        errors.append(f"session_rpe {rpe} out of range 1-10")
    return errors


def _ask_question(prompt: str, cast, valid_range=None) -> any:
    while True:
        try:
            val = cast(input(prompt))
            if valid_range and val not in valid_range and not (
                isinstance(valid_range, tuple) and valid_range[0] <= val <= valid_range[1]
            ):
                print(f"  Valor inválido. Rango: {valid_range}")
                continue
            return val
        except (ValueError, KeyboardInterrupt):
            print("  Entrada inválida, intenta de nuevo.")


def run_wellness(db_path: str = DB_PATH) -> None:
    init_db(db_path)
    print("\n=== Bienestar matutino ===")
    data = build_wellness_dict(
        resting_hr=_ask_question("FC en reposo (bpm): ", int, (30, 200)),
        sleep_quality=_ask_question("Calidad de sueño 1-5: ", int, (1, 5)),
        sleep_hours=_ask_question("Horas de sueño: ", float, (0, 24)),
        mood=_ask_question("Estado de ánimo 1-5: ", int, (1, 5)),
        muscle_soreness=_ask_question("Dolor muscular 1-5: ", int, (1, 5)),
        motivation=_ask_question("Motivación 1-5: ", int, (1, 5)),
        energy=_ask_question("Energía 1-5: ", int, (1, 5)),
    )
    errors = validate_wellness(data)
    if errors:
        print("Errores de validación:", errors)
        return

    conn = get_connection(db_path)
    today = str(date_cls.today())
    insert_wellness(conn, today, data)
    conn.close()
    print(f"Wellness guardado para {today}.")

    # Check overtraining signals
    conn = get_connection(db_path)
    from db.queries import get_wellness_history
    history = get_wellness_history(conn, days=7)
    conn.close()
    _check_overtraining_signals(data, history)

    subprocess.run([sys.executable, 'context.py'], check=False)


def _check_overtraining_signals(today_data: dict, history: list) -> None:
    warnings = []
    if today_data['muscle_soreness'] >= 3:
        # Check if it's been 3+ consecutive days
        consecutive = sum(1 for h in history[:3] if h.get('muscle_soreness', 0) >= 3)
        if consecutive >= 3:
            warnings.append("⚠️  Dolor muscular ≥3/5 por 3+ días consecutivos")

    scores = ['sleep_quality', 'mood', 'motivation', 'energy']
    declining = [s for s in scores if len(history) >= 5
                 and all(history[i].get(s, 3) >= history[i+1].get(s, 3)
                         for i in range(4))]
    if len(declining) >= 2:
        warnings.append("⚠️  2+ métricas de bienestar en tendencia descendente (5 días)")

    for w in warnings:
        print(w)
    if warnings:
        print("Considera descanso adicional o consulta médica si persiste.")


if __name__ == '__main__':
    run_wellness()
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_wellness.py -v`
Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add wellness.py tests/test_wellness.py
git commit -m "feat: wellness module — daily questionnaire, validation, overtraining signals"
```

---

## Task 10: Plan Generator

**Files:**
- Create: `plan.py`
- Create: `tests/test_plan.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_plan.py
import pytest
from plan import generate_plan_sessions, get_phase, SUPPORTED_CONFIGS

def test_supported_configs_exist():
    assert ('10k', 12) in SUPPORTED_CONFIGS
    assert ('5k', 8) in SUPPORTED_CONFIGS

def test_generate_plan_10k_12w_3d_length():
    sessions = generate_plan_sessions('10k', weeks=12, days=3)
    assert len(sessions) == 36  # 12 weeks × 3 sessions

def test_generate_plan_5k_8w_3d_length():
    sessions = generate_plan_sessions('5k', weeks=8, days=3)
    assert len(sessions) == 24  # 8 weeks × 3 sessions

def test_generate_plan_weeks_numbered_1_to_n():
    sessions = generate_plan_sessions('10k', weeks=12, days=3)
    weeks = {s['week'] for s in sessions}
    assert weeks == set(range(1, 13))

def test_get_phase_10k_12w():
    assert get_phase(1, 12) == 'base'
    assert get_phase(4, 12) == 'base'
    assert get_phase(5, 12) == 'build'
    assert get_phase(8, 12) == 'build'
    assert get_phase(9, 12) == 'peak'
    assert get_phase(11, 12) == 'peak'
    assert get_phase(12, 12) == 'taper'

def test_get_phase_5k_8w():
    assert get_phase(1, 8) == 'base'
    assert get_phase(3, 8) == 'base'
    assert get_phase(4, 8) == 'build'
    assert get_phase(6, 8) == 'build'
    assert get_phase(7, 8) == 'peak'
    assert get_phase(8, 8) == 'taper'

def test_deload_weeks_have_lower_volume():
    sessions = generate_plan_sessions('10k', weeks=12, days=3)
    def week_volume(w):
        return sum(s['target_distance_km'] for s in sessions if s['week'] == w)
    # Week 4 (deload) should have less volume than week 3
    assert week_volume(4) < week_volume(3)
    # Week 8 (deload) should have less volume than week 7
    assert week_volume(8) < week_volume(7)

def test_base_phase_all_easy_or_long():
    sessions = generate_plan_sessions('10k', weeks=12, days=3)
    base = [s for s in sessions if s['week'] <= 4]
    for s in base:
        assert s['session_type'] in ('easy', 'long')

def test_build_phase_has_tempo():
    sessions = generate_plan_sessions('10k', weeks=12, days=3)
    build = [s for s in sessions if 5 <= s['week'] <= 8]
    types = {s['session_type'] for s in build}
    assert 'tempo' in types

def test_peak_phase_has_intervals():
    sessions = generate_plan_sessions('10k', weeks=12, days=3)
    peak = [s for s in sessions if 9 <= s['week'] <= 11]
    types = {s['session_type'] for s in peak}
    assert 'intervals' in types

def test_taper_volume_less_than_peak():
    sessions = generate_plan_sessions('10k', weeks=12, days=3)
    def week_volume(w):
        return sum(s['target_distance_km'] for s in sessions if s['week'] == w)
    taper_vol = week_volume(12)
    peak_vol = max(week_volume(w) for w in [9, 10, 11])
    assert taper_vol < peak_vol * 0.65  # at least 35% reduction

def test_all_sessions_have_required_fields():
    sessions = generate_plan_sessions('10k', weeks=12, days=3)
    required = ['week', 'day_of_week', 'session_type', 'target_distance_km',
                'target_duration_min', 'target_rpe_min', 'target_rpe_max', 'target_zone']
    for s in sessions:
        for field in required:
            assert field in s, f"Missing {field} in {s}"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_plan.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'plan'`

- [ ] **Step 3: Implement plan.py**

```python
# plan.py
import argparse
import sys
from datetime import date as date_cls, timedelta

from db.schema import init_db, get_connection
from db.queries import upsert_profile, insert_plan_sessions
from pipeline.fcmax import fcmax_tanaka

DB_PATH = 'db/runs.db'

SUPPORTED_CONFIGS = {
    ('10k', 12): {
        'weekly_km': [9, 11, 13, 10, 15, 17, 19, 14, 22, 24, 22, 13],
        'deload_weeks': {4, 8, 12},
    },
    ('5k', 8): {
        'weekly_km': [8, 10, 12, 9, 14, 16, 14, 10],
        'deload_weeks': {4, 8},
    },
    ('10k', 12, 4): {  # 4 days/week variant — same volumes, one extra easy
        'weekly_km': [12, 14, 16, 12, 18, 20, 22, 16, 26, 28, 26, 15],
        'deload_weeks': {4, 8, 12},
    },
}

SESSION_CONFIG = {
    'easy':      {'rpe_min': 3, 'rpe_max': 4, 'zone': 'Z1-2', 'pace_min_per_km': 8.0},
    'long':      {'rpe_min': 3, 'rpe_max': 4, 'zone': 'Z1-2', 'pace_min_per_km': 8.5},
    'tempo':     {'rpe_min': 6, 'rpe_max': 7, 'zone': 'Z3-4', 'pace_min_per_km': 6.5},
    'intervals': {'rpe_min': 7, 'rpe_max': 9, 'zone': 'Z4-5', 'pace_min_per_km': 6.0},
}

DAYS_3 = ['mon', 'wed', 'sat']
DAYS_4 = ['mon', 'tue', 'thu', 'sat']

PHASE_TYPES_3D = {
    'base':  ['easy', 'easy', 'long'],
    'build': ['easy', 'tempo', 'long'],
    'peak':  ['easy', 'intervals', 'long'],
    'taper': ['easy', 'easy', 'easy'],
}

# Fraction of weekly volume per session slot (3 days)
VOLUME_SPLIT_3D = {
    'easy':      [0.33, 0.34],  # Two easy slots
    'tempo':     [0.20],
    'intervals': [0.15],
    'long':      [0.33],
}


def get_phase(week: int, total_weeks: int) -> str:
    if total_weeks == 12:
        if week <= 4: return 'base'
        if week <= 8: return 'build'
        if week <= 11: return 'peak'
        return 'taper'
    else:  # 8 weeks
        if week <= 3: return 'base'
        if week <= 6: return 'build'
        if week == 7: return 'peak'
        return 'taper'


def generate_plan_sessions(goal: str, weeks: int, days: int) -> list[dict]:
    config_key = (goal, weeks) if days == 3 else (goal, weeks, days)
    config = SUPPORTED_CONFIGS.get(config_key) or SUPPORTED_CONFIGS.get((goal, weeks))
    if not config:
        raise ValueError(f"Unsupported config: goal={goal}, weeks={weeks}, days={days}")

    day_labels = DAYS_3 if days == 3 else DAYS_4
    sessions = []

    for week in range(1, weeks + 1):
        is_deload = week in config['deload_weeks']
        phase = get_phase(week, weeks)
        weekly_km = config['weekly_km'][week - 1]

        # In deload weeks, use easy sessions only regardless of phase
        types = ['easy', 'easy', 'long'] if is_deload else PHASE_TYPES_3D[phase]

        # Volume distribution
        type_counts = {t: types.count(t) for t in set(types)}
        km_per_type = {}
        if 'long' in types:
            km_per_type['long'] = round(weekly_km * 0.33, 1)
        if 'tempo' in types:
            km_per_type['tempo'] = round(weekly_km * 0.18, 1)
        if 'intervals' in types:
            km_per_type['intervals'] = round(weekly_km * 0.15, 1)
        easy_total = weekly_km - sum(km_per_type.values())
        km_per_type['easy'] = round(easy_total / type_counts.get('easy', 1), 1)

        type_seen = {}
        for i, (day_label, session_type) in enumerate(zip(day_labels, types)):
            cfg = SESSION_CONFIG[session_type]
            dist = km_per_type[session_type]
            duration = round(dist * cfg['pace_min_per_km'], 0)
            sessions.append({
                'week': week,
                'day_of_week': day_label,
                'session_type': session_type,
                'target_distance_km': dist,
                'target_duration_min': duration,
                'target_rpe_min': cfg['rpe_min'],
                'target_rpe_max': cfg['rpe_max'],
                'target_zone': cfg['zone'],
                'notes': f"Phase: {phase}" + (" (deload)" if is_deload else ""),
            })

    return sessions


def run_plan(goal: str, weeks: int, days: int, age: int, db_path: str) -> None:
    init_db(db_path)
    conn = get_connection(db_path)

    fcmax_est = fcmax_tanaka(age)
    upsert_profile(conn, {
        'age': age,
        'goal': goal,
        'plan_start_date': str(date_cls.today()),
        'plan_weeks': weeks,
        'days_per_week': days,
        'fcmax_estimated': fcmax_est,
    })
    print(f"Profile created: age={age}, goal={goal}, FCmax estimated={fcmax_est} bpm (Tanaka)")

    sessions = generate_plan_sessions(goal, weeks, days)
    insert_plan_sessions(conn, sessions)
    conn.close()
    print(f"Plan generated: {len(sessions)} sessions over {weeks} weeks.")
    print(f"Start: {date_cls.today()} | Race day (approx): "
          f"{date_cls.today() + timedelta(weeks=weeks)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate training plan')
    parser.add_argument('--goal', choices=['5k', '10k'], required=True)
    parser.add_argument('--weeks', type=int, choices=[8, 12], required=True)
    parser.add_argument('--days', type=int, choices=[3, 4], default=3)
    parser.add_argument('--age', type=int, required=True)
    parser.add_argument('--db', default=DB_PATH)
    args = parser.parse_args()
    run_plan(args.goal, args.weeks, args.days, args.age, args.db)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_plan.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plan.py tests/test_plan.py
git commit -m "feat: plan generator — 4-phase periodization for 5K/10K"
```

---

## Task 11: Context Builder

**Files:**
- Create: `context.py`
- Create: `tests/test_context.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_context.py
import pytest
from context import (
    get_current_week, get_phase_label, get_trends,
    detect_overtraining_signals, build_context_doc, build_session_log
)

def test_get_current_week_week1():
    from datetime import date
    start = str(date.today())
    assert get_current_week(start) == 1

def test_get_current_week_week2():
    from datetime import date, timedelta
    start = str(date.today() - timedelta(days=7))
    assert get_current_week(start) == 2

def test_get_phase_label_base():
    assert 'Base' in get_phase_label(2, 12)

def test_get_phase_label_build():
    assert 'Construcción' in get_phase_label(6, 12)

def test_get_phase_label_taper():
    assert 'Taper' in get_phase_label(12, 12)

def test_get_trends_volume_increase():
    sessions = [
        {'date': '2026-04-01', 'distance_km': 5.0},
        {'date': '2026-04-03', 'distance_km': 5.0},
        {'date': '2026-04-08', 'distance_km': 6.0},
        {'date': '2026-04-10', 'distance_km': 6.0},
    ]
    trends = get_trends(sessions)
    assert 'volume_change_pct' in trends
    assert trends['volume_change_pct'] > 0

def test_detect_overtraining_tsb_warning():
    signals = detect_overtraining_signals(tsb=-35, muscle_soreness=4, rpe_creep=False)
    assert any('TSB' in s for s in signals)

def test_detect_overtraining_soreness_warning():
    signals = detect_overtraining_signals(tsb=-5, muscle_soreness=4, rpe_creep=False)
    assert any('dolor' in s.lower() or 'soreness' in s.lower() for s in signals)

def test_build_context_doc_under_2000_tokens():
    profile = {'goal': '10k', 'plan_weeks': 12, 'days_per_week': 3,
               'fcmax_estimated': 186, 'fcmax_observed': None, 'fcmax_manual': None,
               'fcmax_confidence': 'LOW', 'plan_start_date': '2026-04-01', 'age': 32}
    last_session = {'date': '2026-04-13', 'distance_km': 5.2, 'duration_min': 32.0,
                    'avg_hr': 152, 'max_hr': 171, 'zone2_pct': 12.0, 'zone3_pct': 68.0,
                    'training_load': 224.0, 'decoupling_pct': 4.2, 'cardiac_drift_bpm': 8.0,
                    'rpe_estimated': 5.0, 'rpe_actual': None}
    metrics = {'atl': 187.0, 'ctl': 156.0, 'tsb': -31.0}
    wellness = {'sleep_quality': 4, 'muscle_soreness': 2, 'motivation': 4}
    plan_week = [{'session_type': 'easy', 'day_of_week': 'mon', 'target_distance_km': 5.0}]
    doc = build_context_doc(profile, last_session, metrics, {}, plan_week, wellness, [])
    # Rough token estimate: 1 token ≈ 4 chars
    assert len(doc) / 4 < 2000

def test_build_session_log_format():
    sessions = [
        {'date': '2026-04-13', 'distance_km': 5.2, 'duration_min': 32.0,
         'avg_hr': 152, 'max_hr': 171, 'zone2_pct': 12.0, 'training_load': 224.0,
         'decoupling_pct': 4.2},
    ]
    log = build_session_log(sessions)
    assert '2026-04-13' in log
    assert '5.2' in log
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_context.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'context'`

- [ ] **Step 3: Implement context.py**

```python
# context.py
import os
import sys
from datetime import date as date_cls, datetime, timedelta

from db.schema import init_db, get_connection
from db.queries import (
    get_profile, get_latest_session, get_latest_metrics_snapshot,
    get_sessions_for_period, get_wellness_for_date, get_plan_week,
    get_wellness_history
)
from pipeline.fcmax import get_active_fcmax

DB_PATH = 'db/runs.db'
CONTEXT_PATH = 'data/context.md'
SESSION_LOG_PATH = 'data/session_log.md'

PHASE_LABELS = {
    'base': 'Base', 'build': 'Construcción', 'peak': 'Pico', 'taper': 'Taper'
}


def get_current_week(plan_start_date: str) -> int:
    start = datetime.fromisoformat(plan_start_date).date()
    delta = (date_cls.today() - start).days
    return max(1, delta // 7 + 1)


def get_phase_label(week: int, total_weeks: int) -> str:
    from plan import get_phase
    phase = get_phase(week, total_weeks)
    label = PHASE_LABELS.get(phase, phase)
    return f"{label} (Semana {week}/{total_weeks})"


def get_trends(sessions: list) -> dict:
    """Compute trends from last 4 weeks of sessions."""
    if len(sessions) < 2:
        return {}
    mid = len(sessions) // 2
    vol_h1 = sum(s['distance_km'] for s in sessions[:mid])
    vol_h2 = sum(s['distance_km'] for s in sessions[mid:])
    change_pct = round((vol_h2 - vol_h1) / vol_h1 * 100, 1) if vol_h1 > 0 else 0

    decouplings = [s['decoupling_pct'] for s in sessions if s.get('decoupling_pct')]
    decoupling_trend = None
    if len(decouplings) >= 2:
        decoupling_trend = round(decouplings[-1] - decouplings[0], 1)

    return {
        'volume_change_pct': change_pct,
        'decoupling_trend': decoupling_trend,
    }


def detect_overtraining_signals(tsb: float, muscle_soreness: int, rpe_creep: bool) -> list[str]:
    signals = []
    if tsb < -30:
        signals.append(f"TSB {tsb}: carga alta — considera descanso o sesión fácil")
    if muscle_soreness >= 3:
        signals.append(f"Dolor muscular {muscle_soreness}/5 — posible fatiga acumulada")
    if rpe_creep:
        signals.append("RPE creep detectado — carreras fáciles cuestan más de lo esperado")
    return signals


def build_context_doc(profile: dict, last_session: dict, metrics: dict,
                       trends: dict, plan_week: list, wellness: dict,
                       active_signals: list) -> str:
    fcmax, confidence = get_active_fcmax(profile)
    today = str(date_cls.today())

    phase = get_phase_label(
        get_current_week(profile.get('plan_start_date', today)),
        profile.get('plan_weeks', 12)
    ) if profile.get('plan_start_date') else 'Sin plan activo'

    lines = [
        f"# Estado actual — {today}",
        "",
        "## Perfil",
        f"- Objetivo: {profile['goal'].upper()} | Plan: {profile.get('plan_weeks', '?')} semanas | Fase: {phase}",
        f"- FCmax: {fcmax} lpm ({confidence} confidence) | Días/semana: {profile.get('days_per_week', '?')}",
        "",
    ]

    if last_session:
        dominant_zone = max(
            [(f"zone{i}_pct", last_session.get(f"zone{i}_pct", 0)) for i in range(1, 6)],
            key=lambda x: x[1]
        )
        zone_num = dominant_zone[0][4]
        hr_pct = round(last_session['avg_hr'] / fcmax * 100) if last_session.get('avg_hr') else '?'
        pace_sec = last_session.get('avg_pace_sec_km', 0)
        pace_str = f"{int(pace_sec//60)}:{int(pace_sec%60):02d}/km" if pace_sec else '?'
        decoupling = last_session.get('decoupling_pct')
        drift = last_session.get('cardiac_drift_bpm')
        load = last_session.get('training_load', '?')

        lines += [
            f"## Sesión más reciente — {last_session['date']}",
            f"- Distancia: {last_session.get('distance_km', '?')} km | "
            f"Duración: {last_session.get('duration_min', '?')} min | Ritmo: {pace_str}",
            f"- HR: {last_session.get('avg_hr', '?')} prom / {last_session.get('max_hr', '?')} máx "
            f"→ {hr_pct}% FCmax → Zona {zone_num} predominante",
            f"- Carga Foster: {load} AU | "
            f"Decoupling: {decoupling}%" + (" ✓" if decoupling and decoupling < 5 else " ⚠️" if decoupling else "") +
            f" | Drift: {drift} bpm/h" if drift else "",
            "",
        ]

    if metrics:
        tsb = metrics.get('tsb', 0)
        tsb_label = "✓ fresxo" if tsb > 10 else "⚠️ carga alta" if tsb < -10 else "normal"
        lines += [
            "## Estado de fatiga",
            f"- ATL: {metrics.get('atl', '?')} | CTL: {metrics.get('ctl', '?')} | TSB: {tsb} ({tsb_label})",
        ]
        if wellness:
            lines.append(
                f"- Wellness: sueño {wellness.get('sleep_quality', '?')}/5 | "
                f"dolor {wellness.get('muscle_soreness', '?')}/5 | "
                f"motivación {wellness.get('motivation', '?')}/5"
            )
        lines.append("")

    if trends:
        vol_chg = trends.get('volume_change_pct', 0)
        vol_arrow = '↑' if vol_chg > 0 else '↓'
        vol_warn = ' ⚠️ (>30%)' if abs(vol_chg) > 30 else ' ✓'
        decoup_trend = trends.get('decoupling_trend')
        lines += [
            "## Tendencias 4 semanas",
            f"- Volumen: {vol_arrow} {abs(vol_chg)}% vs 2 semanas previas{vol_warn}",
        ]
        if decoup_trend is not None:
            direction = "mejorando" if decoup_trend < 0 else "empeorando"
            lines.append(f"- Decoupling: {direction} ({decoup_trend:+.1f}%)")
        lines.append("")

    if plan_week:
        lines.append("## Plan semana actual")
        for s in plan_week:
            lines.append(
                f"- ⬜ {s['day_of_week'].capitalize()}: "
                f"{s['session_type'].capitalize()} {s['target_distance_km']} km "
                f"({s['target_zone']}, RPE {s.get('target_rpe_min')}-{s.get('target_rpe_max')})"
            )
        lines.append("")

    if active_signals:
        lines.append("## Señales activas")
        for sig in active_signals:
            lines.append(f"- {sig}")
        lines.append("")

    return '\n'.join(lines)


def build_session_log(sessions: list) -> str:
    header = "fecha      | km   | min  | avg_hr | z2%  | load  | decoup"
    separator = "-" * len(header)
    rows = [header, separator]
    for s in sorted(sessions, key=lambda x: x['date'], reverse=True):
        rows.append(
            f"{s['date']} | {s.get('distance_km', '?'):<4} | "
            f"{s.get('duration_min', '?'):<4} | "
            f"{s.get('avg_hr', '?'):<6} | "
            f"{s.get('zone2_pct', '?'):<4} | "
            f"{s.get('training_load', '?'):<5} | "
            f"{s.get('decoupling_pct', '?')}"
        )
    return '\n'.join(rows)


def run_context(db_path: str = DB_PATH) -> None:
    os.makedirs('data', exist_ok=True)
    init_db(db_path)
    conn = get_connection(db_path)

    profile = get_profile(conn)
    if not profile:
        print("No profile found. Run 'python plan.py' first.")
        conn.close()
        return

    last_session = get_latest_session(conn)
    metrics = get_latest_metrics_snapshot(conn)
    today = str(date_cls.today())
    wellness = get_wellness_for_date(conn, today)

    # 4-week sessions for trends
    four_weeks_ago = str(date_cls.today() - timedelta(weeks=4))
    recent_sessions = get_sessions_for_period(conn, four_weeks_ago, today)
    trends = get_trends(recent_sessions)

    # Current plan week
    plan_week = []
    if profile.get('plan_start_date') and profile.get('plan_weeks'):
        current_week = get_current_week(profile['plan_start_date'])
        if current_week <= profile['plan_weeks']:
            plan_week = get_plan_week(conn, current_week)

    # Overtraining signals
    tsb = metrics['tsb'] if metrics else 0
    soreness = wellness.get('muscle_soreness', 0) if wellness else 0
    signals = detect_overtraining_signals(tsb, soreness, rpe_creep=False)

    # 12-week session log
    twelve_weeks_ago = str(date_cls.today() - timedelta(weeks=12))
    all_recent = get_sessions_for_period(conn, twelve_weeks_ago, today)
    conn.close()

    context_doc = build_context_doc(profile, last_session, metrics, trends,
                                     plan_week, wellness, signals)
    with open(CONTEXT_PATH, 'w') as f:
        f.write(context_doc)

    session_log = build_session_log(all_recent)
    with open(SESSION_LOG_PATH, 'w') as f:
        f.write(session_log)

    print(f"Context updated: {CONTEXT_PATH} ({len(context_doc)} chars)")


if __name__ == '__main__':
    run_context()
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_context.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add context.py tests/test_context.py
git commit -m "feat: context builder — dynamic context.md + session_log.md for agent"
```

---

## Task 12: CLAUDE.md — Agent System Prompt

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Write CLAUDE.md**

```markdown
# Run Intelligence — Agente de Coaching

Sos un coach de running para principiantes basado en evidencia científica.
Tu usuario tiene como objetivo completar su primera carrera de 5K o 10K.

Lee el archivo `data/context.md` al inicio de cada conversación para obtener el
estado actual del corredor. Para preguntas sobre sesiones específicas, lee
`data/session_log.md`.

---

## Principios que gobiernan toda prescripción

**SAID (Specificity):** La progresión está limitada por el tejido conectivo
(tendones necesitan ~10 días para procesar cada incremento de carga), no por la
sensación cardiovascular. "Sentirse capaz de correr más" ≠ "tendones y huesos listos".

**SRA (Ciclo Estímulo-Recuperación-Adaptación):** Regla hard-easy obligatoria —
siempre intercalar al menos un día fácil o descanso tras sesión intensa.
Máximo 2 sesiones duras por semana. Descarga automática cada 3-4 semanas (30% menos volumen).

**SFR (Stimulus-to-Fatigue Ratio):** Priorizar sesiones Zona 1-2 (SFR alto —
gran estímulo aeróbico, fatiga mínima). Evitar Zona 3 (el peor SFR posible:
demasiado dura para recuperarse fácil, demasiado suave para adaptaciones de alta intensidad).
Distribución 80/20: 80% volumen semanal en Zona 1-2, 20% en Zona 4-5.

**Fitness-Fatiga (Banister/Zatsiorsky):**
- TSB > +10: fresxo, apto para sesión de calidad
- TSB -10 a +10: zona de entrenamiento normal
- TSB < -10: fatiga acumulada, priorizar sesiones fáciles
- TSB < -30: señal roja — convertir cualquier sesión de calidad en fácil o descanso

Taper pre-carrera: reducir volumen 40-50% durante 7-10 días, mantener intensidad,
mantener frecuencia de carrera.

**Efectos residuales (Issurin):**
- Resistencia aeróbica persiste 30±5 días sin entrenamiento específico.
- Velocidad máxima: solo 5±3 días. Mantenerla requiere estímulo cada 3-5 días.
- Una semana sin correr no destruye la base aeróbica. No entrar en pánico.

---

## Reglas de prescripción (no negociables)

1. **Siempre mostrar DELTA** entre lo que el plan fijo indica y lo que prescribís hoy.
   Formato: `Plan decía: X | Prescripción: Y | Razón: Z`

2. **Nunca incrementar** distancia + frecuencia + intensidad simultáneamente.
   Solo una variable a la vez, en este orden: duración → frecuencia → intensidad.

3. **Si TSB < -30 o señal roja en wellness**: convertir sesión de calidad en
   fácil o recomendar descanso. No negociar esto.

4. **Alertar si** el volumen semanal proyectado supera 30% de la semana anterior.

5. **Nunca prescribir test de FCmax** hasta que el historial muestre al menos
   4-6 semanas de base aeróbica consistente.

6. **Máximo 2 sesiones de calidad por semana** (tempo, intervalos, carrera larga
   cuenta como calidad por volumen).

---

## Zonas de HR (referencia rápida)

| Zona | % FCmax | RPE (CR-10) | Descripción |
|------|---------|-------------|-------------|
| Z1 | <60% | 1-2 | Recuperación activa |
| Z2 | 60-72% | 2-4 | Base aeróbica (objetivo principal) |
| Z3 | 72-82% | 4-6 | Zona gris — minimizar |
| Z4 | 82-90% | 6-8 | Umbral de lactato |
| Z5 | >90% | 8-10 | VO₂max |

Test del habla: hablar cómodamente = Z1-2 | con dificultad = Z3 | no poder = Z4-5.

---

## Señales rojas de sobreentrenamiento

Si el corredor reporta alguna combinación de:
- FC en reposo >7-10 lpm sobre su baseline por 3+ días
- Calidad de sueño ≤2/5 de forma consistente
- RPE de carreras fáciles subiendo a 6+/10
- Dolor muscular ≥3/5 por 3+ días consecutivos
- 2+ métricas de bienestar en tendencia descendente por 5+ días

→ Recomendar descanso obligatorio de 2-3 días y reevaluar. Si persiste, consulta médica.
```

- [ ] **Step 2: Verify CLAUDE.md loads correctly**

Run: `claude --print "¿Qué archivo de contexto debés leer primero?" 2>/dev/null | head -5`
Expected: Claude mentions `data/context.md`.

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/ -v`
Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "feat: CLAUDE.md agent system prompt — coaching rules and scientific principles"
```

---

## Self-Review Checklist

After writing this plan, checking spec coverage:

- [x] DB schema (5 tables) → Task 2
- [x] FCmax priority chain + Tanaka + p95 → Task 3
- [x] GPX parsing + HR artifact filtering → Task 4
- [x] Metrics Layer A (haversine, splits, elevation) → Task 5
- [x] Metrics Layer B (zones, RPE, Foster, decoupling, drift) → Task 6
- [x] Metrics Layer C (ATL, CTL, TSB) → Task 7
- [x] Single GPX ingest + FCmax auto-update → Task 8
- [x] Bulk folder import + recalculate snapshots → Task 8
- [x] Post-ingest wellness questionnaire → Task 8 (`_ask_wellness_post_run`)
- [x] Daily wellness command → Task 9
- [x] Overtraining signal detection → Task 9 (`_check_overtraining_signals`)
- [x] Plan generation (4 phases, deload weeks, 5K/10K) → Task 10
- [x] Static plan as immutable reference → Task 10 (never modified after generation)
- [x] Context document < 2000 tokens → Task 11 (tested)
- [x] session_log.md → Task 11
- [x] CLAUDE.md with scientific principles + DELTA rule → Task 12
- [x] context.py auto-triggered by ingest + wellness → Tasks 8, 9 (subprocess call)
