import pytest
import sqlite3
from flask import g
from app import app
import db


class TestDatabaseOperations:
    """Tests for the database utility functions in db.py."""

    def test_get_connection_creates_and_caches(self):
        """Test that get_connection creates a new connection and caches it
        in g."""
        with app.app_context():
            # On first call, a new connection is made and stored in g
            conn1 = db.get_connection()
            assert isinstance(conn1, sqlite3.Connection)
            assert 'db' in g

            # On second call, the cached connection is returned
            conn2 = db.get_connection()
            assert conn1 is conn2

    def test_close_connection(self):
        """Test that close_connection removes the database from g and
        closes it."""
        with app.app_context():
            db.get_connection()
            assert 'db' in g
            db.close_connection()
            assert 'db' not in g

    def test_close_connection_is_idempotent(self):
        """Test that closing a non-existent connection does not raise
        an error."""
        with app.app_context():
            # Should not raise an error if 'db' is not in g
            db.close_connection()
            assert 'db' not in g

    def test_execute_query_and_last_id(self):
        """Test successful execute, query, and last_insert_id calls."""
        with app.app_context():
            db.execute(
                "CREATE TABLE IF NOT EXISTS test_table "
                "(id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
            db.execute("DELETE FROM test_table")  # Clean up from previous runs

            # Test execute and last_insert_id
            result = db.execute(
                "INSERT INTO test_table (name) VALUES (?)", ["test1"])
            assert result.rowcount == 1
            last_id = db.last_insert_id()
            assert last_id is not None

            # Test query
            rows = db.query("SELECT * FROM test_table WHERE id = ?", [last_id])
            assert len(rows) == 1
            assert rows[0]['name'] == 'test1'

            db.execute("DROP TABLE test_table")

    def test_last_insert_id_without_insert(self):
        """Test that last_insert_id returns None when no insert
        has occurred."""
        with app.app_context():
            assert db.last_insert_id() is None

    def test_execute_raises_integrity_error(self):
        """Test that execute correctly raises IntegrityError for constraint
        violations."""
        with app.app_context():
            db.execute(
                "CREATE TABLE IF NOT EXISTS test_table "
                "(id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
            db.execute("DELETE FROM test_table")
            db.execute("INSERT INTO test_table (name) VALUES (?)",
                       ["unique_name"])

            with pytest.raises(sqlite3.IntegrityError):
                # Attempt to insert the same unique name again
                db.execute("INSERT INTO test_table (name) VALUES (?)", [
                           "unique_name"])

            db.execute("DROP TABLE test_table")

    def test_execute_raises_general_error_on_bad_sql(self):
        """Test that execute raises a general sqlite3.Error for bad SQL."""
        with app.app_context():
            with pytest.raises(sqlite3.Error):
                db.execute("THIS IS NOT VALID SQL")

    def test_query_raises_general_error_on_bad_sql(self):
        """Test that query raises a general sqlite3.Error for bad SQL."""
        with app.app_context():
            with pytest.raises(sqlite3.Error):
                db.query("SELECT * FROM a_table_that_does_not_exist")

    def test_connection_failure(self, monkeypatch):
        """Test the exception handling in get_connection when sqlite3.connect
        fails."""
        # Mock sqlite3.connect to always raise an error
        def mock_connect(*args, **kwargs):
            raise sqlite3.Error("Mock connection error")

        monkeypatch.setattr(sqlite3, "connect", mock_connect)

        with app.app_context():
            with pytest.raises(sqlite3.Error, match="Mock connection error"):
                db.get_connection()
