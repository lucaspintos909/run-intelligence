import gpxpy
import gpxpy.gpx
from datetime import timezone


def parse_gpx(path: str) -> tuple[list, list, list, list]:
    """
    Parse GPX file into four synchronized streams.
    Returns:
        coords:     [(lat, lon), ...]
        elevations: [float, ...]  in meters
        hr_values:  [int, ...]    bpm, empty list if no HR data
        timestamps: [int, ...]    seconds from first point
    """
    with open(path, 'r') as f:
        gpx = gpxpy.parse(f)

    coords, elevations, hr_raw, times_abs = [], [], [], []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                coords.append((point.latitude, point.longitude))
                elevations.append(point.elevation or 0.0)
                times_abs.append(point.time.replace(tzinfo=timezone.utc).timestamp()
                                  if point.time else 0)
                # HR is stored in Garmin TrackPointExtension
                hr = None
                if point.extensions:
                    for ext in point.extensions:
                        for child in ext:
                            if 'hr' in child.tag.lower():
                                try:
                                    hr = int(child.text)
                                except (ValueError, TypeError):
                                    pass
                hr_raw.append(hr)

    if not times_abs:
        return [], [], [], []

    t0 = times_abs[0]
    timestamps = [int(t - t0) for t in times_abs]

    # Return empty list if no HR data at all
    has_hr = any(h is not None for h in hr_raw)
    hr_values = [h if h is not None else 0 for h in hr_raw] if has_hr else []

    return coords, elevations, hr_values, timestamps


def filter_hr_artifacts(hr_values: list[int],
                         max_bpm: int = 220,
                         max_change_per_sec: int = 30) -> list[int]:
    """
    Remove physiologically impossible HR values.
    - Discard any value > max_bpm
    - Discard values where change from previous > max_change_per_sec
    """
    if not hr_values:
        return []

    filtered = [hr_values[0]] if hr_values[0] <= max_bpm else []

    for i in range(1, len(hr_values)):
        hr = hr_values[i]
        if hr > max_bpm:
            continue
        if filtered and abs(hr - filtered[-1]) > max_change_per_sec:
            continue
        filtered.append(hr)

    return filtered
