import pytest
from app import (app, sanitize_input, is_valid_email, format_date,
                 format_text, total_pages)


@pytest.fixture
def client():
    """Fixture to set up the test client."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """Test the index route."""
    response = client.get('/')
    assert response.status_code == 200
    assert 'Tervetuloa!'.encode('utf-8') in response.data


def test_register_route(client):
    """Test the register route."""
    response = client.get('/register')
    assert response.status_code == 200
    assert 'Rekisteröidy'.encode('utf-8') in response.data


def test_login_get_route(client):
    """Test the login route with GET method."""
    response = client.get('/login')
    assert response.status_code == 200
    assert 'Kirjaudu sisään'.encode('utf-8') in response.data


def test_register_get(client):
    response = client.get('/register')
    assert response.status_code == 200


def test_login_post_invalid(client):
    # Trigger before_request to set csrf_token
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


def test_sanitize_input():
    """Test sanitizing input."""
    assert sanitize_input('<script>alert("test")</script>') == 'alert("test")'
    assert sanitize_input('  clean text  ') == 'clean text'
    assert sanitize_input(123) == ''


def test_sanitize_input_script():
    assert sanitize_input('<script>alert(1)</script>') == 'alert(1)'


def test_sanitize_input_event_handler():
    assert sanitize_input('<div onclick="evil()">test</div>') == 'test'


def test_sanitize_input_non_string():
    assert sanitize_input(None) == ''
    assert sanitize_input(123) == ''


def test_is_valid_email():
    """Test email validation."""
    assert is_valid_email('test@example.com')
    assert not is_valid_email('invalid-email')
    assert not is_valid_email('test@.com')


def test_format_date():
    """Test date formatting."""
    assert format_date('2023-10-05') == '5.10.2023'
    assert format_date('2024-05-29') == '29.5.2024'


def test_format_date_invalid():
    """Test invalid date formatting."""
    assert format_date('not-a-date') == 'not-a-date'


def test_format_text():
    """Test text formatting."""
    assert format_text('Hello\nWorld') == 'Hello<br />World'
    assert format_text('*bold*') == '<strong>bold</strong>'
    assert format_text('_italic_') == '<em>italic</em>'


def test_format_text_with_links():
    text = 'Check this: https://example.com'
    result = format_text(text, links_allowed=True)
    assert '<a href="https://example.com"' in result


def test_csrf_token(client):
    """Test CSRF token presence."""
    with client.session_transaction() as session:
        session['csrf_token'] = 'test_token'
    response = client.post('/logout', data={'csrf_token': 'test_token'})
    assert response.status_code == 302  # Redirect after logout


def test_csrf_protection(client):
    response = client.post('/logout', data={'csrf_token': 'wrong_token'})
    assert response.status_code == 400 or response.status_code == 403


def test_admin_route_without_super_user(client):
    """Test admin route access without super user."""
    response = client.get('/admin')
    assert response.status_code == 403


def test_admin_route_with_super_user(client):
    """Test admin route access with super user."""
    with client.session_transaction() as session:
        session['super_user'] = True
    response = client.get('/admin')
    assert response.status_code == 200
    assert 'Ylläpito'.encode('utf-8') in response.data


def test_logout_route(client):
    """Test logout route."""
    with client.session_transaction() as session:
        session['csrf_token'] = 'test_token'
    response = client.post('/logout', data={'csrf_token': 'test_token'})
    assert response.status_code == 302  # Redirect after logout


def test_total_pages():
    assert total_pages(0, 10) == 0
    assert total_pages(5, 10) == 1
    assert total_pages(20, 10) == 2
    assert total_pages(21, 10) == 3


def test_admin_users_route_without_super_user(client):
    response = client.get('/admin/users')
    assert response.status_code == 403


def test_contest_detail_valid(client):
    response = client.get('/contests/contest/1')
    assert response.status_code in (200, 404)  # 404 if contest doesn't exist


def test_contest_detail_invalid(client):
    response = client.get('/contests/contest/999999')
    assert response.status_code == 404


def test_terms_of_use(client):
    response = client.get('/terms_of_use')
    assert response.status_code == 200


def test_admin_contests_route_with_super_user(client):
    with client.session_transaction() as session:
        session['super_user'] = True
    response = client.get('/admin/contests')
    assert response.status_code == 200


def test_admin_contests_route_without_super_user(client):
    response = client.get('/admin/contests')
    assert response.status_code == 403


def test_admin_users_new_with_super_user(client):
    with client.session_transaction() as session:
        session['super_user'] = True
    response = client.get('/admin/users/new')
    assert response.status_code == 200


def test_admin_users_new_without_super_user(client):
    response = client.get('/admin/users/new')
    assert response.status_code == 403


def test_admin_contests_create_post(client):
    with client.session_transaction() as session:
        session['super_user'] = True
        session['csrf_token'] = 'test_token'
    response = client.post('/admin/contests/create', data={'csrf_token': 'test_token', 'name': 'Test Contest'})
    assert response.status_code in (302, 200, 400)  # Adjust as per your logic


def test_admin_contests_delete_post(client):
    with client.session_transaction() as session:
        session['super_user'] = True
        session['csrf_token'] = 'test_token'
    response = client.post('/admin/contests/delete/1', data={'csrf_token': 'test_token'})
    assert response.status_code in (302, 200, 404)


def test_admin_entries_route_with_super_user(client):
    with client.session_transaction() as session:
        session['super_user'] = True
    response = client.get('/admin/entries')
    assert response.status_code == 200


def test_admin_entries_route_without_super_user(client):
    response = client.get('/admin/entries')
    assert response.status_code == 403


def test_admin_users_edit_with_super_user(client):
    with client.session_transaction() as session:
        session['super_user'] = True
    response = client.get('/admin/users/edit/1')
    assert response.status_code in (200, 404)


def test_admin_users_update_with_super_user(client):
    with client.session_transaction() as session:
        session['super_user'] = True
        session['csrf_token'] = 'test_token'
    response = client.post('/admin/users/update/1', data={
        'csrf_token': 'test_token',
        'username': 'newname',
        'name': 'New Name'  # Add this line
    })
    assert response.status_code in (302, 200, 404)


def test_admin_create_entry_post(client):
    with client.session_transaction() as session:
        session['super_user'] = True
        session['csrf_token'] = 'test_token'
    # You may need to mock sql.create_entry for this test
    response = client.post('/admin/entries/create', data={
        'csrf_token': 'test_token',
        'contest_id': 1,
        'user_id': 1,
        'content': 'Test Content'
    })
    assert response.status_code in (302, 200, 400)


def test_admin_route_forbidden(client):
    response = client.get('/admin')
    assert response.status_code == 403


def test_nonexistent_route(client):
    response = client.get('/thispagedoesnotexist')
    assert response.status_code == 404


def test_admin_edit_entry_with_super_user(client):
    with client.session_transaction() as session:
        session['super_user'] = True
    # Assuming entry with id=1 exists or will 404
    response = client.get('/admin/entries/edit/1')
    assert response.status_code in (200, 404)


def test_admin_edit_entry_without_super_user(client):
    response = client.get('/admin/entries/edit/1')
    assert response.status_code == 403


def test_admin_update_entry_with_super_user(client):
    with client.session_transaction() as session:
        session['super_user'] = True
        session['csrf_token'] = 'test_token'
    # Assuming entry with id=1 exists or will 404
    response = client.post('/admin/entries/update/1', data={
        'csrf_token': 'test_token',
        'contest_id': 1,
        'user_id': 1,
        'title': 'Muokattu otsikko',
        'content': 'Muokattu sisältö'
    })
    assert response.status_code in (302, 200, 404)


def test_admin_update_entry_without_super_user(client):
    response = client.post('/admin/entries/update/1', data={
        'csrf_token': 'test_token',
        'contest_id': 1,
        'user_id': 1,
        'title': 'Muokattu otsikko',
        'content': 'Muokattu sisältö'
    })
    assert response.status_code == 403


def test_admin_delete_entry_with_super_user(client):
    with client.session_transaction() as session:
        session['super_user'] = True
        session['csrf_token'] = 'test_token'
    # Assuming entry with id=1 exists or will 404
    response = client.post('/admin/entries/delete/1', data={'csrf_token': 'test_token'})
    assert response.status_code in (302, 200, 404)


def test_admin_delete_entry_without_super_user(client):
    response = client.post('/admin/entries/delete/1', data={'csrf_token': 'test_token'})
    assert response.status_code == 403


def test_admin_create_entry_missing_fields(client):
    with client.session_transaction() as session:
        session['super_user'] = True
        session['csrf_token'] = 'test_token'
    # Missing title and content
    response = client.post('/admin/entries/create', data={
        'csrf_token': 'test_token',
        'contest_id': 1,
        'user_id': 1
    })
    assert response.status_code in (302, 200, 400)


def test_duplicate_entry_prevention(client):
    with client.session_transaction() as session:
        session['super_user'] = True
        session['csrf_token'] = 'test_token'
    # First entry should succeed
    response1 = client.post('/admin/entries/create', data={
        'csrf_token': 'test_token',
        'contest_id': 1,
        'user_id': 1,
        'entry': 'First entry'
    })
    # Second entry for same user/contest should fail or update, depending on logic
    response2 = client.post('/admin/entries/create', data={
        'csrf_token': 'test_token',
        'contest_id': 1,
        'user_id': 1,
        'entry': 'Duplicate entry'
    })
    assert response2.status_code in (400, 302, 409)
