"""Unit tests for the sql.py database interaction functions."""
from unittest.mock import MagicMock
import pytest
import sql
import db


class TestSqlFunctions:
    """Tests for the database interaction functions in sql.py."""

    # Contest CRUD
    def test_get_all_contests_with_all_filters(self, monkeypatch):
        """Verifies that get_all_contests constructs the correct SQL query and
        parameters when all filters are applied.
        """
        mock_query = MagicMock()
        monkeypatch.setattr(db, "query", mock_query)
        sql.get_all_contests(limit=10, offset=5, title_search="Test")

        expected_sql = ("""
        SELECT contests.id, contests.title, contests.collection_end,
               contests.review_end, classes.value AS class_value
        FROM contests
        JOIN classes ON contests.class_id = classes.id
     WHERE contests.title LIKE ? ORDER BY contests.collection_end DESC """
                        """LIMIT ? OFFSET ?""")
        mock_query.assert_called_with(expected_sql, ["%Test%", 10, 5])

    def test_get_contest_by_id_not_found(self, monkeypatch):
        """Tests that get_contest_by_id returns None for a non-existent ID."""
        monkeypatch.setattr(db, "query", lambda *a: [])
        assert sql.get_contest_by_id(999) is None

    def test_update_contest(self, monkeypatch):
        """Tests that update_contest calls the underlying database execute
        method.
        """
        mock_execute = MagicMock()
        monkeypatch.setattr(db, "execute", mock_execute)
        contest_data = {
            "title": "T", "class_id": 1, "short_description": "s",
            "long_description": "l", "anonymity": True,
            "public_reviews": True, "public_results": True,
            "collection_end": "d1", "review_end": "d2"
        }
        sql.update_contest(1, contest_data)
        assert mock_execute.called

    def test_delete_contest(self, monkeypatch):
        """Tests that delete_contest constructs the correct DELETE SQL
        statement.
        """
        mock_execute = MagicMock()
        monkeypatch.setattr(db, "execute", mock_execute)
        sql.delete_contest(1)
        mock_execute.assert_called_with(
            "DELETE FROM contests WHERE id = ?", [1])

    def test_create_contest(self, monkeypatch):
        """Tests that create_contest calls the underlying database execute
        method.
        """
        mock_execute = MagicMock()
        monkeypatch.setattr(db, "execute", mock_execute)
        contest_data = {
            "title": "T", "class_id": 1, "short_description": "s",
            "long_description": "l", "anonymity": True,
            "public_reviews": True, "public_results": True,
            "collection_end": "d1", "review_end": "d2", "private_key": "key"
        }
        sql.create_contest(contest_data)
        assert mock_execute.called

    # Contest Listings
    @pytest.mark.parametrize("func", [
        sql.get_contests_for_entry,
        sql.get_contests_for_review,
        sql.get_contests_for_results
    ])
    def test_contest_listing_functions_with_limit_offset(self, monkeypatch,
                                                         func):
        """Tests that contest listing functions apply limit and offset
        correctly.

        This test is parameterized to cover get_contests_for_entry,
        get_contests_for_review, and get_contests_for_results.

        Args:
            monkeypatch: The pytest monkeypatch fixture.
            func: The parameterized sql function to test.
        """
        mock_query = MagicMock()
        monkeypatch.setattr(db, "query", mock_query)
        func(limit=10, offset=5)

        # Get the arguments the mock was called with
        call_args = mock_query.call_args
        generated_sql = call_args[0][0]
        params = call_args[0][1]

        # Check that the generated SQL string contains the placeholders
        assert "LIMIT ?" in generated_sql
        assert "OFFSET ?" in generated_sql

        # Check that the parameters list contains the correct values
        assert params == [10, 5]

    # Contest Counts
    def test_get_contest_count_with_search(self, monkeypatch):
        """Tests get_contest_count with a title search filter."""
        monkeypatch.setattr(db, "query", lambda *a: [[5]])
        count = sql.get_contest_count(title_search="Test")
        assert count == 5

    def test_get_contest_count_no_result(self, monkeypatch):
        """Tests that get_contest_count returns 0 when the query finds no
        contests.
        """
        monkeypatch.setattr(db, "query", lambda *a: [])
        assert sql.get_contest_count() == 0

    @pytest.mark.parametrize("func, expected_sql_part", [
        (sql.get_entry_contest_count, "collection_end >= DATE('now')"),
        (sql.get_review_contest_count, "review_end >= DATE('now')"),
        (sql.get_results_contest_count, "review_end < DATE('now')")
    ])
    def test_time_based_contest_counts(self, monkeypatch, func,
                                       expected_sql_part):
        """Tests that time-based count functions build correct SQL and handle
        empty results.

        Args:
            monkeypatch: The pytest monkeypatch fixture.
            func: The parameterized sql function to test.
            expected_sql_part: The expected time-based clause in the SQL query.
        """
        mock_query = MagicMock(return_value=[[3]])
        monkeypatch.setattr(db, "query", mock_query)
        assert func() == 3
        assert expected_sql_part in mock_query.call_args[0][0]
        # Test empty case
        mock_query.return_value = []
        assert func() == 0

    # Entry CRUD
    def test_create_entry(self, monkeypatch):
        """Tests that create_entry constructs the correct INSERT SQL
        statement."""
        mock_execute = MagicMock()
        monkeypatch.setattr(db, "execute", mock_execute)
        sql.create_entry(1, 1, "content")
        mock_execute.assert_called_with(
            "INSERT INTO entries (contest_id, user_id, entry)\n"
            "             VALUES (?, ?, ?)",
            [1, 1, "content"]
        )

    def test_get_all_entries_with_all_filters(self, monkeypatch):
        """Verifies that get_all_entries constructs the correct SQL query when
        all filters are applied.
        """
        mock_query = MagicMock()
        monkeypatch.setattr(db, "query", mock_query)
        sql.get_all_entries(limit=10, offset=5,
                            contest_id=1, user_search="Test")
        assert "contests.id = ?" in mock_query.call_args[0][0]
        assert "users.name LIKE ?" in mock_query.call_args[0][0]
        assert "LIMIT ? OFFSET ?" in mock_query.call_args[0][0]

    def test_get_entry_by_id_not_found(self, monkeypatch):
        """Tests that get_entry_by_id returns None for a non-existent ID."""
        monkeypatch.setattr(db, "query", lambda *a: [])
        assert sql.get_entry_by_id(999) is None

    def test_update_entry(self, monkeypatch):
        """Tests that update_entry calls the underlying database execute
        method.
        """
        mock_execute = MagicMock()
        monkeypatch.setattr(db, "execute", mock_execute)
        sql.update_entry(1, 2, 3, "content")
        assert mock_execute.called

    def test_delete_entry(self, monkeypatch):
        """Tests that delete_entry constructs the correct DELETE SQL
        statement."""
        mock_execute = MagicMock()
        monkeypatch.setattr(db, "execute", mock_execute)
        sql.delete_entry(1)
        mock_execute.assert_called_with(
            "DELETE FROM entries WHERE id = ?", [1])

    # Entry Helpers
    def test_entry_exists(self, monkeypatch):
        """Tests that entry_exists correctly identifies if an entry exists."""
        monkeypatch.setattr(db, "query", lambda *a: [1])
        assert sql.entry_exists(1, 1) is True
        monkeypatch.setattr(db, "query", lambda *a: [])
        assert sql.entry_exists(1, 1) is False

    def test_get_entry_count_with_filters(self, monkeypatch):
        """Tests get_entry_count with multiple filters applied."""
        mock_query = MagicMock(return_value=[{"count": 1}])
        monkeypatch.setattr(db, "query", mock_query)
        count = sql.get_entry_count(contest_id=1, user_search="Test")
        assert count == 1
        assert "contests.id = ?" in mock_query.call_args[0][0]
        assert "users.name LIKE ?" in mock_query.call_args[0][0]

    def test_get_entry_count_no_result(self, monkeypatch):
        """Tests that get_entry_count returns 0 when the query finds no
        entries.
        """
        monkeypatch.setattr(db, "query", lambda *a: [])
        assert sql.get_entry_count() == 0

    def test_get_user_entry_for_contest_not_found(self, monkeypatch):
        """Tests that get_user_entry_for_contest returns None when no entry is
        found.
        """
        monkeypatch.setattr(db, "query", lambda *a: [])
        assert sql.get_user_entry_for_contest(1, 1) is None

    # Review CRUD
    def test_add_review(self, monkeypatch):
        """Tests that add_review calls the underlying database execute
        method."""
        mock_execute = MagicMock()
        monkeypatch.setattr(db, "execute", mock_execute)
        sql.add_review(1, 1, 5, "review")
        assert mock_execute.called

    def test_get_entries_for_review(self, monkeypatch):
        """Tests that get_entries_for_review includes ORDER BY RANDOM() in its
        query.
        """
        mock_query = MagicMock()
        monkeypatch.setattr(db, "query", mock_query)
        sql.get_entries_for_review(1)
        assert "ORDER BY RANDOM()" in mock_query.call_args[0][0]

    def test_save_review(self, monkeypatch):
        """Tests that save_review uses an ON CONFLICT clause for upserting."""
        mock_execute = MagicMock()
        monkeypatch.setattr(db, "execute", mock_execute)
        sql.save_review(1, 1, 5)
        assert "ON CONFLICT" in mock_execute.call_args[0][0]

    def test_get_review_count(self, monkeypatch):
        """Tests that get_review_count returns the correct count from the
        query.
        """
        monkeypatch.setattr(db, "query", lambda *a: [[5]])
        assert sql.get_review_count(1) == 5

    def test_get_user_reviews_for_contest(self, monkeypatch):
        """Tests that get_user_reviews_for_contest returns a correctly
        formatted dictionary.
        """
        mock_rows = [{"entry_id": 10, "points": 5},
                     {"entry_id": 12, "points": 3}]
        monkeypatch.setattr(db, "query", lambda *a: mock_rows)
        reviews = sql.get_user_reviews_for_contest(1, 1)
        assert reviews == {10: 5, 12: 3}

    # Class Helpers
    def test_get_all_classes(self, monkeypatch):
        """Tests that get_all_classes constructs the correct SELECT SQL
        statement.
        """
        mock_query = MagicMock()
        monkeypatch.setattr(db, "query", mock_query)
        sql.get_all_classes()
        mock_query.assert_called_with(
            "SELECT id, value FROM classes ORDER BY value")

    def test_get_class_by_id_not_found(self, monkeypatch):
        """Tests that get_class_by_id returns None for a non-existent ID."""
        monkeypatch.setattr(db, "query", lambda *a: [])
        assert sql.get_class_by_id(999) is None

    # Results and Stats
    def test_get_contest_results(self, monkeypatch):
        """Tests that get_contest_results orders the results by points."""
        mock_query = MagicMock()
        monkeypatch.setattr(db, "query", mock_query)
        sql.get_contest_results(1)
        assert "ORDER BY points DESC" in mock_query.call_args[0][0]

    def test_get_user_entries_with_results(self, monkeypatch):
        """Tests that get_user_entries_with_results uses a RANK() window
        function.
        """
        mock_query = MagicMock()
        monkeypatch.setattr(db, "query", mock_query)
        sql.get_user_entries_with_results(1)
        assert "RANK() OVER" in mock_query.call_args[0][0]

    def test_get_user_entry_count(self, monkeypatch):
        """Tests that get_user_entry_count returns the correct count and
        handles empty results.
        """
        monkeypatch.setattr(db, "query", lambda *a: [{"count": 3}])
        assert sql.get_user_entry_count(1) == 3
        monkeypatch.setattr(db, "query", lambda *a: [])
        assert sql.get_user_entry_count(1) == 0
