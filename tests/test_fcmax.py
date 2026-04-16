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
