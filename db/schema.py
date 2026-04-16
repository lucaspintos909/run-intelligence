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
