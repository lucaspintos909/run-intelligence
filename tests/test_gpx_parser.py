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
