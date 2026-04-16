# pipeline/metrics.py
import math
from typing import Optional


# ─── Layer A: Basic session metrics ──────────────────────────────────────────

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in meters between two GPS coordinates."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def calculate_distance(coords: list[tuple]) -> float:
    """Total distance in meters."""
    return sum(haversine(*coords[i-1], *coords[i]) for i in range(1, len(coords)))


def calculate_speed_stream(coords: list[tuple], timestamps: list[int]) -> list[float]:
    """Speed in m/s between consecutive GPS points."""
    speeds = []
    for i in range(1, len(coords)):
        dist = haversine(*coords[i-1], *coords[i])
        dt = timestamps[i] - timestamps[i-1]
        speeds.append(dist / dt if dt > 0 else 0.0)
    return speeds


def calculate_splits(coords: list[tuple], timestamps: list[int]) -> list[int]:
    """
    Pace in seconds/km for each complete kilometer.
    Returns list of sec/km values.
    """
    splits = []
    km_start_time = timestamps[0]
    km_start_dist = 0.0
    cumulative_dist = 0.0
    km_count = 0

    for i in range(1, len(coords)):
        seg_dist = haversine(*coords[i-1], *coords[i])
        cumulative_dist += seg_dist

        while cumulative_dist >= (km_count + 1) * 1000:
            km_count += 1
            # Interpolate time at exactly km boundary
            overshoot = cumulative_dist - km_count * 1000
            seg_time = timestamps[i] - timestamps[i-1]
            fraction = 1 - (overshoot / seg_dist) if seg_dist > 0 else 1
            km_end_time = timestamps[i-1] + seg_time * fraction
            splits.append(round(km_end_time - km_start_time))
            km_start_time = km_end_time

    return splits


def smooth_elevation(elevations: list[float],
                      timestamps: list[int],
                      window_sec: int = 30) -> list[float]:
    """Moving average over a time window to remove GPS noise."""
    smoothed = []
    for i, t in enumerate(timestamps):
        window = [
            elevations[j]
            for j, ts in enumerate(timestamps)
            if abs(ts - t) <= window_sec // 2
        ]
        smoothed.append(sum(window) / len(window))
    return smoothed


def calculate_elevation_gain_loss(elevations: list[float]) -> tuple[float, float]:
    """Total elevation gain and loss in meters."""
    gain, loss = 0.0, 0.0
    for i in range(1, len(elevations)):
        delta = elevations[i] - elevations[i-1]
        if delta > 0:
            gain += delta
        else:
            loss += abs(delta)
    return round(gain, 1), round(loss, 1)
