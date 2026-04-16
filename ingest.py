# ingest.py
import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import date as date_cls

from db.schema import init_db, get_connection
from db.queries import (
    get_profile, upsert_profile, insert_session, update_session_rpe,
    insert_wellness, get_all_sessions_loads, insert_metrics_snapshot,
    update_fcmax_observed
)
from pipeline.gpx_parser import parse_gpx, filter_hr_artifacts
from pipeline.fcmax import (
    fcmax_tanaka, get_active_fcmax, should_update_fcmax_observed, p95_hr
)
from pipeline.metrics import (
    calculate_distance, calculate_speed_stream, calculate_splits,
    smooth_elevation, calculate_elevation_gain_loss,
    calculate_zones, estimate_rpe, foster_load,
    aerobic_decoupling, cardiac_drift, calculate_atl_ctl
)

DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'runs.db')


def process_gpx_file(gpx_path: str, fcmax: int) -> tuple[dict, list]:
    """
    Parse GPX and compute all metrics. Pure function — no DB side effects.
    Returns (session_dict, hr_values).
    """
    coords, elevations, hr_raw, timestamps = parse_gpx(gpx_path)
    hr_values = filter_hr_artifacts(hr_raw) if hr_raw else []

    distance_m = calculate_distance(coords)
    distance_km = round(distance_m / 1000, 2)
    duration_min = round(timestamps[-1] / 60, 1) if timestamps else 0.0
    avg_pace_sec_km = round(timestamps[-1] / (distance_m / 1000), 1) if distance_m > 0 else 0

    speed_stream = calculate_speed_stream(coords, timestamps)
    splits = calculate_splits(coords, timestamps)

    smoothed_elev = smooth_elevation(elevations, timestamps)
    elev_gain, _ = calculate_elevation_gain_loss(smoothed_elev)

    avg_hr = round(sum(hr_values) / len(hr_values)) if hr_values else None
    max_hr = max(hr_values) if hr_values else None

    zone_pcts = calculate_zones(hr_values, fcmax) if hr_values else [0.0] * 5
    rpe_estimated = estimate_rpe(zone_pcts) if hr_values else 5.0
    training_load = foster_load(rpe_estimated, duration_min)

    decoupling = None
    drift = None
    if hr_values and len(speed_stream) >= 4:
        hr_aligned = hr_values[1:] if len(hr_values) > len(speed_stream) else hr_values
        hr_aligned = hr_aligned[:len(speed_stream)]
        decoupling = aerobic_decoupling(speed_stream, hr_aligned)
        drift = cardiac_drift(timestamps[1:], hr_aligned, speed_stream)

    return {
        'date': str(date_cls.today()),
        'source': 'gpx',
        'distance_km': distance_km,
        'duration_min': duration_min,
        'avg_pace_sec_km': avg_pace_sec_km,
        'avg_hr': avg_hr,
        'max_hr': max_hr,
        'zone1_pct': zone_pcts[0], 'zone2_pct': zone_pcts[1],
        'zone3_pct': zone_pcts[2], 'zone4_pct': zone_pcts[3],
        'zone5_pct': zone_pcts[4],
        'rpe_estimated': rpe_estimated,
        'rpe_actual': None,
        'training_load': training_load,
        'decoupling_pct': decoupling,
        'cardiac_drift_bpm': drift,
        'splits_json': json.dumps(splits),
        'elevation_gain_m': elev_gain,
        'is_bulk_import': 0,
    }, hr_values


def recalculate_metrics_snapshots(db_path: str) -> None:
    """Recalculate ATL/CTL/TSB for every session date. Used after bulk import."""
    conn = get_connection(db_path)
    sessions_loads = get_all_sessions_loads(conn)
    for i, (session_date, _) in enumerate(sessions_loads):
        loads_up_to = sessions_loads[:i + 1]
        atl, ctl = calculate_atl_ctl(loads_up_to, reference_date=session_date)
        tsb = round(ctl - atl, 2)
        insert_metrics_snapshot(conn, session_date, atl, ctl, tsb)
    conn.close()


def _ask_wellness_post_run() -> tuple[dict, float]:
    print("\n=== Bienestar post-carrera ===")
    rpe = float(input("RPE de la sesión (1-10): "))
    sleep_quality = int(input("Calidad de sueño anoche (1-5): "))
    sleep_hours = float(input("Horas de sueño: "))
    mood = int(input("Estado de ánimo (1-5): "))
    soreness = int(input("Dolor muscular (1-5): "))
    motivation = int(input("Motivación (1-5): "))
    energy = int(input("Energía (1-5): "))
    return {
        'sleep_quality': sleep_quality,
        'sleep_hours': sleep_hours,
        'mood': mood,
        'muscle_soreness': soreness,
        'motivation': motivation,
        'energy': energy,
        'session_rpe': rpe,
        'has_session': 1,
    }, rpe


def run_single_ingest(gpx_path: str, db_path: str, interactive: bool = True) -> None:
    init_db(db_path)
    conn = get_connection(db_path)
    profile = get_profile(conn)
    if not profile:
        print("ERROR: Run 'python plan.py' first to set up your profile.")
        conn.close()
        sys.exit(1)

    fcmax, confidence = get_active_fcmax(profile)
    print(f"Using FCmax: {fcmax} bpm ({confidence} confidence)")

    session_data, hr_values = process_gpx_file(gpx_path, fcmax)
    session_id = insert_session(conn, session_data)
    print(f"Session ingested: {session_data['distance_km']} km, "
          f"{session_data['duration_min']} min, load {session_data['training_load']} AU")

    # FCmax auto-update
    if hr_values:
        current_observed = profile.get('fcmax_observed')
        if should_update_fcmax_observed(hr_values, current_observed):
            new_obs = p95_hr(hr_values)
            update_fcmax_observed(conn, new_obs)
            print(f"FCmax observed updated: {current_observed} -> {new_obs} bpm")

    # ATL/CTL/TSB snapshot
    sessions_loads = get_all_sessions_loads(conn)
    atl, ctl = calculate_atl_ctl(sessions_loads)
    tsb = round(ctl - atl, 2)
    insert_metrics_snapshot(conn, session_data['date'], atl, ctl, tsb)
    print(f"ATL: {atl} | CTL: {ctl} | TSB: {tsb}")
    if tsb < -30:
        print("WARNING: TSB < -30: alta carga acumulada. Considera descanso o sesion facil.")

    if interactive:
        try:
            wellness, rpe_actual = _ask_wellness_post_run()
            update_session_rpe(conn, session_id, rpe_actual)
            insert_wellness(conn, session_data['date'], wellness)
        except (ValueError, KeyboardInterrupt):
            print("\nWellness skipped.")

    conn.close()
    subprocess.run([sys.executable, 'context.py'], check=False)


def run_folder_ingest(folder_path: str, db_path: str) -> None:
    init_db(db_path)
    gpx_files = sorted(glob.glob(os.path.join(folder_path, '*.gpx')))
    if not gpx_files:
        print(f"No GPX files found in {folder_path}")
        return

    conn = get_connection(db_path)
    profile = get_profile(conn)
    if not profile:
        print("ERROR: Run 'python plan.py' first to set up your profile.")
        conn.close()
        sys.exit(1)
    fcmax, _ = get_active_fcmax(profile)
    conn.close()

    print(f"Importing {len(gpx_files)} GPX files (no wellness prompts)...")
    for i, gpx_path in enumerate(gpx_files, 1):
        try:
            conn = get_connection(db_path)
            session_data, hr_values = process_gpx_file(gpx_path, fcmax)
            session_data['is_bulk_import'] = 1
            insert_session(conn, session_data)
            if hr_values and should_update_fcmax_observed(hr_values, profile.get('fcmax_observed')):
                new_obs = p95_hr(hr_values)
                update_fcmax_observed(conn, new_obs)
                profile['fcmax_observed'] = new_obs
            conn.close()
            print(f"  [{i}/{len(gpx_files)}] {os.path.basename(gpx_path)} — "
                  f"{session_data['distance_km']} km")
        except Exception as e:
            print(f"  [{i}/{len(gpx_files)}] SKIP {os.path.basename(gpx_path)}: {e}")

    print("Recalculating ATL/CTL/TSB for all sessions...")
    recalculate_metrics_snapshots(db_path)
    subprocess.run([sys.executable, 'context.py'], check=False)
    print("Done. Run 'claude' to chat with the agent.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest GPX files into run-intelligence')
    parser.add_argument('gpx_file', nargs='?', help='Single GPX file to ingest')
    parser.add_argument('--folder', help='Folder of GPX files for bulk import')
    parser.add_argument('--db', default=DB_PATH, help='SQLite database path')
    args = parser.parse_args()

    if args.folder:
        run_folder_ingest(args.folder, args.db)
    elif args.gpx_file:
        run_single_ingest(args.gpx_file, args.db)
    else:
        parser.print_help()
