"""Pytest configuration and shared fixtures for the Writing Contest Web App tests.

This module provides fixtures and setup code used across multiple test modules,
including the Flask test client.
"""

import pytest
from app import app as flask_app


@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test_secret_key'
    return flask_app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client
