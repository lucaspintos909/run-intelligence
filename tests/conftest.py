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
