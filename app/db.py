"""SQLite storage for normalized events (stdlib only)."""

import json
import sqlite3
from pathlib import Path

from flask import Flask, current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL,
    src_ip     TEXT NOT NULL,
    user       TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    doc        TEXT NOT NULL
)
"""


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        path = current_app.config["DATABASE"]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
        g.db.execute(SCHEMA)
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)


def insert_event(doc: dict) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO events (ts, src_ip, user, risk_score, doc) VALUES (?, ?, ?, ?, ?)",
        (doc["@timestamp"], doc["source"]["ip"], doc["user"]["name"], doc["risk_score"], json.dumps(doc)),
    )
    conn.commit()
    return cur.lastrowid


def search_by_user(user: str) -> list[dict]:
    # Parameterized: the driver sends `user` as data, never as SQL text (B-02).
    rows = get_db().execute("SELECT doc FROM events WHERE user = ? ORDER BY id", (user,))
    return [json.loads(row["doc"]) for row in rows]


def summary_counts() -> dict:
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    matched = conn.execute(
        "SELECT COUNT(*) FROM events WHERE doc LIKE ?", ("%threat.indicator.matched%",)
    ).fetchone()[0]
    top = conn.execute(
        "SELECT src_ip, MAX(risk_score) AS score FROM events GROUP BY src_ip ORDER BY score DESC LIMIT 5"
    ).fetchall()
    return {"total": total, "matched": matched, "top": [(r["src_ip"], r["score"]) for r in top]}
