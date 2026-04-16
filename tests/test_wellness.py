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
