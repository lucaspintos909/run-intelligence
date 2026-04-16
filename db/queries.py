import json
import sqlite3
from typing import Optional


def get_profile(conn: sqlite3.Connection) -> Optional[dict]:
    row = conn.execute("SELECT * FROM profile WHERE id=1").fetchone()
    return dict(row) if row else None


def upsert_profile(conn: sqlite3.Connection, data: dict) -> None:
    existing = get_profile(conn)
    if existing:
        fields = ', '.join(f"{k}=?" for k in data)
        conn.execute(f"UPDATE profile SET {fields} WHERE id=1", list(data.values()))
    else:
        data.setdefault('id', 1)
        fields = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        conn.execute(f"INSERT INTO profile ({fields}) VALUES ({placeholders})", list(data.values()))
    conn.commit()


def update_fcmax_observed(conn: sqlite3.Connection, fcmax: int) -> None:
    conn.execute("UPDATE profile SET fcmax_observed=? WHERE id=1", (fcmax,))
    conn.commit()


def insert_session(conn: sqlite3.Connection, data: dict) -> int:
    fields = ', '.join(data.keys())
    placeholders = ', '.join('?' * len(data))
    cursor = conn.execute(
        f"INSERT INTO sessions ({fields}) VALUES ({placeholders})",
        list(data.values())
    )
    conn.commit()
    return cursor.lastrowid


def update_session_rpe(conn: sqlite3.Connection, session_id: int, rpe_actual: float) -> None:
    conn.execute(
        "UPDATE sessions SET rpe_actual=?, training_load=COALESCE(?,rpe_estimated)*duration_min WHERE id=?",
        (rpe_actual, rpe_actual, session_id)
    )
    conn.commit()


def get_latest_session(conn: sqlite3.Connection) -> Optional[dict]:
    row = conn.execute("SELECT * FROM sessions ORDER BY date DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def get_sessions_for_period(conn: sqlite3.Connection, start_date: str, end_date: str) -> list:
    rows = conn.execute(
        "SELECT * FROM sessions WHERE date BETWEEN ? AND ? ORDER BY date",
        (start_date, end_date)
    ).fetchall()
    return [dict(r) for r in rows]


def get_all_sessions_loads(conn: sqlite3.Connection) -> list:
    """Returns [(date, training_load)] sorted by date ASC."""
    rows = conn.execute(
        "SELECT date, COALESCE(training_load, 0) as load FROM sessions ORDER BY date"
    ).fetchall()
    return [(r['date'], r['load']) for r in rows]


def insert_wellness(conn: sqlite3.Connection, date: str, data: dict) -> None:
    data['date'] = date
    fields = ', '.join(data.keys())
    placeholders = ', '.join('?' * len(data))
    conn.execute(
        f"INSERT OR REPLACE INTO wellness ({fields}) VALUES ({placeholders})",
        list(data.values())
    )
    conn.commit()


def get_wellness_for_date(conn: sqlite3.Connection, date: str) -> Optional[dict]:
    row = conn.execute("SELECT * FROM wellness WHERE date=?", (date,)).fetchone()
    return dict(row) if row else None


def get_wellness_history(conn: sqlite3.Connection, days: int = 14) -> list:
    rows = conn.execute(
        "SELECT * FROM wellness ORDER BY date DESC LIMIT ?", (days,)
    ).fetchall()
    return [dict(r) for r in rows]


def insert_metrics_snapshot(conn: sqlite3.Connection, date: str,
                             atl: float, ctl: float, tsb: float) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO metrics_snapshot (date,atl,ctl,tsb) VALUES (?,?,?,?)",
        (date, atl, ctl, tsb)
    )
    conn.commit()


def get_latest_metrics_snapshot(conn: sqlite3.Connection) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM metrics_snapshot ORDER BY date DESC LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


def insert_plan_sessions(conn: sqlite3.Connection, sessions: list) -> None:
    conn.execute("DELETE FROM plan_sessions")
    for s in sessions:
        fields = ', '.join(s.keys())
        placeholders = ', '.join('?' * len(s))
        conn.execute(f"INSERT INTO plan_sessions ({fields}) VALUES ({placeholders})",
                     list(s.values()))
    conn.commit()


def get_plan_week(conn: sqlite3.Connection, week: int) -> list:
    rows = conn.execute(
        "SELECT * FROM plan_sessions WHERE week=? ORDER BY id", (week,)
    ).fetchall()
    return [dict(r) for r in rows]
