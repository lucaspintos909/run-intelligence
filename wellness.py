import subprocess
import sys
from datetime import date as date_cls

from db.schema import init_db, get_connection
from db.queries import insert_wellness, get_wellness_history

DB_PATH = 'db/runs.db'


def build_wellness_dict(resting_hr: int, sleep_quality: int, sleep_hours: float,
                         mood: int, muscle_soreness: int, motivation: int,
                         energy: int, session_rpe=None) -> dict:
    return {
        'resting_hr': resting_hr,
        'sleep_quality': sleep_quality,
        'sleep_hours': sleep_hours,
        'mood': mood,
        'muscle_soreness': muscle_soreness,
        'motivation': motivation,
        'energy': energy,
        'session_rpe': session_rpe,
        'has_session': 1 if session_rpe is not None else 0,
    }


def validate_wellness(data: dict) -> list[str]:
    errors = []
    hr = data.get('resting_hr', 0)
    if not (30 <= hr <= 200):
        errors.append(f"resting_hr {hr} out of range 30-200")
    for field in ['sleep_quality', 'mood', 'muscle_soreness', 'motivation', 'energy']:
        val = data.get(field, 0)
        if not (1 <= val <= 5):
            errors.append(f"{field} {val} out of range 1-5")
    rpe = data.get('session_rpe')
    if rpe is not None and not (1 <= rpe <= 10):
        errors.append(f"session_rpe {rpe} out of range 1-10")
    return errors


def _ask_question(prompt: str, cast, valid_range=None):
    while True:
        try:
            val = cast(input(prompt))
            if valid_range and not (valid_range[0] <= val <= valid_range[1]):
                print(f"  Valor inválido. Rango: {valid_range}")
                continue
            return val
        except (ValueError, KeyboardInterrupt):
            print("  Entrada inválida, intenta de nuevo.")


def run_wellness(db_path: str = DB_PATH) -> None:
    init_db(db_path)
    print("\n=== Bienestar matutino ===")
    data = build_wellness_dict(
        resting_hr=_ask_question("FC en reposo (bpm): ", int, (30, 200)),
        sleep_quality=_ask_question("Calidad de sueño 1-5: ", int, (1, 5)),
        sleep_hours=_ask_question("Horas de sueño: ", float, (0, 24)),
        mood=_ask_question("Estado de ánimo 1-5: ", int, (1, 5)),
        muscle_soreness=_ask_question("Dolor muscular 1-5: ", int, (1, 5)),
        motivation=_ask_question("Motivación 1-5: ", int, (1, 5)),
        energy=_ask_question("Energía 1-5: ", int, (1, 5)),
    )
    errors = validate_wellness(data)
    if errors:
        print("Errores de validación:", errors)
        return

    conn = get_connection(db_path)
    today = str(date_cls.today())
    insert_wellness(conn, today, data)
    conn.close()
    print(f"Wellness guardado para {today}.")

    conn = get_connection(db_path)
    history = get_wellness_history(conn, days=7)
    conn.close()
    _check_overtraining_signals(data, history)

    subprocess.run([sys.executable, 'context.py'], check=False)


def _check_overtraining_signals(today_data: dict, history: list) -> None:
    warnings = []
    if today_data['muscle_soreness'] >= 3:
        consecutive = sum(1 for h in history[:3] if h.get('muscle_soreness', 0) >= 3)
        if consecutive >= 3:
            warnings.append("⚠️  Dolor muscular ≥3/5 por 3+ días consecutivos")

    scores = ['sleep_quality', 'mood', 'motivation', 'energy']
    declining = [s for s in scores if len(history) >= 5
                 and all(history[i].get(s, 3) >= history[i+1].get(s, 3)
                         for i in range(4))]
    if len(declining) >= 2:
        warnings.append("⚠️  2+ métricas de bienestar en tendencia descendente (5 días)")

    for w in warnings:
        print(w)
    if warnings:
        print("Considera descanso adicional o consulta médica si persiste.")


if __name__ == '__main__':
    run_wellness()
