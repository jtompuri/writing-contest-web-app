import sqlite3
from unittest.mock import patch, MagicMock
import users
import db


class TestUserFunctions:
    """Tests for the user management functions in users.py."""

    def test_create_user_success(self, monkeypatch):
        """Test successful user creation."""
        mock_execute = MagicMock()
        # Mock last_insert_id to avoid the context error and return
        # a predictable ID
        mock_last_id = MagicMock(return_value=1)
        monkeypatch.setattr(db, "execute", mock_execute)
        monkeypatch.setattr(db, "last_insert_id", mock_last_id)

        result = users.create_user(
            "Test User", "test@example.com", "password123", 0)

        # The function should now return the ID from last_insert_id
        assert result == 1
        mock_execute.assert_called_once()
        # Check that the password was hashed using the new default method
        assert mock_execute.call_args[0][1][2].startswith("scrypt:")

    def test_create_user_integrity_error(self, monkeypatch):
        """Test user creation failure due to an existing username."""
        mock_execute = MagicMock(side_effect=sqlite3.IntegrityError)
        monkeypatch.setattr(db, "execute", mock_execute)

        result = users.create_user(
            "Test User", "test@example.com", "password123", 0)

        # The function now returns None on failure
        assert result is None

    def test_get_user_found(self, monkeypatch):
        """Test retrieving a user that exists."""
        mock_user = {"id": 1, "name": "Test User"}
        monkeypatch.setattr(db, "query", lambda *args: [mock_user])

        user = users.get_user(1)

        assert user == mock_user

    def test_get_user_not_found(self, monkeypatch):
        """Test retrieving a user that does not exist."""
        monkeypatch.setattr(db, "query", lambda *args: [])

        user = users.get_user(999)

        assert user is None

    def test_get_all_users_no_filters(self, monkeypatch):
        """Test get_all_users with no filters."""
        mock_query = MagicMock(return_value=[])
        monkeypatch.setattr(db, "query", mock_query)

        users.get_all_users()

        expected_query = "SELECT * FROM users WHERE 1=1 ORDER BY id ASC"
        mock_query.assert_called_with(expected_query, [])

    def test_get_all_users_with_all_filters(self, monkeypatch):
        """Test get_all_users with all available filters."""
        mock_query = MagicMock(return_value=[])
        monkeypatch.setattr(db, "query", mock_query)

        users.get_all_users(limit=10, offset=5, name_search="Admin",
                            username_search="admin@test.com", super_user="1")

        expected_query = ("SELECT * FROM users WHERE 1=1 AND name LIKE ? AND "
                          "username LIKE ? AND super_user = ? ORDER BY id "
                          "ASC LIMIT ? OFFSET ?")
        expected_params = ["%Admin%", "%admin@test.com%", 1, 10, 5]
        mock_query.assert_called_with(expected_query, expected_params)

    def test_get_user_count_success(self, monkeypatch):
        """Test get_user_count when users exist."""
        monkeypatch.setattr(db, "query", lambda *args: [[5]])

        count = users.get_user_count()

        assert count == 5

    def test_get_user_count_no_users(self, monkeypatch):
        """Test get_user_count when no users exist."""
        monkeypatch.setattr(db, "query", lambda *args: [])

        count = users.get_user_count()

        assert count == 0

    def test_get_user_count_with_filters(self, monkeypatch):
        """Test get_user_count with filters applied."""
        mock_query = MagicMock(return_value=[[1]])
        monkeypatch.setattr(db, "query", mock_query)

        users.get_user_count(name_search="Test", super_user="0")

        expected_query = ("SELECT COUNT(*) FROM users WHERE 1=1 AND "
                          "name LIKE ? AND super_user = ?")
        expected_params = ["%Test%", 0]
        mock_query.assert_called_with(expected_query, expected_params)

    def test_get_super_user_count(self, monkeypatch):
        """Test get_super_user_count."""
        monkeypatch.setattr(db, "query", lambda *args: [[2]])

        count = users.get_super_user_count()

        assert count == 2

    def test_update_user(self, monkeypatch):
        """Test the update_user function."""
        mock_execute = MagicMock()
        monkeypatch.setattr(db, "execute", mock_execute)

        users.update_user(1, "New Name", "new@email.com", 1)

        # Update the query to match the exact formatting in users.py
        expected_query = ("UPDATE users SET name = ?, username = ?, "
                          "super_user = ?\n                WHERE id = ?")
        expected_params = ["New Name", "new@email.com", 1, 1]
        mock_execute.assert_called_with(expected_query, expected_params)

    def test_update_user_name(self, monkeypatch):
        """Test the update_user_name function."""
        mock_execute = MagicMock()
        monkeypatch.setattr(db, "execute", mock_execute)

        users.update_user_name(1, "Just The Name")

        mock_execute.assert_called_with(
            "UPDATE users SET name = ? WHERE id = ?", ["Just The Name", 1])

    def test_update_user_password(self, monkeypatch):
        """Test the update_user_password function."""
        mock_execute = MagicMock()
        monkeypatch.setattr(db, "execute", mock_execute)

        users.update_user_password(1, "new_password")

        assert mock_execute.call_args[0][0] == ("UPDATE users SET "
                                                "password_hash = ? WHERE "
                                                "id = ?")
        assert mock_execute.call_args[0][1][1] == 1
        # Check that the password was hashed using the new default method
        assert mock_execute.call_args[0][1][0].startswith("scrypt:")

    def test_delete_user(self, monkeypatch):
        """Test the delete_user function."""
        mock_execute = MagicMock()
        monkeypatch.setattr(db, "execute", mock_execute)

        users.delete_user(1)

        mock_execute.assert_called_with("DELETE FROM users WHERE id = ?", [1])

    def test_get_user_count_with_username_search(self, monkeypatch):
        """Test get_user_count with username_search filter."""
        mock_query = MagicMock(return_value=[[3]])
        monkeypatch.setattr(db, "query", mock_query)

        users.get_user_count(username_search="testuser")

        expected_query = ("SELECT COUNT(*) FROM users WHERE 1=1 AND "
                          "username LIKE ?")
        expected_params = ["%testuser%"]
        mock_query.assert_called_with(expected_query, expected_params)

    def test_is_super_user(self, monkeypatch):
        """Test is_super_user for a super user."""
        monkeypatch.setattr(db, "query", lambda *args: [{"super_user": 1}])
        assert users.is_super_user(1) is True

    def test_is_not_super_user(self, monkeypatch):
        """Test is_super_user for a regular user."""
        monkeypatch.setattr(db, "query", lambda *args: [{"super_user": 0}])
        assert users.is_super_user(1) is False

    def test_is_super_user_not_found(self, monkeypatch):
        """Test is_super_user for a non-existent user."""
        monkeypatch.setattr(db, "query", lambda *args: [])
        assert users.is_super_user(999) is False

    @patch('users.check_password_hash')
    def test_check_login_success(self, mock_check_hash, monkeypatch):
        """Test successful login."""
        mock_check_hash.return_value = True
        mock_user = {"id": 1, "password_hash": "hashed_password"}
        monkeypatch.setattr(db, "query", lambda *args: [mock_user])

        user_id = users.check_login("test@example.com", "password123")

        assert user_id == 1
        mock_check_hash.assert_called_with("hashed_password", "password123")

    @patch('users.check_password_hash')
    def test_check_login_wrong_password(self, mock_check_hash, monkeypatch):
        """Test login with a wrong password."""
        mock_check_hash.return_value = False
        mock_user = {"id": 1, "password_hash": "hashed_password"}
        monkeypatch.setattr(db, "query", lambda *args: [mock_user])

        user_id = users.check_login("test@example.com", "wrong_password")

        assert user_id is None

    def test_check_login_user_not_found(self, monkeypatch):
        """Test login with a non-existent username."""
        monkeypatch.setattr(db, "query", lambda *args: [])

        user_id = users.check_login("nouser@example.com", "password123")

        assert user_id is None
