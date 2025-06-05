"""
Unit tests for the Writing Contest Web App Flask application.

This module contains tests for routes, utility functions, and admin features.
"""

import pytest
from app import (
    app, sanitize_input, is_valid_email, format_date,
    format_text, total_pages
)
import users


@pytest.fixture
def client():
    """Fixture to set up the test client."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    with app.test_client() as client:
        yield client


class TestPublicRoutes:
    def test_index_route(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert 'Tervetuloa!'.encode('utf-8') in response.data

    def test_register_route(self, client):
        response = client.get('/register')
        assert response.status_code == 200
        assert 'Rekisteröidy'.encode('utf-8') in response.data

    def test_login_get_route(self, client):
        response = client.get('/login')
        assert response.status_code == 200
        assert 'Kirjaudu sisään'.encode('utf-8') in response.data

    def test_register_get(self, client):
        response = client.get('/register')
        assert response.status_code == 200

    def test_terms_of_use(self, client):
        response = client.get('/terms_of_use')
        assert response.status_code == 200

    def test_nonexistent_route(self, client):
        response = client.get('/thispagedoesnotexist')
        assert response.status_code == 404


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


class TestUtils:
    def test_sanitize_input(self):
        assert sanitize_input('<script>alert("test")</script>') == 'alert("test")'
        assert sanitize_input('  clean text  ') == 'clean text'
        assert sanitize_input(123) == ''

    def test_sanitize_input_script(self):
        assert sanitize_input('<script>alert(1)</script>') == 'alert(1)'

    def test_sanitize_input_event_handler(self):
        assert sanitize_input('<div onclick="evil()">test</div>') == 'test'

    def test_sanitize_input_non_string(self):
        assert sanitize_input(None) == ''
        assert sanitize_input(123) == ''

    def test_is_valid_email(self):
        assert is_valid_email('test@example.com')
        assert not is_valid_email('invalid-email')
        assert not is_valid_email('test@.com')

    def test_format_date(self):
        assert format_date('2023-10-05') == '5.10.2023'
        assert format_date('2024-05-29') == '29.5.2024'

    def test_format_date_invalid(self):
        assert format_date('not-a-date') == 'not-a-date'

    def test_format_text(self):
        assert format_text('Hello\nWorld') == 'Hello<br />World'
        assert format_text('*bold*') == '<strong>bold</strong>'
        assert format_text('_italic_') == '<em>italic</em>'

    def test_format_text_with_links(self):
        text = 'Check this: https://example.com'
        result = format_text(text, links_allowed=True)
        assert '<a href="https://example.com"' in result

    def test_total_pages(self):
        assert total_pages(0, 10) == 0
        assert total_pages(5, 10) == 1
        assert total_pages(20, 10) == 2
        assert total_pages(21, 10) == 3


class TestAdminRoutes:
    def test_admin_route_without_super_user(self, client):
        response = client.get('/admin')
        assert response.status_code == 403

    def test_admin_route_with_super_user(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin')
        assert response.status_code == 200
        assert 'Ylläpito'.encode('utf-8') in response.data

    def test_admin_users_route_without_super_user(self, client):
        response = client.get('/admin/users')
        assert response.status_code == 403

    def test_admin_users_new_with_super_user(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/users/new')
        assert response.status_code == 200

    def test_admin_users_new_without_super_user(self, client):
        response = client.get('/admin/users/new')
        assert response.status_code == 403

    def test_admin_contests_route_with_super_user(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/contests')
        assert response.status_code == 200

    def test_admin_contests_route_without_super_user(self, client):
        response = client.get('/admin/contests')
        assert response.status_code == 403

    def test_admin_entries_route_with_super_user(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/entries')
        assert response.status_code == 200

    def test_admin_entries_route_without_super_user(self, client):
        response = client.get('/admin/entries')
        assert response.status_code == 403

    def test_admin_route_forbidden(self, client):
        response = client.get('/admin')
        assert response.status_code == 403


class TestContestRoutes:
    def test_contest_detail_valid(self, client):
        response = client.get('/contests/contest/1')
        assert response.status_code in (200, 404)

    def test_contest_detail_invalid(self, client):
        response = client.get('/contests/contest/999999')
        assert response.status_code == 404

    def test_admin_contests_create_post(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/contests/create',
            data={
                'csrf_token': 'test_token',
                'title': 'Test Contest',
                'class_id': 1,
                'short_description': 'Short desc',
                'long_description': 'Long desc',
                'collection_end': '2025-12-31',
                'review_end': '2026-01-31'
            }
        )
        assert response.status_code in (302, 200, 400)

    def test_admin_contests_delete_post(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/contests/delete/1',
            data={'csrf_token': 'test_token'}
        )
        assert response.status_code in (302, 200, 404)

    def test_admin_edit_contest_with_super_user(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/contests/edit/1')
        assert response.status_code in (200, 404)

    def test_admin_edit_contest_without_super_user(self, client):
        response = client.get('/admin/contests/edit/1')
        assert response.status_code == 403

    def test_admin_update_contest_with_super_user(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/contests/update/1',
            data={
                'csrf_token': 'test_token',
                'title': 'Updated Title',
                'class_id': 1,
                'short_description': 'Short desc',
                'long_description': 'Long desc',
                'collection_end': '2025-12-31',
                'review_end': '2026-01-31'
            }
        )
        assert response.status_code in (302, 200, 404)

    def test_admin_update_contest_without_super_user(self, client):
        response = client.post(
            '/admin/contests/update/1',
            data={
                'csrf_token': 'test_token',
                'title': 'Updated Title',
                'class_id': 1,
                'short_description': 'Short desc',
                'long_description': 'Long desc',
                'collection_end': '2025-12-31',
                'review_end': '2026-01-31'
            }
        )
        assert response.status_code == 403

    def test_admin_new_contest_with_super_user(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/contests/new')
        assert response.status_code == 200

    def test_admin_new_contest_without_super_user(self, client):
        response = client.get('/admin/contests/new')
        assert response.status_code == 403

    def test_admin_create_contest_short_description_too_long(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        long_desc = 'a' * 256
        response = client.post(
            '/admin/contests/create',
            data={
                'csrf_token': 'test_token',
                'title': 'Test',
                'class_id': 1,
                'short_description': long_desc,
                'long_description': 'Valid',
                'collection_end': '2025-12-31',
                'review_end': '2026-01-31'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert '255' in response.get_data(as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_admin_create_contest_long_description_too_long(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        long_desc = 'a' * 2001
        response = client.post(
            '/admin/contests/create',
            data={
                'csrf_token': 'test_token',
                'title': 'Test',
                'class_id': 1,
                'short_description': 'Valid',
                'long_description': long_desc,
                'collection_end': '2025-12-31',
                'review_end': '2026-01-31'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert '2000' in response.get_data(as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_admin_create_contest_missing_fields(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/contests/create',
            data={
                'csrf_token': 'test_token',
                'title': '',
                'class_id': 1,
                'short_description': '',
                'long_description': '',
                'collection_end': '',
                'review_end': ''
            },
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_admin_update_contest_short_description_too_long(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        long_desc = 'a' * 256
        response = client.post(
            '/admin/contests/update/1',
            data={
                'csrf_token': 'test_token',
                'title': 'Test',
                'class_id': 1,
                'short_description': long_desc,
                'long_description': 'Valid',
                'collection_end': '2025-12-31',
                'review_end': '2026-01-31'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert '255' in response.get_data(as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_admin_update_contest_long_description_too_long(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        long_desc = 'a' * 2001
        response = client.post(
            '/admin/contests/update/1',
            data={
                'csrf_token': 'test_token',
                'title': 'Test',
                'class_id': 1,
                'short_description': 'Valid',
                'long_description': long_desc,
                'collection_end': '2025-12-31',
                'review_end': '2026-01-31'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert '2000' in response.get_data(as_text=True) or 'Virhe' in response.get_data(as_text=True)


class TestEntryRoutes:
    def test_admin_create_entry_post(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/entries/create',
            data={
                'csrf_token': 'test_token',
                'contest_id': 1,
                'user_id': 1,
                'content': 'Test Content'
            }
        )
        assert response.status_code in (302, 200, 400)

    def test_admin_create_entry_missing_fields(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/entries/create',
            data={
                'csrf_token': 'test_token',
                'contest_id': 1,
                'user_id': 1
            }
        )
        assert response.status_code in (302, 200, 400)

    def test_admin_create_entry_missing_fields_flash(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/entries/create',
            data={
                'csrf_token': 'test_token',
                'contest_id': '',
                'user_id': '',
                'entry': ''
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert 'Kaikki pakolliset kentät on täytettävä.' in response.get_data(as_text=True)

    def test_admin_edit_entry_with_super_user(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/entries/edit/1')
        assert response.status_code in (200, 404)

    def test_admin_edit_entry_without_super_user(self, client):
        response = client.get('/admin/entries/edit/1')
        assert response.status_code == 403

    def test_admin_update_entry_with_super_user(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/entries/update/1',
            data={
                'csrf_token': 'test_token',
                'contest_id': 1,
                'user_id': 1,
                'entry': 'Updated content'
            }
        )
        assert response.status_code in (302, 200, 404)

    def test_admin_update_entry_without_super_user(self, client):
        response = client.post(
            '/admin/entries/update/1',
            data={
                'csrf_token': 'test_token',
                'contest_id': 1,
                'user_id': 1,
                'entry': 'Updated content'
            }
        )
        assert response.status_code == 403

    def test_admin_delete_entry_with_super_user(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post('/admin/entries/delete/1', data={'csrf_token': 'test_token'})
        assert response.status_code in (302, 200, 404)

    def test_admin_delete_entry_without_super_user(self, client):
        response = client.post('/admin/entries/delete/1', data={'csrf_token': 'test_token'})
        assert response.status_code == 403

    def test_admin_update_entry_invalid_id(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/entries/update/999999',
            data={
                'csrf_token': 'test_token',
                'contest_id': 1,
                'user_id': 1,
                'entry': 'Updated content'
            }
        )
        assert response.status_code in (302, 404, 400)

    def test_admin_delete_entry_invalid_id(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post('/admin/entries/delete/999999', data={'csrf_token': 'test_token'})
        assert response.status_code in (302, 200)

    def test_duplicate_entry_prevention(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response1 = client.post(
            '/admin/entries/create',
            data={
                'csrf_token': 'test_token',
                'contest_id': 1,
                'user_id': 1,
                'entry': 'First entry'
            }
        )
        assert response1.status_code in (200, 302)
        response2 = client.post(
            '/admin/entries/create',
            data={
                'csrf_token': 'test_token',
                'contest_id': 1,
                'user_id': 1,
                'entry': 'Duplicate entry'
            }
        )
        assert response2.status_code in (400, 302, 409)


class TestUserRoutes:
    def test_admin_users_edit_with_super_user(self, client):
        from app import app
        with app.app_context():
            # Create a user to edit
            users.create_user('EditMe', 'editme@example.com', 'password123', 0)
            user = users.get_all_users()
            edit_user_id = None
            for u in user:
                if u['username'] == 'editme@example.com':
                    edit_user_id = u['id']
                    break
            assert edit_user_id is not None
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get(f'/admin/users/edit/{edit_user_id}')
        assert response.status_code in (200, 302, 404)

    def test_admin_users_edit_with_super_user_valid_and_invalid(self, client):
        from app import app
        with app.app_context():
            # Create a user to edit
            users.create_user('EditMe2', 'editme2@example.com', 'password123', 0)
            user = users.get_all_users()
            edit_user_id = None
            for u in user:
                if u['username'] == 'editme2@example.com':
                    edit_user_id = u['id']
                    break
            assert edit_user_id is not None
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get(f'/admin/users/edit/{edit_user_id}')
        assert response.status_code in (200, 302, 404)
        response = client.get('/admin/users/edit/999999')
        assert response.status_code in (302, 404)

    def test_admin_users_update_with_super_user(self, client):
        from app import app
        with app.app_context():
            # Create a user to update
            users.create_user('UpdateMe', 'updateme@example.com', 'password123', 0)
            user = users.get_all_users()
            update_user_id = None
            for u in user:
                if u['username'] == 'updateme@example.com':
                    update_user_id = u['id']
                    break
            assert update_user_id is not None
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            f'/admin/users/update/{update_user_id}',
            data={
                'csrf_token': 'test_token',
                'username': 'newname@example.com',
                'name': 'New Name'
            }
        )
        assert response.status_code in (302, 200, 404)

    def test_admin_users_update_missing_fields(self, client):
        from app import app
        with app.app_context():
            # Create a user to update
            users.create_user('UpdateMe2', 'updateme2@example.com', 'password123', 0)
            user = users.get_all_users()
            update_user_id = None
            for u in user:
                if u['username'] == 'updateme2@example.com':
                    update_user_id = u['id']
                    break
            assert update_user_id is not None
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.post(
            f'/admin/users/update/{update_user_id}',
            data={'name': '', 'username': ''}
        )
        assert response.status_code in (302, 200, 400)

    def test_admin_users_update_invalid_email(self, client):
        from app import app
        with app.app_context():
            # Create a user to update
            users.create_user('UpdateMe3', 'updateme3@example.com', 'password123', 0)
            user = users.get_all_users()
            update_user_id = None
            for u in user:
                if u['username'] == 'updateme3@example.com':
                    update_user_id = u['id']
                    break
            assert update_user_id is not None
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.post(
            f'/admin/users/update/{update_user_id}',
            data={'name': 'Name', 'username': 'not-an-email'}
        )
        assert response.status_code in (302, 200, 400)

    def test_admin_users_update_short_password(self, client):
        from app import app
        with app.app_context():
            # Create a user to update
            users.create_user('UpdateMe4', 'updateme4@example.com', 'password123', 0)
            user = users.get_all_users()
            update_user_id = None
            for u in user:
                if u['username'] == 'updateme4@example.com':
                    update_user_id = u['id']
                    break
            assert update_user_id is not None
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.post(
            f'/admin/users/update/{update_user_id}',
            data={'name': 'Name', 'username': 'test@example.com', 'password': 'short'}
        )
        assert response.status_code in (302, 200, 400)

    def test_admin_users_update_without_super_user(self, client):
        from app import app
        with app.app_context():
            # Create a user to update
            users.create_user('UpdateMe5', 'updateme5@example.com', 'password123', 0)
            user = users.get_all_users()
            update_user_id = None
            for u in user:
                if u['username'] == 'updateme5@example.com':
                    update_user_id = u['id']
                    break
            assert update_user_id is not None
        response = client.post(
            f'/admin/users/update/{update_user_id}',
            data={'name': 'Name', 'username': 'test@example.com'}
        )
        assert response.status_code == 403

    def test_admin_users_delete_with_super_user(self, client):
        from app import app
        with app.app_context():
            # Ensure no user with this username exists before creating
            existing_users = users.get_all_users()
            for u in existing_users:
                if u['username'] == 'deleteme@example.com':
                    users.delete_user(u['id'])
            user_created = users.create_user('DeleteMe', 'deleteme@example.com', 'password123', 0)
            assert user_created
            user = users.get_all_users()
            delete_user_id = None
            for u in user:
                if u['username'] == 'deleteme@example.com':
                    delete_user_id = u['id']
                    break
            assert delete_user_id is not None
        with client.session_transaction() as session:
            session['super_user'] = True
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        response = client.post(f'/admin/users/delete/{delete_user_id}', data={'csrf_token': 'test_token'})
        assert response.status_code in (302, 200)
        response = client.post('/admin/users/delete/999999', data={'csrf_token': 'test_token'})
        assert response.status_code in (302, 200)

    def test_admin_users_delete_without_super_user(self, client):
        from app import app
        with app.app_context():
            # Ensure no user with this username exists before creating
            existing_users = users.get_all_users()
            for u in existing_users:
                if u['username'] == 'deleteme2@example.com':
                    users.delete_user(u['id'])
            user_created = users.create_user('DeleteMe2', 'deleteme2@example.com', 'password123', 0)
            assert user_created
            user = users.get_all_users()
            delete_user_id = None
            for u in user:
                if u['username'] == 'deleteme2@example.com':
                    delete_user_id = u['id']
                    break
            assert delete_user_id is not None
        # No super_user in session
        response = client.post(f'/admin/users/delete/{delete_user_id}', data={'csrf_token': 'test_token'})
        assert response.status_code == 403

    def test_admin_users_delete_invalid_csrf(self, client):
        from app import app
        with app.app_context():
            # Ensure no user with this username exists before creating
            existing_users = users.get_all_users()
            for u in existing_users:
                if u['username'] == 'deleteme3@example.com':
                    users.delete_user(u['id'])
            user_created = users.create_user('DeleteMe3', 'deleteme3@example.com', 'password123', 0)
            assert user_created
            user = users.get_all_users()
            delete_user_id = None
            for u in user:
                if u['username'] == 'deleteme3@example.com':
                    delete_user_id = u['id']
                    break
            assert delete_user_id is not None
        with client.session_transaction() as session:
            session['super_user'] = True
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        response = client.post(f'/admin/users/delete/{delete_user_id}', data={'csrf_token': 'wrong_token'})
        assert response.status_code in (400, 403)

    def test_admin_create_user_missing_fields(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': '', 'username': '', 'password': ''}
        )
        assert response.status_code in (302, 200, 400)

    def test_admin_create_user_invalid_email(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': 'Name', 'username': 'not-an-email', 'password': 'password123'}
        )
        assert response.status_code in (302, 200, 400)

    def test_admin_create_user_without_super_user(self, client):
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': 'Name', 'username': 'test@example.com', 'password': 'password123'}
        )
        assert response.status_code == 403

    def test_admin_new_user_without_super_user(self, client):
        response = client.get('/admin/users/new')
        assert response.status_code == 403

    def test_admin_new_user_with_super_user(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/users/new')
        assert response.status_code == 200

    def test_admin_edit_user_with_super_user_invalid(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/users/edit/999999')
        assert response.status_code in (302, 404)

    def test_admin_update_user_duplicate_username(self, client):
        from app import app
        with app.app_context():
            users.create_user('User1', 'dupe@example.com', 'password123', 0)
            users.create_user('User2', 'dupe2@example.com', 'password123', 0)
            user = users.get_all_users()
            update_user_id = None
            for u in user:
                if u['username'] == 'dupe2@example.com':
                    update_user_id = u['id']
                    break
            assert update_user_id is not None
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.post(
            f'/admin/users/update/{update_user_id}',
            data={'name': 'User2', 'username': 'dupe@example.com'},
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_admin_delete_super_user(self, client):
        from app import app
        with app.app_context():
            existing_users = users.get_all_users()
            for u in existing_users:
                if u['username'] == 'superdelete@example.com':
                    users.delete_user(u['id'])
            user_created = users.create_user('SuperDelete', 'superdelete@example.com', 'password123', 1)
            assert user_created
            user = users.get_all_users()
            super_user_id = None
            for u in user:
                if u['username'] == 'superdelete@example.com':
                    super_user_id = u['id']
                    break
            assert super_user_id is not None
        with client.session_transaction() as session:
            session['super_user'] = True
            session['user_id'] = 2
            session['csrf_token'] = 'test_token'
        response = client.post(f'/admin/users/delete/{super_user_id}', data={'csrf_token': 'test_token'}, follow_redirects=True)
        assert response.status_code == 200
        assert 'pääkäyttäj' in response.get_data(as_text=True).lower() or 'virhe' in response.get_data(as_text=True).lower()

    def test_admin_delete_own_user(self, client):
        from app import app
        with app.app_context():
            # Ensure no user with this username exists before creating
            existing_users = users.get_all_users()
            for u in existing_users:
                if u['username'] == 'ownuserdelete@example.com':
                    users.delete_user(u['id'])
            user_created = users.create_user('OwnUserDelete', 'ownuserdelete@example.com', 'password123', 0)
            assert user_created
            user = users.get_all_users()
            own_user_id = None
            for u in user:
                if u['username'] == 'ownuserdelete@example.com':
                    own_user_id = u['id']
                    break
            assert own_user_id is not None
        with client.session_transaction() as session:
            session['super_user'] = True
            session['user_id'] = own_user_id
            session['csrf_token'] = 'test_token'
        response = client.post(f'/admin/users/delete/{own_user_id}', data={'csrf_token': 'test_token'}, follow_redirects=True)
        assert response.status_code == 200
        assert 'Et voi poistaa omaa tunnustasi.' in response.get_data(as_text=True)


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


class TestEntryAndReview:
    def test_entry_view_valid(self, client):
        response = client.get('/entry/1')
        assert response.status_code in (200, 404)

    def test_entry_view_invalid(self, client):
        response = client.get('/entry/999999')
        assert response.status_code == 404

    def test_result_view_valid(self, client):
        response = client.get('/result/1')
        assert response.status_code in (200, 404)

    def test_result_view_invalid(self, client):
        response = client.get('/result/999999')
        assert response.status_code == 404

    def test_add_entry_get_logged_in(self, client):
        with client.session_transaction() as session:
            session['user_id'] = 1
        response = client.get('/contests/contest/1/add_entry')
        assert response.status_code in (200, 404)

    def test_add_entry_get_not_logged_in(self, client):
        response = client.get('/contests/contest/1/add_entry')
        assert response.status_code == 302

    def test_add_entry_post_logged_in(self, client):
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token', 'entry': 'Test entry', 'action': 'submit'}
        )
        assert response.status_code in (302, 200, 404)

    def test_add_entry_post_missing_entry(self, client):
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token', 'entry': '', 'action': 'submit'}
        )
        assert response.status_code in (200, 302, 404)
        if response.status_code == 200:
            assert 'Kilpailutyö ei saa olla tyhjä' in response.get_data(as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_add_entry_post_too_long(self, client):
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        long_text = 'a' * 6000
        response = client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token', 'entry': long_text, 'action': 'submit'}
        )
        assert response.status_code in (200, 302, 404)

    def test_add_entry_post_duplicate(self, client):
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token', 'entry': 'My entry', 'action': 'submit'}
        )
        response = client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token', 'entry': 'My entry', 'action': 'submit'}
        )
        assert response.status_code in (302, 200, 404)
        if response.status_code == 200:
            assert 'Olet jo osallistunut' in response.get_data(as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_review_get_logged_in(self, client):
        with client.session_transaction() as session:
            session['user_id'] = 1
        response = client.get('/review/1')
        assert response.status_code in (200, 404, 302)

    def test_review_get_not_logged_in(self, client):
        response = client.get('/review/1')
        assert response.status_code == 302

    def test_my_texts_logged_in(self, client):
        with client.session_transaction() as session:
            session['user_id'] = 1
        response = client.get('/my_texts')
        assert response.status_code == 200

    def test_my_texts_not_logged_in(self, client):
        response = client.get('/my_texts')
        assert response.status_code == 302

    def test_review_post_missing_points(self, client):
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/review/1',
            data={'csrf_token': 'test_token', 'points_1': '5'}
        )
        assert response.status_code in (200, 302, 404)
        if response.status_code == 200:
            assert 'Kaikki tekstit on arvioitava' in response.get_data(as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_review_post_invalid_points(self, client):
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/review/1',
            data={'csrf_token': 'test_token', 'points_1': '10'},
            follow_redirects=True
        )
        assert response.status_code in (200, 302, 404)
        if response.status_code == 200:
            assert 'arvosanojen tulee olla välillä 0-5' in response.get_data(as_text=True) or 'Virhe' in response.get_data(as_text=True)


class TestPaginationAnd404:
    def test_contests_pagination_out_of_range(self, client):
        response = client.get('/contests?page=999')
        assert response.status_code == 200

    def test_results_pagination_negative_page(self, client):
        response = client.get('/results?page=-1')
        assert response.status_code == 200

    def test_404_error_page(self, client):
        response = client.get('/thispagedoesnotexist')
        assert response.status_code == 404

    def test_admin_update_contest_invalid_id(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/contests/update/999999',
            data={
                'csrf_token': 'test_token',
                'title': 'Updated Title',
                'class_id': 1,
                'short_description': 'Short desc',
                'long_description': 'Long desc',
                'collection_end': '2025-12-31',
                'review_end': '2026-01-31'
            }
        )
        assert response.status_code in (302, 404, 400)

    def test_admin_delete_contest_invalid_id(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post('/admin/contests/delete/999999', data={'csrf_token': 'test_token'})
        assert response.status_code in (302, 200)
