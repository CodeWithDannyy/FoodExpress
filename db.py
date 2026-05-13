"""
Database connection helper.

Each Flask request gets one MySQL connection stashed on `flask.g`,
which is closed automatically when the request ends.

Usage:
    from db import query_all, query_one, execute

    rows = query_all("SELECT * FROM restaurants WHERE is_active = %s", (True,))
    row  = query_one("SELECT * FROM customers WHERE email = %s", (email,))
    new_id = execute("INSERT INTO customers (...) VALUES (...)", (...))
"""

import mysql.connector
from flask import g
from config import DB_CONFIG


# Connection lifecycle
def get_db():
    """Return the MySQL connection for the current request, opening one
    on first use."""
    if "db" not in g:
        g.db = mysql.connector.connect(**DB_CONFIG)
    return g.db


def close_db(_=None):
    """Close the request's connection (registered as teardown handler)."""
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()


def init_app(app):
    """Wire the teardown handler to the Flask app."""
    app.teardown_appcontext(close_db)



# Query helpers — every cursor returns rows as dicts so templates can use
# row["column_name"] (matching the old in-memory style).
def query_all(sql, params=None):
    """Run a SELECT and return ALL rows as a list of dicts."""
    cur = get_db().cursor(dictionary=True)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    return rows


def query_one(sql, params=None):
    """Run a SELECT and return the FIRST row as a dict (or None)."""
    cur = get_db().cursor(dictionary=True)
    cur.execute(sql, params or ())
    row = cur.fetchone()
    cur.fetchall()        # drain in case of multi-row result
    cur.close()
    return row


def execute(sql, params=None):
    """Run an INSERT/UPDATE/DELETE. Commits and returns lastrowid."""
    db = get_db()
    cur = db.cursor()
    cur.execute(sql, params or ())
    db.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id


def execute_many(sql, seq_of_params):
    """Run an INSERT for many rows in one round trip."""
    db = get_db()
    cur = db.cursor()
    cur.executemany(sql, seq_of_params)
    db.commit()
    cur.close()
