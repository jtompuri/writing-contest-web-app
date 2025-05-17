import sqlite3
from flask import g, current_app

DATABASE = "database.db"

def get_connection():
    if "db" not in g:
        try:
            g.db = sqlite3.connect(DATABASE, timeout=5)
            g.db.execute("PRAGMA foreign_keys = ON")
            g.db.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            current_app.logger.error(f"Database connection error: {e}")
            raise
    return g.db

def execute(sql, params=[]):
    try:
        con = get_connection()
        result = con.execute(sql, params)
        con.commit()
        g.last_insert_id = result.lastrowid
        return result
    except sqlite3.IntegrityError as e:
        # esim. UNIQUE-rikkomus
        current_app.logger.warning(f"Integrity error: {e}")
        raise
    except sqlite3.Error as e:
        current_app.logger.error(f"Database error in execute: {e}")
        raise

def query(sql, params=[]):
    try:
        con = get_connection()
        return con.execute(sql, params).fetchall()
    except sqlite3.Error as e:
        current_app.logger.error(f"Database error in query: {e}")
        raise

def last_insert_id():
    return g.get("last_insert_id", None)

def close_connection(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()