# context.py
import os
import sys
from datetime import date as date_cls, datetime, timedelta

from db.schema import init_db, get_connection
from db.queries import (
    get_profile, get_latest_session, get_latest_metrics_snapshot,
    get_sessions_for_period, get_wellness_for_date, get_plan_week,
    get_wellness_history
)
from pipeline.fcmax import get_active_fcmax

DB_PATH = 'db/runs.db'
CONTEXT_PATH = 'data/context.md'
SESSION_LOG_PATH = 'data/session_log.md'

PHASE_LABELS = {
    'base': 'Base', 'build': 'Construcción', 'peak': 'Pico', 'taper': 'Taper'
}


def get_current_week(plan_start_date: str) -> int:
    start = datetime.fromisoformat(plan_start_date).date()
    delta = (date_cls.today() - start).days
    return max(1, delta // 7 + 1)


def get_phase_label(week: int, total_weeks: int) -> str:
    from plan import get_phase
    phase = get_phase(week, total_weeks)
    label = PHASE_LABELS.get(phase, phase)
    return f"{label} (Semana {week}/{total_weeks})"


def get_trends(sessions: list) -> dict:
    """Compute trends from last 4 weeks of sessions."""
    if len(sessions) < 2:
        return {}
    mid = len(sessions) // 2
    vol_h1 = sum(s['distance_km'] for s in sessions[:mid])
    vol_h2 = sum(s['distance_km'] for s in sessions[mid:])
    change_pct = round((vol_h2 - vol_h1) / vol_h1 * 100, 1) if vol_h1 > 0 else 0

    decouplings = [s['decoupling_pct'] for s in sessions if s.get('decoupling_pct')]
    decoupling_trend = None
    if len(decouplings) >= 2:
        decoupling_trend = round(decouplings[-1] - decouplings[0], 1)

    return {
        'volume_change_pct': change_pct,
        'decoupling_trend': decoupling_trend,
    }


def detect_overtraining_signals(tsb: float, muscle_soreness: int, rpe_creep: bool) -> list[str]:
    signals = []
    if tsb < -30:
        signals.append(f"TSB {tsb}: carga alta — considera descanso o sesión fácil")
    if muscle_soreness >= 3:
        signals.append(f"Dolor muscular {muscle_soreness}/5 — posible fatiga acumulada")
    if rpe_creep:
        signals.append("RPE creep detectado — carreras fáciles cuestan más de lo esperado")
    return signals


def build_context_doc(profile: dict, last_session: dict, metrics: dict,
                       trends: dict, plan_week: list, wellness: dict,
                       active_signals: list) -> str:
    fcmax, confidence = get_active_fcmax(profile)
    today = str(date_cls.today())

    phase = get_phase_label(
        get_current_week(profile.get('plan_start_date', today)),
        profile.get('plan_weeks', 12)
    ) if profile.get('plan_start_date') else 'Sin plan activo'

    lines = [
        f"# Estado actual — {today}",
        "",
        "## Perfil",
        f"- Objetivo: {profile['goal'].upper()} | Plan: {profile.get('plan_weeks', '?')} semanas | Fase: {phase}",
        f"- FCmax: {fcmax} lpm ({confidence} confidence) | Días/semana: {profile.get('days_per_week', '?')}",
        "",
    ]

    if last_session:
        dominant_zone = max(
            [(f"zone{i}_pct", last_session.get(f"zone{i}_pct", 0)) for i in range(1, 6)],
            key=lambda x: x[1]
        )
        zone_num = dominant_zone[0][4]
        hr_pct = round(last_session['avg_hr'] / fcmax * 100) if last_session.get('avg_hr') else '?'
        pace_sec = last_session.get('avg_pace_sec_km', 0)
        pace_str = f"{int(pace_sec//60)}:{int(pace_sec%60):02d}/km" if pace_sec else '?'
        decoupling = last_session.get('decoupling_pct')
        drift = last_session.get('cardiac_drift_bpm')
        load = last_session.get('training_load', '?')

        decoupling_str = ""
        if decoupling is not None:
            decoupling_str = f" | Decoupling: {decoupling}%" + (" ✓" if decoupling < 5 else " ⚠️")
        drift_str = f" | Drift: {drift} bpm/h" if drift else ""

        lines += [
            f"## Sesión más reciente — {last_session['date']}",
            f"- Distancia: {last_session.get('distance_km', '?')} km | "
            f"Duración: {last_session.get('duration_min', '?')} min | Ritmo: {pace_str}",
            f"- HR: {last_session.get('avg_hr', '?')} prom / {last_session.get('max_hr', '?')} máx "
            f"→ {hr_pct}% FCmax → Zona {zone_num} predominante",
            f"- Carga Foster: {load} AU{decoupling_str}{drift_str}",
            "",
        ]

    if metrics:
        tsb = metrics.get('tsb', 0)
        tsb_label = "✓ fresco" if tsb > 10 else "⚠️ carga alta" if tsb < -10 else "normal"
        lines += [
            "## Estado de fatiga",
            f"- ATL: {metrics.get('atl', '?')} | CTL: {metrics.get('ctl', '?')} | TSB: {tsb} ({tsb_label})",
        ]
        if wellness:
            lines.append(
                f"- Wellness: sueño {wellness.get('sleep_quality', '?')}/5 | "
                f"dolor {wellness.get('muscle_soreness', '?')}/5 | "
                f"motivación {wellness.get('motivation', '?')}/5"
            )
        lines.append("")

    if trends:
        vol_chg = trends.get('volume_change_pct', 0)
        vol_arrow = '↑' if vol_chg > 0 else '↓'
        vol_warn = ' ⚠️ (>30%)' if abs(vol_chg) > 30 else ' ✓'
        decoup_trend = trends.get('decoupling_trend')
        lines += [
            "## Tendencias 4 semanas",
            f"- Volumen: {vol_arrow} {abs(vol_chg)}% vs 2 semanas previas{vol_warn}",
        ]
        if decoup_trend is not None:
            direction = "mejorando" if decoup_trend < 0 else "empeorando"
            lines.append(f"- Decoupling: {direction} ({decoup_trend:+.1f}%)")
        lines.append("")

    if plan_week:
        lines.append("## Plan semana actual")
        for s in plan_week:
            lines.append(
                f"- ⬜ {s['day_of_week'].capitalize()}: "
                f"{s['session_type'].capitalize()} {s['target_distance_km']} km "
                f"({s['target_zone']}, RPE {s.get('target_rpe_min')}-{s.get('target_rpe_max')})"
            )
        lines.append("")

    if active_signals:
        lines.append("## Señales activas")
        for sig in active_signals:
            lines.append(f"- {sig}")
        lines.append("")

    return '\n'.join(lines)


def build_session_log(sessions: list) -> str:
    header = "fecha      | km   | min  | avg_hr | z2%  | load  | decoup"
    separator = "-" * len(header)
    rows = [header, separator]
    for s in sorted(sessions, key=lambda x: x['date'], reverse=True):
        rows.append(
            f"{s['date']} | {s.get('distance_km', '?'):<4} | "
            f"{s.get('duration_min', '?'):<4} | "
            f"{s.get('avg_hr', '?'):<6} | "
            f"{s.get('zone2_pct', '?'):<4} | "
            f"{s.get('training_load', '?'):<5} | "
            f"{s.get('decoupling_pct', '?')}"
        )
    return '\n'.join(rows)


def run_context(db_path: str = DB_PATH) -> None:
    os.makedirs('data', exist_ok=True)
    init_db(db_path)
    conn = get_connection(db_path)

    profile = get_profile(conn)
    if not profile:
        print("No profile found. Run 'python plan.py' first.")
        conn.close()
        return

    last_session = get_latest_session(conn)
    metrics = get_latest_metrics_snapshot(conn)
    today = str(date_cls.today())
    wellness = get_wellness_for_date(conn, today)

    # 4-week sessions for trends
    four_weeks_ago = str(date_cls.today() - timedelta(weeks=4))
    recent_sessions = get_sessions_for_period(conn, four_weeks_ago, today)
    trends = get_trends(recent_sessions)

    # Current plan week
    plan_week = []
    if profile.get('plan_start_date') and profile.get('plan_weeks'):
        current_week = get_current_week(profile['plan_start_date'])
        if current_week <= profile['plan_weeks']:
            plan_week = get_plan_week(conn, current_week)

    # Overtraining signals
    tsb = metrics['tsb'] if metrics else 0
    soreness = wellness.get('muscle_soreness', 0) if wellness else 0
    signals = detect_overtraining_signals(tsb, soreness, rpe_creep=False)

    # 12-week session log
    twelve_weeks_ago = str(date_cls.today() - timedelta(weeks=12))
    all_recent = get_sessions_for_period(conn, twelve_weeks_ago, today)
    conn.close()

    context_doc = build_context_doc(profile, last_session, metrics, trends,
                                     plan_week, wellness, signals)
    with open(CONTEXT_PATH, 'w') as f:
        f.write(context_doc)

    session_log = build_session_log(all_recent)
    with open(SESSION_LOG_PATH, 'w') as f:
        f.write(session_log)

    print(f"Context updated: {CONTEXT_PATH} ({len(context_doc)} chars)")


if __name__ == '__main__':
    run_context()
