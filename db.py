"""
Provides database connection management and helper functions for executing and
querying SQL statements using SQLite and Flask's application context.

Functions:
    get_connection()
    execute(sql, params=None)
    query(sql, params=None)
    last_insert_id()
    close_connection(e=None)
"""

import sqlite3
from flask import g, current_app


def get_connection():
    """
    Get a SQLite database connection for the current Flask application context.
    Ensures foreign key support and sets row_factory to sqlite3.Row.

    Returns:
        sqlite3.Connection: The database connection.

    Raises:
        sqlite3.Error: If a connection cannot be established.
    """
    if "db" not in g:
        try:
            # This is the critical change: use the config from the current app.
            db_path = current_app.config["DATABASE"]
            g.db = sqlite3.connect(db_path, timeout=5)
            g.db.execute("PRAGMA foreign_keys = ON")
            g.db.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            current_app.logger.error(f"Database connection error: {e}")
            raise
    return g.db


def execute(sql, params=None):
    """
    Execute a SQL statement (INSERT, UPDATE, DELETE).

    Args:
        sql (str): The SQL statement to execute.
        params (list, optional): Parameters for the SQL statement.

    Returns:
        sqlite3.Cursor: The result cursor.

    Raises:
        sqlite3.IntegrityError: On integrity constraint violation.
        sqlite3.Error: On other database errors.
    """
    if params is None:
        params = []
    try:
        con = get_connection()
        result = con.execute(sql, params)
        con.commit()
        g.last_insert_id = result.lastrowid
        return result
    except sqlite3.IntegrityError as e:
        current_app.logger.warning(f"Integrity error: {e}")
        raise
    except sqlite3.Error as e:
        current_app.logger.error(f"Database error in execute: {e}")
        raise


def query(sql, params=None):
    """
    Execute a SQL SELECT statement and return all results.

    Args:
        sql (str): The SQL SELECT statement.
        params (list, optional): Parameters for the SQL statement.

    Returns:
        list: List of sqlite3.Row objects.

    Raises:
        sqlite3.Error: On database errors.
    """
    if params is None:
        params = []
    try:
        con = get_connection()
        return con.execute(sql, params).fetchall()
    except sqlite3.Error as e:
        current_app.logger.error(f"Database error in query: {e}")
        raise


def last_insert_id():
    """
    Get the last inserted row ID for the current request.

    Returns:
        int or None: The last inserted row ID, or None if not set.
    """
    return g.get("last_insert_id", None)


def close_connection(_=None):
    """
    Close the database connection for the current Flask application context.

    Args:
        _ (Exception, optional): Exception passed by Flask's teardown context.
                                 This argument is unused but required by the
                                 teardown function signature.

    Returns:
        None
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()
