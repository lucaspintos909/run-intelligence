# pipeline/metrics.py
import math
from typing import Optional
import numpy as np


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


# ─── Layer B: Physiological metrics ──────────────────────────────────────────

ZONE_BOUNDS = [
    (0.00, 0.60),   # Z1: < 60% FCmax
    (0.60, 0.72),   # Z2: 60–72%
    (0.72, 0.82),   # Z3: 72–82%
    (0.82, 0.90),   # Z4: 82–90%
    (0.90, 1.01),   # Z5: > 90%
]

ZONE_RPE_MIDPOINTS = {1: 1.5, 2: 3.0, 3: 5.0, 4: 7.0, 5: 9.0}


def calculate_zones(hr_values: list[int], fcmax: int) -> list[float]:
    """Returns [z1_pct, z2_pct, z3_pct, z4_pct, z5_pct]."""
    if not hr_values:
        return [0.0] * 5
    total = len(hr_values)
    result = []
    for low, high in ZONE_BOUNDS:
        count = sum(1 for hr in hr_values if low * fcmax <= hr < high * fcmax)
        result.append(round(count / total * 100, 1))
    return result


def estimate_rpe(zone_pcts: list[float]) -> float:
    """RPE estimate from dominant HR zone. Uses zone midpoint RPE values."""
    dominant_zone = zone_pcts.index(max(zone_pcts)) + 1
    return ZONE_RPE_MIDPOINTS[dominant_zone]


def foster_load(rpe: float, duration_min: float) -> float:
    """Foster Session RPE load: RPE (CR-10) × duration in minutes."""
    return round(rpe * duration_min, 1)


def aerobic_decoupling(speed_values: list[float], hr_values: list[float]) -> float:
    """
    Friel aerobic decoupling: efficiency factor degradation from H1 to H2.
    EF = avg_speed / avg_hr. Positive = efficiency dropped. < 5% = good.
    """
    if len(speed_values) < 4:
        return 0.0
    mid = len(speed_values) // 2
    ef_h1 = (sum(speed_values[:mid]) / mid) / (sum(hr_values[:mid]) / mid)
    ef_h2 = (sum(speed_values[mid:]) / (len(speed_values) - mid)) / \
            (sum(hr_values[mid:]) / (len(hr_values) - mid))
    return round((ef_h1 - ef_h2) / ef_h1 * 100, 2)


def cardiac_drift(times_sec: list[int], hr_values: list[float],
                   speed_values: list[float],
                   speed_tolerance: float = 0.05,
                   min_points: int = 10) -> Optional[float]:
    """
    HR linear trend at constant pace (±speed_tolerance of mean speed).
    Returns bpm/hour. Positive = HR drifting up. None if insufficient stable data.
    """
    if not speed_values:
        return None
    mean_speed = sum(speed_values) / len(speed_values)
    low = mean_speed * (1 - speed_tolerance)
    high = mean_speed * (1 + speed_tolerance)

    stable = [(t, h) for t, s, h in zip(times_sec, speed_values, hr_values)
              if low <= s <= high]

    if len(stable) < min_points:
        return None

    t_arr = np.array([p[0] for p in stable], dtype=float)
    h_arr = np.array([p[1] for p in stable], dtype=float)
    slope = np.polyfit(t_arr, h_arr, 1)[0]  # bpm/second
    return round(float(slope) * 3600, 2)     # convert to bpm/hour
