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
    session, hr_values = process_gpx_file(gpx_file, fcmax=186)
    assert 'distance_km' in session
    assert 'duration_min' in session
    assert 'avg_hr' in session
    assert 'rpe_estimated' in session
    assert 'training_load' in session
    assert session['distance_km'] > 0

def test_process_gpx_file_distance_approx_2km(db_path, gpx_file):
    session, _ = process_gpx_file(gpx_file, fcmax=186)
    assert 1.8 < session['distance_km'] < 2.2

def test_process_gpx_file_zone_pcts_sum_to_100(gpx_file):
    session, _ = process_gpx_file(gpx_file, fcmax=186)
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
