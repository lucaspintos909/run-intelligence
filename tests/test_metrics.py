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


# ─── Layer B tests ───────────────────────────────────────────────────────────
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
