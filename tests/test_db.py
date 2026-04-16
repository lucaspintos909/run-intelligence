import pytest
import sqlite3
from db.schema import init_db, get_connection

def test_init_db_creates_all_tables(db_path):
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    assert tables == {'profile', 'sessions', 'wellness', 'metrics_snapshot', 'plan_sessions'}

def test_get_connection_returns_row_factory(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    conn.execute("INSERT INTO profile (age, goal, fcmax_estimated) VALUES (32, '10k', 186)")
    conn.commit()
    row = conn.execute("SELECT * FROM profile").fetchone()
    conn.close()
    assert row['age'] == 32
    assert row['goal'] == '10k'

def test_profile_fcmax_fields_nullable(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    conn.execute("INSERT INTO profile (age, goal, fcmax_estimated) VALUES (32, '10k', 186)")
    conn.commit()
    row = conn.execute("SELECT fcmax_manual, fcmax_observed FROM profile").fetchone()
    conn.close()
    assert row['fcmax_manual'] is None
    assert row['fcmax_observed'] is None
