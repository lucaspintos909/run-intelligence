#!/usr/bin/env python3
"""CLI utility to parse .fit files and compute standard metrics.

Usage:
    poetry run python scripts/parse_fit.py fit-examples/
    poetry run python scripts/parse_fit.py fit-examples/477376944541827275.fit --json
    poetry run python scripts/parse_fit.py --help

Outputs a human-readable summary by default, or JSON with --json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from run_intelligence.pipeline.fit_parser import FitParseError, parse_fit_file
from run_intelligence.pipeline.metrics import (
    MetricCalculationError,
    calculate_standard_metrics,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse Coros .fit files and compute standard running metrics."
    )
    parser.add_argument(
        "path",
        help="Path to a .fit file or directory containing .fit files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of human-readable text",
    )
    return parser.parse_args()


def _collect_fit_files(path: Path) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() != ".fit":
            raise ValueError(f"Expected a .fit file, got: {path}")
        return [path]
    if path.is_dir():
        files = sorted(path.glob("*.fit"))
        if not files:
            raise ValueError(f"No .fit files found in directory: {path}")
        return files
    raise ValueError(f"Path does not exist: {path}")


def _process_file(fit_path: Path) -> dict | None:
    result: dict = {"file": fit_path.name, "status": "ok"}

    try:
        raw = parse_fit_file(str(fit_path))
    except FitParseError as e:
        result["status"] = "parse_error"
        result["error"] = str(e)
        return result

    result["raw"] = {
        "timestamp": raw.timestamp.isoformat(),
        "duration_seconds": raw.duration_seconds,
        "distance_meters": raw.distance_meters,
        "pace_sec_per_km": raw.pace_sec_per_km,
        "hr_avg_bpm": raw.hr_avg_bpm,
        "hr_max_bpm": raw.hr_max_bpm,
        "hr_min_bpm": raw.hr_min_bpm,
        "cadence_avg_rpm": raw.cadence_avg_rpm,
        "cadence_max_rpm": raw.cadence_max_rpm,
        "gps_points": len(raw.gps_lat) if raw.gps_lat else 0,
        "elevation_points": len(raw.gps_elevation) if raw.gps_elevation else 0,
    }

    try:
        metrics = calculate_standard_metrics(raw)
    except MetricCalculationError as e:
        result["status"] = "metrics_error"
        result["error"] = str(e)
        return result

    result["metrics"] = json.loads(metrics.to_json())
    return result


def _print_human(results: list[dict]) -> None:
    for res in results:
        print(f"=== {res['file']} ===")

        if res["status"] != "ok":
            print(f"  ERROR [{res['status']}]: {res.get('error', 'unknown')}\n")
            continue

        raw = res["raw"]
        print(f"  Timestamp:        {raw['timestamp']}")
        print(f"  Duration:         {raw['duration_seconds']:.1f}s")
        print(f"  Distance:         {raw['distance_meters']:.1f}m")
        print(f"  Pace (sec/km):    {raw['pace_sec_per_km']}")
        print(
            f"  HR avg/max/min:   {raw['hr_avg_bpm']} / "
            f"{raw['hr_max_bpm']} / {raw['hr_min_bpm']}"
        )
        print(
            f"  Cadence avg/max:  {raw['cadence_avg_rpm']} / "
            f"{raw['cadence_max_rpm']}"
        )
        print(f"  GPS points:       {raw['gps_points']}")
        print(f"  Elevation points: {raw['elevation_points']}")

        metrics = res["metrics"]
        print("  --- StandardMetrics ---")
        print(f"  Pace avg:         {metrics.get('pace_avg_min_per_km')} min/km")
        print(f"  HR zones:         {metrics.get('hr_zone_distribution')}")
        print(f"  Cadence avg/max:  {metrics.get('cadence_avg_rpm')} / {metrics.get('cadence_max_rpm')}")
        print(f"  Elevation gain:   {metrics.get('elevation_gain_m')}m")
        print(f"  Elevation loss:   {metrics.get('elevation_loss_m')}m")
        print()


def main() -> int:
    args = _parse_args()
    target = Path(args.path)

    try:
        fit_files = _collect_fit_files(target)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    results = []
    for fit_path in fit_files:
        result = _process_file(fit_path)
        if result:
            results.append(result)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        _print_human(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
