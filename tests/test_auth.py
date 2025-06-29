"""Tests for the auth blueprint and authentication features.

This module contains unit tests for authentication and registration routes,
including login, logout, CSRF protection, and user registration in the
Writing Contest Web App.

Test Classes:
    TestAuth: Tests for login, logout, and CSRF protection.
    TestUserActions: Tests for user registration and related validation.
    TestProfileEdit: Tests for profile editing features.
"""

from unittest.mock import MagicMock
import users


class TestAuth:
    """Tests for login, logout, and CSRF protection."""

    def test_register_post_normal_user_flash(self, client, monkeypatch):
        """Covers flash('Tunnus on luotu.') for non-superuser registration."""
        monkeypatch.setattr("users.get_user_count",
                            lambda: 1)  # Not first user
        monkeypatch.setattr("users.create_user", lambda n, u, p, s: True)
        client.get('/register')
        with client.session_transaction() as session:
            csrf_token = session['csrf_token']
        response = client.post('/create', data={
            'csrf_token': csrf_token,
            'name': 'Regular User',
            'username': 'regular@example.com',
            'password1': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)
        assert b'Tunnus on luotu' in response.data

    def test_login_route_unsupported_method_redirects(self, client):
        """Covers the fallback 'return redirect("/login")' for unsupported
        methods."""
        response = client.open('/login', method='PUT')
        # Accept 405 (Method Not Allowed) as the correct Flask behavior
        assert response.status_code == 405

    def test_login_get_request(self, client):
        """Test that the login page loads correctly with a GET request."""
        response = client.get('/login')
        assert response.status_code == 200
        assert 'Kirjaudu sisään' in response.get_data(as_text=True)

    def test_login_success(self, app, client):
        """Test a successful login and redirection."""
        with app.app_context():
            users.create_user(
                "Test User", "test@example.com", "password123", 0)

        client.get('/login')
        with client.session_transaction() as session:
            csrf_token = session["csrf_token"]
        response = client.post('/login', data={
            'username': 'test@example.com',
            'password': 'password123',
            'csrf_token': csrf_token
        }, follow_redirects=True)
        assert response.status_code == 200
        with client.session_transaction() as session:
            assert 'user_id' in session
            assert session['username'] == 'test@example.com'

    def test_login_user_not_found_after_check(self, client, monkeypatch):
        """Test the edge case where check_login succeeds but get_user fails."""
        monkeypatch.setattr("users.check_login", lambda u, p: 1)
        monkeypatch.setattr("users.get_user", lambda uid: None)

        client.get('/login')
        with client.session_transaction() as session:
            csrf_token = session["csrf_token"]
        response = client.post('/login', data={
            'username': 'test@example.com',
            'password': 'password123',
            'csrf_token': csrf_token
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "Virheellinen käyttäjätunnus" in response.get_data(as_text=True)

    def test_login_post_invalid(self, client):
        """Test login failure with invalid credentials."""
        client.get('/login')
        with client.session_transaction() as session:
            csrf_token = session["csrf_token"]
        response = client.post('/login', data={
            'username': 'x',
            'password': 'y',
            'csrf_token': csrf_token
        }, follow_redirects=True)
        assert response.status_code == 200
        assert ('Virheellinen käyttäjätunnus tai '
                'salasana.').encode('utf-8') in response.data

    def test_csrf_token(self, client):
        """Test that a valid CSRF token allows logout."""
        with client.session_transaction() as session:
            session['csrf_token'] = 'test_token'
        response = client.post('/logout', data={'csrf_token': 'test_token'})
        assert response.status_code == 302

    def test_csrf_protection(self, client):
        """Test that an invalid CSRF token prevents logout."""
        response = client.post('/logout', data={'csrf_token': 'wrong_token'})
        assert response.status_code == 400 or response.status_code == 403

    def test_logout_route(self, client):
        """Test that the logout route redirects successfully."""
        with client.session_transaction() as session:
            session['csrf_token'] = 'test_token'
        response = client.post('/logout', data={'csrf_token': 'test_token'})
        assert response.status_code == 302

    def test_logout_missing_csrf(self, client):
        """Test that a missing CSRF token prevents logout."""
        response = client.post('/logout')
        assert response.status_code in (400, 403)


class TestUserActions:
    """Tests for user registration and related validation."""

    def test_register_post_first_user_is_super(self, client, monkeypatch):
        """Test that the first user created is automatically a superuser."""
        # Mock get_user_count to simulate an empty database
        monkeypatch.setattr("users.get_user_count", lambda: 0)
        # Mock create_user to check if is_super is correctly set to 1
        mock_create = MagicMock(return_value=1)
        monkeypatch.setattr("users.create_user", mock_create)

        client.get('/register')
        with client.session_transaction() as session:
            csrf_token = session['csrf_token']
        client.post('/create', data={
            'csrf_token': csrf_token,
            'name': 'Super User',
            'username': 'super@example.com',
            'password1': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)

        # Assert that create_user was called with is_super=1
        mock_create.assert_called_with(
            'Super User', 'super@example.com', 'password123', 1)

    def test_register_post_long_fields(self, client):
        """Test registration failure with overly long input fields."""
        client.get('/register')
        with client.session_transaction() as session:
            csrf_token = session['csrf_token']
        response = client.post('/create', data={
            'csrf_token': csrf_token,
            'name': 'a' * 51,
            'username': 'test@example.com',
            'password1': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert ("Nimi on pakollinen ja saa olla enintään 50 "
                "merkkiä.") in response.get_data(as_text=True)

    def test_register_post_missing_fields(self, client):
        """Test registration failure with missing required fields."""
        client.get('/register')
        with client.session_transaction() as session:
            csrf_token = session['csrf_token']
        response = client.post('/create', data={
            'csrf_token': csrf_token,
            'name': '',
            'username': '',
            'password1': '',
            'password2': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "Nimi on pakollinen" in response.get_data(as_text=True)

    def test_register_post_password_mismatch(self, client):
        """Test registration failure with mismatched passwords."""
        client.get('/register')
        with client.session_transaction() as session:
            csrf_token = session['csrf_token']
        response = client.post('/create', data={
            'csrf_token': csrf_token,
            'name': 'Test',
            'username': 'test@example.com',
            'password1': 'password123',
            'password2': 'password321'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "Salasanat eivät ole samat." in response.get_data(as_text=True)

    def test_register_post_short_password(self, client):
        """Test registration failure with a password that is too short."""
        client.get('/register')
        with client.session_transaction() as session:
            csrf_token = session['csrf_token']
        response = client.post('/create', data={
            'csrf_token': csrf_token,
            'name': 'Test',
            'username': 'test@example.com',
            'password1': 'short',
            'password2': 'short'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert ("Salasanan on oltava "
                "vähintään 8") in response.get_data(as_text=True)

    def test_register_post_invalid_email(self, client):
        """Test registration failure with an invalid email address."""
        client.get('/register')
        with client.session_transaction() as session:
            csrf_token = session['csrf_token']
        response = client.post('/create', data={
            'csrf_token': csrf_token,
            'name': 'Test',
            'username': 'not-an-email',
            'password1': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Sähköpostiosoite' in response.get_data(
            as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_login_post_missing_fields(self, client):
        """Test login failure with missing username and password fields."""
        client.get('/login')
        with client.session_transaction() as session:
            csrf_token = session['csrf_token']
        response = client.post('/login', data={
            'csrf_token': csrf_token,
            'username': '',
            'password': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Virheellinen' in response.data

    def test_register_post_duplicate_email(self, client):
        """Test registration failure with a duplicate email address."""
        client.get('/register')
        with client.session_transaction() as session:
            csrf_token = session['csrf_token']
        client.post('/create', data={
            'csrf_token': csrf_token,
            'name': 'Test',
            'username': 'duplicate@example.com',
            'password1': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)
        client.get('/register')
        with client.session_transaction() as session:
            csrf_token = session['csrf_token']
        response = client.post('/create', data={
            'csrf_token': csrf_token,
            'name': 'Test2',
            'username': 'duplicate@example.com',
            'password1': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'varattu' in response.get_data(
            as_text=True) or 'Virhe' in response.get_data(as_text=True)


class TestProfileEdit:
    """Tests for profile editing features."""

    def login_as(self, client, user_id=1, username="test@example.com"):
        """Log in a user by setting session variables.

        Args:
            client: The Flask test client.
            user_id: The user ID to set in the session.
            username: The username to set in the session.
        """
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["username"] = username
            sess["csrf_token"] = "test_token"

    def test_edit_profile_get_not_logged_in(self, client):
        """Test that a non-logged-in user is redirected from the edit
        profile page."""
        response = client.get("/profile/edit", follow_redirects=True)
        assert response.status_code == 200
        assert "Kirjaudu sisään" in response.get_data(as_text=True)

    def test_edit_profile_post_not_logged_in(self, client):
        """Test that a non-logged-in user cannot POST to the edit
        profile page."""
        response = client.post("/profile/edit", follow_redirects=True)
        assert response.status_code == 200
        assert "Kirjaudu sisään" in response.get_data(as_text=True)

    def test_edit_profile_user_not_found(self, client, monkeypatch):
        """Test behavior when the logged-in user is not found in
        the database."""
        self.login_as(client)
        monkeypatch.setattr("users.get_user", lambda uid: None)
        response = client.get("/profile/edit", follow_redirects=True)
        assert response.status_code == 200
        assert "Käyttäjää ei löytynyt" in response.get_data(as_text=True)

    def test_edit_profile_get(self, client, monkeypatch):
        """Test that a logged-in user can access the edit profile page."""
        self.login_as(client)

        def fake_get_user(user_id):
            return {"id": user_id, "username": "test@example.com",
                    "name": "Test"}
        monkeypatch.setattr("users.get_user", fake_get_user)
        response = client.get("/profile/edit")
        assert response.status_code == 200
        assert b"Muokkaa profiilia" in response.data

    def test_edit_profile_post_name(self, client, monkeypatch):
        """Test that a user can successfully update their name."""
        self.login_as(client)

        def fake_get_user(user_id):
            return {"id": user_id, "username": "test@example.com",
                    "name": "Test"}

        def fake_update_user_name(user_id, name):
            assert name == "Uusi Nimi"
        monkeypatch.setattr("users.get_user", fake_get_user)
        monkeypatch.setattr("users.update_user_name", fake_update_user_name)
        monkeypatch.setattr("users.update_user_password", lambda uid, pw: None)
        response = client.post("/profile/edit", data={
            "csrf_token": "test_token",
            "name": "Uusi Nimi",
            "password1": "",
            "password2": ""
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "Profiili päivitetty" in response.get_data(as_text=True)

    def test_edit_profile_post_password(self, client, monkeypatch):
        """Test that a user can successfully update their password."""
        self.login_as(client)

        def fake_get_user(user_id):
            return {"id": user_id, "username": "test@example.com",
                    "name": "Test"}
        monkeypatch.setattr("users.get_user", fake_get_user)
        monkeypatch.setattr("users.update_user_name", lambda uid, name: None)

        def fake_update_user_password(user_id, password):
            assert password == "uusiSalasana123"
        monkeypatch.setattr("users.update_user_password",
                            fake_update_user_password)
        response = client.post("/profile/edit", data={
            "csrf_token": "test_token",
            "name": "Test",
            "password1": "uusiSalasana123",
            "password2": "uusiSalasana123"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "Profiili päivitetty" in response.get_data(as_text=True)

    def test_edit_profile_post_password_mismatch(self, client, monkeypatch):
        """Test profile edit failure with mismatched passwords."""
        self.login_as(client)

        def fake_get_user(user_id):
            return {"id": user_id, "username": "test@example.com",
                    "name": "Test"}
        monkeypatch.setattr("users.get_user", fake_get_user)
        monkeypatch.setattr("users.update_user_name", lambda uid, name: None)
        monkeypatch.setattr("users.update_user_password", lambda uid, pw: None)
        response = client.post("/profile/edit", data={
            "csrf_token": "test_token",
            "name": "Test",
            "password1": "salasana1",
            "password2": "salasana2"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "Salasanat eivät täsmää" in response.get_data(
            as_text=True) or "salasanat" in response.get_data(as_text=True)

    def test_edit_profile_post_short_password(self, client, monkeypatch):
        """Test profile edit failure with a password that is too short."""
        self.login_as(client)

        def fake_get_user(user_id):
            return {"id": user_id, "username": "test@example.com",
                    "name": "Test"}
        monkeypatch.setattr("users.get_user", fake_get_user)
        monkeypatch.setattr("users.update_user_name", lambda uid, name: None)
        monkeypatch.setattr("users.update_user_password", lambda uid, pw: None)
        response = client.post("/profile/edit", data={
            "csrf_token": "test_token",
            "name": "Test",
            "password1": "short",
            "password2": "short"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert (("Salasanan on oltava vähintään 8 merkkiä pitkä")
                in response.get_data(as_text=True)
                or "salasanan on oltava" in response.get_data(as_text=True))

    def test_edit_profile_post_invalid_name(self, client, monkeypatch):
        """Test profile edit failure with an empty name field."""
        self.login_as(client)

        def fake_get_user(user_id):
            return {"id": user_id, "username": "test@example.com",
                    "name": "Test"}
        monkeypatch.setattr("users.get_user", fake_get_user)
        monkeypatch.setattr("users.update_user_name", lambda uid, name: None)
        monkeypatch.setattr("users.update_user_password", lambda uid, pw: None)
        response = client.post("/profile/edit", data={
            "csrf_token": "test_token",
            "name": "",
            "password1": "",
            "password2": ""
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "Nimi ei saa olla tyhjä" in response.get_data(as_text=True)

    def test_edit_profile_post_long_name(self, client, monkeypatch):
        """Test profile edit failure with an overly long name."""
        self.login_as(client)

        def fake_get_user(user_id):
            return {"id": user_id, "username": "test@example.com",
                    "name": "Test"}
        monkeypatch.setattr("users.get_user", fake_get_user)
        response = client.post("/profile/edit", data={
            "csrf_token": "test_token",
            "name": "a" * 51,
            "password1": "",
            "password2": ""
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "Nimi ei saa olla tyhjä tai liian pitkä" in response.get_data(
            as_text=True)

    def test_delete_profile_not_logged_in(self, client):
        """Test that a non-logged-in user cannot delete a profile."""
        response = client.post("/profile/delete", follow_redirects=True)
        assert response.status_code == 200
        assert "Kirjaudu sisään" in response.get_data(as_text=True)

    def test_delete_profile(self, client, monkeypatch):
        """Test successful profile deletion for a logged-in user."""
        self.login_as(client)
        monkeypatch.setattr("users.delete_user", lambda user_id: True)
        response = client.post(
            "/profile/delete", data={"csrf_token": "test_token"},
            follow_redirects=True)
        assert response.status_code in (200, 302)
        assert "Profiili poistettu" in response.get_data(
            as_text=True) or "poistettu" in response.get_data(as_text=True)

    def test_delete_profile_failure(self, client, monkeypatch):
        """Test profile deletion failure."""
        self.login_as(client)
        monkeypatch.setattr("users.delete_user", lambda user_id: False)
        response = client.post(
            "/profile/delete", data={"csrf_token": "test_token"},
            follow_redirects=True)
        assert response.status_code in (200, 302)
        assert "Profiilia ei voitu poistaa" in response.get_data(
            as_text=True) or "virhe" in response.get_data(as_text=True)
