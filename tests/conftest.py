"""Pytest configuration and shared fixtures for the Writing Contest Web App
tests.

This module provides fixtures and setup code used across multiple test modules,
including the Flask test client.
"""

import os
import tempfile
import pytest
from app import app as flask_app
from db import get_connection


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_path = tempfile.mkstemp()

    # Use a different name for the local app instance to avoid shadowing
    # the fixture name
    _app = flask_app
    _app.config.update({
        "TESTING": True,
        "DATABASE": db_path,
        "WTF_CSRF_ENABLED": False,
    })

    # Manually initialize the database for the test
    with _app.app_context():
        # Get the database connection using the function from your db.py
        db_conn = get_connection()
        # Open and execute the schema file to set up the tables
        with _app.open_resource('schema.sql') as f:
            db_conn.executescript(f.read().decode('utf8'))

    yield _app

    # Clean up: close and remove the temporary database file
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()
