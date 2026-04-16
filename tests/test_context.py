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
                    'rpe_estimated': 5.0, 'rpe_actual': None, 'avg_pace_sec_km': 369}
    metrics = {'atl': 187.0, 'ctl': 156.0, 'tsb': -31.0}
    wellness = {'sleep_quality': 4, 'muscle_soreness': 2, 'motivation': 4}
    plan_week = [{'session_type': 'easy', 'day_of_week': 'mon', 'target_distance_km': 5.0,
                  'target_zone': 'Z1-2', 'target_rpe_min': 3, 'target_rpe_max': 4}]
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
