"""Tests for the auth blueprint and authentication features.

This module contains unit tests for authentication and registration routes,
including login, logout, CSRF protection, and user registration in the
Writing Contest Web App.

Test Classes:
    TestAuth: Tests for login, logout, and CSRF protection.
    TestUserActions: Tests for user registration and related validation.
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
