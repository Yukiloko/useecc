import sqlite3
from pathlib import Path

from flask import current_app, g

SCHEMA = Path(__file__).with_name("schema.sql")


def connect(path):
    conn = sqlite3.connect(path, detect_types=0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn):
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.commit()


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def get_config(conn, chave, padrao=None):
    row = conn.execute("SELECT valor FROM config WHERE chave = ?", (chave,)).fetchone()
    return row["valor"] if row else padrao


def set_config(conn, chave, valor):
    conn.execute(
        "INSERT INTO config (chave, valor) VALUES (?, ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
        (chave, str(valor)),
    )
