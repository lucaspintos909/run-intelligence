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
