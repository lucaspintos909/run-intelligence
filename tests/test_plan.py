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
