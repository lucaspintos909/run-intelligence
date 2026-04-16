import argparse
import sys
from datetime import date as date_cls, timedelta

from db.schema import init_db, get_connection
from db.queries import upsert_profile, insert_plan_sessions
from pipeline.fcmax import fcmax_tanaka

DB_PATH = 'db/runs.db'

SUPPORTED_CONFIGS = {
    ('10k', 12): {
        'weekly_km': [9, 11, 13, 10, 15, 17, 19, 14, 22, 24, 22, 13],
        'deload_weeks': {4, 8, 12},
    },
    ('5k', 8): {
        'weekly_km': [8, 10, 12, 9, 14, 16, 14, 10],
        'deload_weeks': {4, 8},
    },
    ('10k', 12, 4): {  # 4 days/week variant
        'weekly_km': [12, 14, 16, 12, 18, 20, 22, 16, 26, 28, 26, 15],
        'deload_weeks': {4, 8, 12},
    },
}

SESSION_CONFIG = {
    'easy':      {'rpe_min': 3, 'rpe_max': 4, 'zone': 'Z1-2', 'pace_min_per_km': 8.0},
    'long':      {'rpe_min': 3, 'rpe_max': 4, 'zone': 'Z1-2', 'pace_min_per_km': 8.5},
    'tempo':     {'rpe_min': 6, 'rpe_max': 7, 'zone': 'Z3-4', 'pace_min_per_km': 6.5},
    'intervals': {'rpe_min': 7, 'rpe_max': 9, 'zone': 'Z4-5', 'pace_min_per_km': 6.0},
}

DAYS_3 = ['mon', 'wed', 'sat']
DAYS_4 = ['mon', 'tue', 'thu', 'sat']

PHASE_TYPES_3D = {
    'base':  ['easy', 'easy', 'long'],
    'build': ['easy', 'tempo', 'long'],
    'peak':  ['easy', 'intervals', 'long'],
    'taper': ['easy', 'easy', 'easy'],
}


def get_phase(week: int, total_weeks: int) -> str:
    if total_weeks == 12:
        if week <= 4: return 'base'
        if week <= 8: return 'build'
        if week <= 11: return 'peak'
        return 'taper'
    else:  # 8 weeks
        if week <= 3: return 'base'
        if week <= 6: return 'build'
        if week == 7: return 'peak'
        return 'taper'


def generate_plan_sessions(goal: str, weeks: int, days: int) -> list[dict]:
    config_key = (goal, weeks) if days == 3 else (goal, weeks, days)
    config = SUPPORTED_CONFIGS.get(config_key) or SUPPORTED_CONFIGS.get((goal, weeks))
    if not config:
        raise ValueError(f"Unsupported config: goal={goal}, weeks={weeks}, days={days}")

    day_labels = DAYS_3 if days == 3 else DAYS_4
    sessions = []

    for week in range(1, weeks + 1):
        is_deload = week in config['deload_weeks']
        phase = get_phase(week, weeks)
        weekly_km = config['weekly_km'][week - 1]

        # In deload weeks, use easy sessions only regardless of phase
        types = ['easy', 'easy', 'long'] if is_deload else PHASE_TYPES_3D[phase]

        # Volume distribution
        type_counts = {t: types.count(t) for t in set(types)}
        km_per_type = {}
        if 'long' in types:
            km_per_type['long'] = round(weekly_km * 0.33, 1)
        if 'tempo' in types:
            km_per_type['tempo'] = round(weekly_km * 0.18, 1)
        if 'intervals' in types:
            km_per_type['intervals'] = round(weekly_km * 0.15, 1)
        easy_total = weekly_km - sum(km_per_type.values())
        km_per_type['easy'] = round(easy_total / type_counts.get('easy', 1), 1)

        for day_label, session_type in zip(day_labels, types):
            cfg = SESSION_CONFIG[session_type]
            dist = km_per_type[session_type]
            duration = round(dist * cfg['pace_min_per_km'], 0)
            sessions.append({
                'week': week,
                'day_of_week': day_label,
                'session_type': session_type,
                'target_distance_km': dist,
                'target_duration_min': duration,
                'target_rpe_min': cfg['rpe_min'],
                'target_rpe_max': cfg['rpe_max'],
                'target_zone': cfg['zone'],
                'notes': f"Phase: {phase}" + (" (deload)" if is_deload else ""),
            })

    return sessions


def run_plan(goal: str, weeks: int, days: int, age: int, db_path: str) -> None:
    init_db(db_path)
    conn = get_connection(db_path)

    fcmax_est = fcmax_tanaka(age)
    upsert_profile(conn, {
        'age': age,
        'goal': goal,
        'plan_start_date': str(date_cls.today()),
        'plan_weeks': weeks,
        'days_per_week': days,
        'fcmax_estimated': fcmax_est,
    })
    print(f"Profile created: age={age}, goal={goal}, FCmax estimated={fcmax_est} bpm (Tanaka)")

    sessions = generate_plan_sessions(goal, weeks, days)
    insert_plan_sessions(conn, sessions)
    conn.close()
    print(f"Plan generated: {len(sessions)} sessions over {weeks} weeks.")
    print(f"Start: {date_cls.today()} | Race day (approx): "
          f"{date_cls.today() + timedelta(weeks=weeks)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate training plan')
    parser.add_argument('--goal', choices=['5k', '10k'], required=True)
    parser.add_argument('--weeks', type=int, choices=[8, 12], required=True)
    parser.add_argument('--days', type=int, choices=[3, 4], default=3)
    parser.add_argument('--age', type=int, required=True)
    parser.add_argument('--db', default=DB_PATH)
    args = parser.parse_args()
    run_plan(args.goal, args.weeks, args.days, args.age, args.db)
