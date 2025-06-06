"""Pytest configuration and shared fixtures for the Writing Contest Web App tests.

This module provides fixtures and setup code used across multiple test modules,
including the Flask test client.
"""

import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    with app.test_client() as client:
        yield client
