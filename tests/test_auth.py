"""Tests for the auth blueprint and authentication features.

This module contains unit tests for authentication and registration routes,
including login, logout, CSRF protection, and user registration in the
Writing Contest Web App.

Test Classes:
    TestAuth: Tests for login, logout, and CSRF protection.
    TestUserActions: Tests for user registration and related validation.
    TestProfileEdit: Tests for profile editing features.
"""


class TestAuth:
    def test_login_post_invalid(self, client):
        client.get('/login')
        with client.session_transaction() as session:
            csrf_token = session["csrf_token"]
        response = client.post('/login', data={
            'username': 'x',
            'password': 'y',
            'csrf_token': csrf_token
        })
        assert response.status_code in (200, 403)
        if response.status_code == 200:
            assert 'Virhe'.encode('utf-8') in response.data

    def test_csrf_token(self, client):
        with client.session_transaction() as session:
            session['csrf_token'] = 'test_token'
        response = client.post('/logout', data={'csrf_token': 'test_token'})
        assert response.status_code == 302

    def test_csrf_protection(self, client):
        response = client.post('/logout', data={'csrf_token': 'wrong_token'})
        assert response.status_code == 400 or response.status_code == 403

    def test_logout_route(self, client):
        with client.session_transaction() as session:
            session['csrf_token'] = 'test_token'
        response = client.post('/logout', data={'csrf_token': 'test_token'})
        assert response.status_code == 302

    def test_logout_missing_csrf(self, client):
        response = client.post('/logout')
        assert response.status_code in (400, 403)


class TestUserActions:
    def test_register_post_missing_fields(self, client):
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
        assert response.status_code in (302, 200)
        assert b'Virhe' in response.data or b'error' in response.data.lower()

    def test_register_post_password_mismatch(self, client):
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
        assert 'salasanat' in response.get_data(as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_register_post_short_password(self, client):
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
        assert 'salasanan on oltava' in response.get_data(as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_register_post_invalid_email(self, client):
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
        assert 'Sähköpostiosoite' in response.get_data(as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_login_post_missing_fields(self, client):
        client.get('/login')
        with client.session_transaction() as session:
            csrf_token = session['csrf_token']
        response = client.post('/login', data={
            'csrf_token': csrf_token,
            'username': '',
            'password': ''
        })
        assert response.status_code in (200, 403)
        assert b'Virhe' in response.data or 'Väärä'.encode('utf-8') in response.data or b'error' in response.data.lower()

    def test_register_post_duplicate_email(self, client):
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
        assert 'varattu' in response.get_data(as_text=True) or 'Virhe' in response.get_data(as_text=True)


class TestProfileEdit:
    def login_as(self, client, user_id=1, username="test@example.com"):
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["username"] = username
            sess["csrf_token"] = "test_token"

    def test_edit_profile_get(self, client, monkeypatch):
        self.login_as(client)

        def fake_get_user(user_id):
            return {"id": user_id, "username": "test@example.com", "name": "Test"}
        monkeypatch.setattr("users.get_user", fake_get_user)
        response = client.get("/profile/edit")
        assert response.status_code == 200
        assert b"Muokkaa profiilia" in response.data

    def test_edit_profile_post_name(self, client, monkeypatch):
        self.login_as(client)

        def fake_get_user(user_id):
            return {"id": user_id, "username": "test@example.com", "name": "Test"}

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
        self.login_as(client)

        def fake_get_user(user_id):
            return {"id": user_id, "username": "test@example.com", "name": "Test"}
        monkeypatch.setattr("users.get_user", fake_get_user)
        monkeypatch.setattr("users.update_user_name", lambda uid, name: None)

        def fake_update_user_password(user_id, password):
            assert password == "uusiSalasana123"
        monkeypatch.setattr("users.update_user_password", fake_update_user_password)
        response = client.post("/profile/edit", data={
            "csrf_token": "test_token",
            "name": "Test",
            "password1": "uusiSalasana123",
            "password2": "uusiSalasana123"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "Profiili päivitetty" in response.get_data(as_text=True)

    def test_edit_profile_post_password_mismatch(self, client, monkeypatch):
        self.login_as(client)

        def fake_get_user(user_id):
            return {"id": user_id, "username": "test@example.com", "name": "Test"}
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
        assert "Salasanat eivät täsmää" in response.get_data(as_text=True) or "salasanat" in response.get_data(as_text=True)

    def test_edit_profile_post_short_password(self, client, monkeypatch):
        self.login_as(client)

        def fake_get_user(user_id):
            return {"id": user_id, "username": "test@example.com", "name": "Test"}
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
        assert "Salasanan on oltava vähintään 8 merkkiä pitkä" in response.get_data(as_text=True) or "salasanan on oltava" in response.get_data(as_text=True)

    def test_edit_profile_post_invalid_name(self, client, monkeypatch):
        self.login_as(client)

        def fake_get_user(user_id):
            return {"id": user_id, "username": "test@example.com", "name": "Test"}
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
        assert "Nimi ei saa olla tyhjä" in response.get_data(as_text=True) or "Nimi ei saa olla" in response.get_data(as_text=True)

    def test_delete_profile(self, client, monkeypatch):
        self.login_as(client)
        monkeypatch.setattr("users.delete_user", lambda user_id: True)
        response = client.post("/profile/delete", data={"csrf_token": "test_token"}, follow_redirects=True)
        assert response.status_code in (200, 302)
        assert "Profiili poistettu" in response.get_data(as_text=True) or "poistettu" in response.get_data(as_text=True)
