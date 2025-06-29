"""Tests for admin user management features."""

import pytest
import sqlite3
import users


class TestAdminUserAccess:
    """Tests access control for the admin user management routes."""

    def test_delete_user_forbidden(self, client):
        """Test that non-admins cannot delete users."""
        response = client.post('/admin/users/delete/1',
                               data={'csrf_token': 'test_token'})
        assert response.status_code == 403

    def test_edit_user_forbidden(self, client):
        """Test that non-admins cannot access the edit user page."""
        response = client.get('/admin/users/edit/1', follow_redirects=True)
        assert response.status_code == 403

    def test_new_user_forbidden(self, client):
        """Test that non-admins cannot access the new user page."""
        response = client.get('/admin/users/new')
        assert response.status_code == 403

    def test_admin_users_route_without_super_user(self, client):
        """Test that non-admins are forbidden from the admin users page."""
        response = client.get('/admin/users')
        assert response.status_code == 403

    def test_admin_users_new_with_super_user(self, client):
        """Test that admins can access the new user page."""
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/users/new')
        assert response.status_code == 200

    def test_admin_create_user_without_super_user(self, client):
        """Test that a non-admin cannot create a user."""
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': 'Name',
                  'username': 'test@example.com', 'password': 'password123'}
        )
        assert response.status_code == 403

    def test_admin_users_update_without_super_user(self, app, client):
        """Test that a non-admin cannot update a user."""
        with app.app_context():
            update_user_id = users.create_user(
                'UpdateMe5', 'updateme5@example.com', 'password123', 0)
            assert update_user_id is not None

        response = client.post(
            f'/admin/users/update/{update_user_id}',
            data={'name': 'Name', 'username': 'test@example.com'}
        )
        assert response.status_code == 403

    def test_admin_users_delete_without_super_user(self, app, client):
        """Test that a non-admin cannot delete a user."""
        with app.app_context():
            delete_user_id = users.create_user(
                'DeleteMe2', 'deleteme2@example.com', 'password123', 0)
            assert delete_user_id is not None

        # No super_user in session
        response = client.post(
            f'/admin/users/delete/{delete_user_id}',
            data={'csrf_token': 'test_token'})
        assert response.status_code == 403


class TestAdminUserActions:
    """Tests for user creation, updating, and deletion by an admin."""

    @pytest.fixture(autouse=True)
    def admin_session(self, client):
        """Fixture to automatically log in as a superuser for all tests."""
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'

    def test_admin_users_with_filters(self, client, monkeypatch):
        """Test the search filters on the admin users page."""
        monkeypatch.setattr("users.get_all_users", lambda **kwargs: [])
        monkeypatch.setattr("users.get_user_count", lambda **kwargs: 0)
        response = client.get(
            '/admin/users?name_search=Admin&username_search=admin@test.com'
            '&super_user=1')
        assert response.status_code == 200
        assert b'value="Admin"' in response.data
        assert b'value="admin@test.com"' in response.data
        assert ('<option value="1" selected>Kyllä'
                '</option>') in response.get_data(as_text=True)

    def test_create_user_success(self, client, monkeypatch):
        """Test successful user creation."""
        monkeypatch.setattr("users.create_user", lambda *a, **kw: True)
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': 'Test',
                  'username': 'test@example.com', 'password': 'password123'},
            follow_redirects=True
        )
        assert b'Uusi k\xc3\xa4ytt\xc3\xa4j\xc3\xa4 on luotu' in response.data

    def test_create_user_missing_fields(self, client):
        """Test user creation failure with missing fields."""
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': '',
                  'username': '', 'password': ''},
            follow_redirects=True
        )
        assert b'Kaikki kent' in response.data

    def test_create_user_invalid_email(self, client):
        """Test user creation failure with an invalid email."""
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': 'Test',
                  'username': 'notanemail', 'password': 'password123'},
            follow_redirects=True
        )
        assert (b'S\xc3\xa4hk\xc3\xb6postiosoite ei ole '
                b'kelvollinen') in response.data

    def test_create_user_duplicate_username(self, client, monkeypatch):
        """Test user creation failure with a duplicate username."""
        monkeypatch.setattr("users.create_user", lambda *a, **kw: False)
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': 'Test',
                  'username': 'dupe@test.com', 'password': 'password123'},
            follow_redirects=True
        )
        assert (b'K\xc3\xa4ytt\xc3\xa4j\xc3\xa4nimi on jo '
                b'k\xc3\xa4yt\xc3\xb6ss\xc3\xa4') in response.data

    def test_delete_user_not_found(self, client, monkeypatch):
        """Test that deleting a non-existent user shows a flash message."""
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.get_user", lambda uid: None)
        response = client.post(
            '/admin/users/delete/999', data={'csrf_token': 'test_token'},
            follow_redirects=True)
        assert (b'K\xc3\xa4ytt\xc3\xa4j\xc3\xa4\xc3\xa4 ei '
                b'l\xc3\xb6ytynyt') in response.data

    # --- 501-502: delete_user, super user ---
    def test_delete_super_user(self, client, monkeypatch):
        """Test that deleting a super user is not allowed."""
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.get_user", lambda uid: {
                            'id': 2, 'name': 'Super',
                            'username': 'super@example.com', 'super_user': 1})
        response = client.post(
            '/admin/users/delete/2', data={'csrf_token': 'test_token'},
            follow_redirects=True)
        assert (b'P\xc3\xa4\xc3\xa4k\xc3\xa4ytt\xc3\xa4ji\xc3\xa4 '
                b'ei voi poistaa') in response.data

    # --- 508-511: delete_user, generic Exception ---
    def test_delete_user_generic_exception(self, client, monkeypatch):
        """Test generic exception handling during user deletion."""
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.get_user", lambda uid: {
                            'id': 3, 'name': 'User',
                            'username': 'user@example.com', 'super_user': 0})
        monkeypatch.setattr("users.delete_user", lambda uid: (
            _ for _ in ()).throw(sqlite3.Error("fail")))
        response = client.post(
            '/admin/users/delete/3', data={'csrf_token': 'test_token'},
            follow_redirects=True)
        assert (b'K\xc3\xa4ytt\xc3\xa4j\xc3\xa4\xc3\xa4 ei voitu '
                b'poistaa') in response.data

    # --- 522-524: new_entry, missing fields POST ---
    def test_new_entry_post_missing_fields(self, client, monkeypatch):
        """Test creating a new entry with missing fields."""
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("sql.get_all_contests", lambda: [
                            {'id': 1, 'title': 'Test Contest'}])
        monkeypatch.setattr("users.get_all_users", lambda: [
                            {'id': 1, 'name': 'Test User',
                             'username': 'test@user.com'}])
        response = client.post(
            '/admin/entries/new',
            data={'csrf_token': 'test_token',
                  'contest_id': '', 'user_id': '', 'entry': ''},
            follow_redirects=True
        )
        assert b'Kaikki pakolliset kent' in response.data
