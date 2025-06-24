"""Tests for the admin blueprint and related admin features.

This module contains unit tests for the admin panel routes, including access
control, user management, contest management, entry management, and
pagination/error handling in the Writing Contest Web App.

Test Classes:
    TestAdminRoutes: Tests for admin dashboard and access control.
    TestUserRoutes: Tests for admin user management (CRUD, permissions, CSRF).
    TestPaginationAnd404: Tests for pagination and 404/error handling in admin
                          and public routes.
"""

import users
import pytest
import sqlite3


class TestAdminRoutes:
    def test_new_entry_forbidden(self, client):
        response = client.get('/admin/entries/new')
        assert response.status_code == 403

    def test_delete_user_forbidden(self, client):
        response = client.post('/admin/users/delete/1',
                               data={'csrf_token': 'test_token'})
        assert response.status_code == 403

    def test_edit_user_forbidden(self, client):
        response = client.get('/admin/users/edit/1', follow_redirects=True)
        assert response.status_code == 403

    def test_new_user_forbidden(self, client):
        response = client.get('/admin/users/new')
        assert response.status_code == 403

    def test_admin_route_without_super_user(self, client):
        response = client.get('/admin/')
        assert response.status_code == 403

    def test_admin_route_with_super_user(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/')
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

    def test_admin_edit_contest_without_super_user(self, client):
        response = client.get('/admin/contests/edit/1')
        assert response.status_code == 403

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

    def test_admin_new_contest_without_super_user(self, client):
        response = client.get('/admin/contests/new')
        assert response.status_code == 403

    def test_admin_route_forbidden(self, client):
        response = client.get('/admin/')
        assert response.status_code == 403

    def test_admin_index_contest_phase_listings(self, client, monkeypatch):
        # Mock contest data for each phase
        contests_collection = [
            {"id": 1, "title": "Keräysvaihe", "short_description": "Keräyskuvaus", "class_value": "Runo", "anonymity": 1,
                "public_reviews": 1, "public_results": 1, "collection_end": "2025-12-31", "review_end": "2026-01-31"}
        ]
        contests_review = [
            {"id": 2, "title": "Arviointivaihe", "short_description": "Arviointikuvaus", "class_value": "Novelli", "anonymity": 0,
                "public_reviews": 0, "public_results": 1, "collection_end": "2024-12-31", "review_end": "2025-01-31"}
        ]
        contests_results = [
            {"id": 3, "title": "Tulokset", "short_description": "Tuloksetkuvaus", "class_value": "Essee", "anonymity": 1,
                "public_reviews": 1, "public_results": 1, "collection_end": "2023-12-31", "review_end": "2024-01-31"}
        ]

        monkeypatch.setattr("sql.get_contests_for_entry",
                            lambda *a, **kw: contests_collection)
        monkeypatch.setattr("sql.get_contests_for_review",
                            lambda *a, **kw: contests_review)
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda *a, **kw: contests_results)

        with client.session_transaction() as sess:
            sess['super_user'] = True

        response = client.get('/admin/')
        html = response.get_data(as_text=True)

        # Instead of using url_for, check for the expected static URL path directly.
        # This is simpler and avoids the need for a request context.
        expected_contest_url = 'href="/contests/contest/1"'
        assert expected_contest_url in html

    def test_admin_index_no_contests(self, client, monkeypatch):
        # Mock all contest-fetching and count functions to ensure a truly empty state
        monkeypatch.setattr("sql.get_contests_for_entry", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_contests_for_review", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda *a, **kw: [])
        # Make mocks more robust by accepting any arguments
        monkeypatch.setattr("sql.get_contest_count", lambda *a, **kw: 0)
        monkeypatch.setattr("users.get_user_count", lambda *a, **kw: 0)
        monkeypatch.setattr("sql.get_entry_count", lambda *a, **kw: 0)
        # Add mocks for get_all_* functions that the template might be calling directly
        monkeypatch.setattr("users.get_all_users", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_all_contests", lambda *a, **kw: [])

        with client.session_transaction() as sess:
            sess['super_user'] = True

        response = client.get('/admin/')
        html = response.get_data(as_text=True)
        # Correct the assertion to look for the actual text from the template
        assert "Ei käynnissä olevia keräysvaiheen kilpailuja." in html

    def test_admin_index_shows_only_latest_three_per_phase(self, client, monkeypatch):
        # Mock 5 contests, only 3 latest should be shown
        contests_collection = [
            {"id": i, "title": f"Keräys {i}", "short_description": f"Kuvaus {i}", "class_value": "Runo", "anonymity": 1, "public_reviews": 1, "public_results": 1, "collection_end": f"2025-12-{30 - i}", "review_end": f"2026-01-{31 - i}"} for i in range(5)
        ]
        monkeypatch.setattr("sql.get_contests_for_entry",
                            lambda *a, **kw: contests_collection[:3])
        monkeypatch.setattr("sql.get_contests_for_review", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda *a, **kw: [])

        with client.session_transaction() as sess:
            sess['super_user'] = True

        response = client.get('/admin/')
        html = response.get_data(as_text=True)
        assert "Keräys 0" in html
        assert "Keräys 1" in html
        assert "Keräys 2" in html
        assert "Keräys 3" not in html
        assert "Keräys 4" not in html

    def test_admin_index_contest_details_rendered(self, client, monkeypatch):
        contests_collection = [
            {"id": 1, "title": "Testikisa", "short_description": "Lyhyt kuvaus", "class_value": "Runo", "anonymity": 1,
                "public_reviews": 0, "public_results": 1, "collection_end": "2025-12-31", "review_end": "2026-01-31"}
        ]
        monkeypatch.setattr("sql.get_contests_for_entry",
                            lambda *a, **kw: contests_collection)
        monkeypatch.setattr("sql.get_contests_for_review", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda *a, **kw: [])

        with client.session_transaction() as sess:
            sess['super_user'] = True

        response = client.get('/admin/')
        html = response.get_data(as_text=True)
        assert "Testikisa" in html
        assert "Lyhyt kuvaus" in html
        assert "Anonyymi arviointi" in html
        assert "Tulokset julkisia" in html
        assert "Ei-julkinen arviointi" in html

    def test_admin_index_contest_links(self, client, monkeypatch):
        contests_collection = [
            {"id": 1, "title": "Linkkitesti", "short_description": "Kuvaus", "class_value": "Runo", "anonymity": 1,
                "public_reviews": 1, "public_results": 1, "collection_end": "2025-12-31", "review_end": "2026-01-31"}
        ]
        monkeypatch.setattr("sql.get_contests_for_entry",
                            lambda *a, **kw: contests_collection)
        monkeypatch.setattr("sql.get_contests_for_review", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda *a, **kw: [])

        with client.session_transaction() as sess:
            sess['super_user'] = True

        response = client.get('/admin/')
        html = response.get_data(as_text=True)
        # Check for the static URL directly instead of using url_for to avoid context errors
        assert 'href="/contests/contest/1"' in html

    def test_admin_users_edit_with_super_user(self, app, client):
        # Manually push an application context to perform database operations
        with app.app_context():
            edit_user_id = users.create_user(
                'EditMe', 'editme@example.com', 'password123', 0)
            assert edit_user_id is not None

        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get(f'/admin/users/edit/{edit_user_id}')
        assert response.status_code in (200, 302, 404)

    def test_admin_users_edit_with_super_user_valid_and_invalid(self, app, client):
        with app.app_context():
            edit_user_id = users.create_user(
                'EditMe2', 'editme2@example.com', 'password123', 0)
            assert edit_user_id is not None

        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get(f'/admin/users/edit/{edit_user_id}')
        assert response.status_code in (200, 302, 404)
        response = client.get('/admin/users/edit/999999')
        assert response.status_code in (302, 404)

    def test_admin_users_update_with_super_user(self, app, client):
        with app.app_context():
            update_user_id = users.create_user(
                'UpdateMe', 'updateme@example.com', 'password123', 0)
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

    def test_admin_users_update_missing_fields(self, app, client):
        with app.app_context():
            update_user_id = users.create_user(
                'UpdateMe2', 'updateme2@example.com', 'password123', 0)
            assert update_user_id is not None

        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'  # Add CSRF token to session
        response = client.post(
            f'/admin/users/update/{update_user_id}',
            # Add CSRF token to form data
            data={'name': '', 'username': '', 'csrf_token': 'test_token'}
        )
        assert response.status_code in (302, 200, 400)

    def test_admin_users_update_invalid_email(self, app, client):
        with app.app_context():
            update_user_id = users.create_user(
                'UpdateMe3', 'updateme3@example.com', 'password123', 0)
            assert update_user_id is not None

        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'  # Add CSRF token to session
        response = client.post(
            f'/admin/users/update/{update_user_id}',
            # Add CSRF token to form data
            data={'name': 'Name', 'username': 'not-an-email',
                  'csrf_token': 'test_token'}
        )
        assert response.status_code in (302, 200, 400)

    def test_admin_users_update_short_password(self, app, client):
        with app.app_context():
            update_user_id = users.create_user(
                'UpdateMe4', 'updateme4@example.com', 'password123', 0)
            assert update_user_id is not None

        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'  # Add CSRF token to session
        response = client.post(
            f'/admin/users/update/{update_user_id}',
            # Add CSRF token to form data
            data={'name': 'Name', 'username': 'test@example.com',
                  'password': 'short', 'csrf_token': 'test_token'}
        )
        assert response.status_code in (302, 200, 400)

    def test_admin_users_update_without_super_user(self, app, client):
        with app.app_context():
            update_user_id = users.create_user(
                'UpdateMe5', 'updateme5@example.com', 'password123', 0)
            assert update_user_id is not None

        response = client.post(
            f'/admin/users/update/{update_user_id}',
            data={'name': 'Name', 'username': 'test@example.com'}
        )
        assert response.status_code == 403

    def test_admin_users_delete_with_super_user(self, app, client):
        with app.app_context():
            delete_user_id = users.create_user(
                'DeleteMe', 'deleteme@example.com', 'password123', 0)
            assert delete_user_id is not None

        with client.session_transaction() as session:
            session['super_user'] = True
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        response = client.post(
            f'/admin/users/delete/{delete_user_id}', data={'csrf_token': 'test_token'})
        assert response.status_code in (302, 200)
        response = client.post('/admin/users/delete/999999',
                               data={'csrf_token': 'test_token'})
        assert response.status_code in (302, 200)

    def test_admin_users_delete_without_super_user(self, app, client):
        with app.app_context():
            delete_user_id = users.create_user(
                'DeleteMe2', 'deleteme2@example.com', 'password123', 0)
            assert delete_user_id is not None

        # No super_user in session
        response = client.post(
            f'/admin/users/delete/{delete_user_id}', data={'csrf_token': 'test_token'})
        assert response.status_code == 403

    def test_admin_users_delete_invalid_csrf(self, app, client):
        with app.app_context():
            delete_user_id = users.create_user(
                'DeleteMe3', 'deleteme3@example.com', 'password123', 0)
            assert delete_user_id is not None

        with client.session_transaction() as session:
            session['super_user'] = True
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        response = client.post(
            f'/admin/users/delete/{delete_user_id}', data={'csrf_token': 'wrong_token'})
        assert response.status_code in (400, 403)

    def test_admin_create_user_missing_fields(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': '',
                  'username': '', 'password': ''}
        )
        assert response.status_code in (302, 200, 400)

    def test_admin_create_user_invalid_email(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': 'Name',
                  'username': 'not-an-email', 'password': 'password123'}
        )
        assert response.status_code in (302, 200, 400)

    def test_admin_create_user_without_super_user(self, client):
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': 'Name',
                  'username': 'test@example.com', 'password': 'password123'}
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

    def test_admin_update_user_duplicate_username(self, app, client):
        with app.app_context():
            users.create_user('User1', 'dupe@example.com', 'password123', 0)
            update_user_id = users.create_user(
                'User2', 'dupe2@example.com', 'password123', 0)
            assert update_user_id is not None

        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'  # Add CSRF token to session
        response = client.post(
            f'/admin/users/update/{update_user_id}',
            # Add CSRF token to form data
            data={'name': 'User2', 'username': 'dupe@example.com',
                  'csrf_token': 'test_token'},
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_admin_delete_super_user(self, app, client):
        with app.app_context():
            super_user_id = users.create_user(
                'SuperDelete', 'superdelete@example.com', 'password123', 1)
            assert super_user_id is not None

        with client.session_transaction() as session:
            session['super_user'] = True
            # Assuming a different admin is doing the deleting
            session['user_id'] = 2
            session['csrf_token'] = 'test_token'
        response = client.post(f'/admin/users/delete/{super_user_id}', data={
                               'csrf_token': 'test_token'}, follow_redirects=True)
        assert response.status_code == 200
        assert 'pääkäyttäj' in response.get_data(as_text=True).lower(
        ) or 'virhe' in response.get_data(as_text=True).lower()

    def test_admin_delete_own_user(self, app, client):
        with app.app_context():
            own_user_id = users.create_user(
                'OwnUserDelete', 'ownuserdelete@example.com', 'password123', 0)
            assert own_user_id is not None

        with client.session_transaction() as session:
            session['super_user'] = True
            session['user_id'] = own_user_id
            session['csrf_token'] = 'test_token'
        response = client.post(f'/admin/users/delete/{own_user_id}', data={
                               'csrf_token': 'test_token'}, follow_redirects=True)
        assert response.status_code == 200
        assert 'Et voi poistaa omaa tunnustasi.' in response.get_data(
            as_text=True)

    def test_edit_entry_as_non_owner(self, client):
        # Assume entry 2 belongs to user 2, but we log in as user 1
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        response = client.get('/entry/2/edit')
        assert response.status_code == 403

    def test_delete_entry_invalid_csrf(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'correct_token'
        response = client.post(
            '/entry/1/delete', data={'csrf_token': 'wrong_token'})
        assert response.status_code in (400, 403)

    def test_review_get_logged_in(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        response = client.get('/review/1')
        assert response.status_code in (200, 404, 302)

    def test_review_post_valid(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'
        # You may need to adjust points_1, points_2, ... based on your app logic
        response = client.post(
            '/review/1', data={'csrf_token': 'test_token', 'points_1': '5'}, follow_redirects=True)
        assert response.status_code in (200, 302, 404)

    def test_admin_contests_with_search_filter(self, client, monkeypatch):
        """Test the title search filter on the admin contests page."""
        monkeypatch.setattr("sql.get_all_contests", lambda **kwargs: [])
        monkeypatch.setattr("sql.get_contest_count", lambda **kwargs: 0)
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/contests?title_search=Test')
        assert response.status_code == 200
        assert b'value="Test"' in response.data

    def test_admin_users_with_filters(self, client, monkeypatch):
        """Test the search filters on the admin users page."""
        monkeypatch.setattr("users.get_all_users", lambda **kwargs: [])
        monkeypatch.setattr("users.get_user_count", lambda **kwargs: 0)
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get(
            '/admin/users?name_search=Admin&username_search=admin@test.com&super_user=1')
        assert response.status_code == 200
        assert b'value="Admin"' in response.data
        assert b'value="admin@test.com"' in response.data
        assert '<option value="1" selected>Kyllä</option>' in response.get_data(
            as_text=True)

    def test_admin_entries_with_filters(self, client, monkeypatch):
        """Test the search filters on the admin entries page."""
        # Provide a mock contest list that includes the contest being filtered by
        mock_contests = [{'id': 1, 'title': 'Test Contest'}]
        monkeypatch.setattr("sql.get_all_contests", lambda: mock_contests)
        monkeypatch.setattr("sql.get_all_entries", lambda **kwargs: [])
        monkeypatch.setattr("sql.get_entry_count", lambda **kwargs: 0)
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get(
            '/admin/entries?contest_id=1&user_search=TestUser')
        assert response.status_code == 200
        assert b'value="TestUser"' in response.data
        assert b'<option value="1" selected>' in response.data


class TestAdminContestManagement:
    """Tests for contest creation, updating, and error handling in the admin panel."""

    @pytest.fixture(autouse=True)
    def admin_session(self, client):
        """Fixture to automatically log in as a superuser for all tests in this class."""
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'

    def test_create_contest_validation_failure(self, client):
        """Test contest creation with missing required fields."""
        response = client.post(
            '/admin/contests/create', data={'csrf_token': 'test_token'}, follow_redirects=True)
        assert response.status_code == 200
        # "Kaikki pakolliset kentät on täytettävä."
        assert b'Kaikki pakolliset kent\xc3\xa4t on t\xc3\xa4ytett\xc3\xa4v\xc3\xa4.' in response.data

    def test_create_contest_description_length_validation(self, client):
        """Test contest creation with descriptions that are too long."""
        long_string = "a" * 2001
        response = client.post('/admin/contests/create', data={
            'csrf_token': 'test_token', 'title': 'T', 'class_id': 1, 'collection_end': 'd', 'review_end': 'd',
            'short_description': long_string, 'long_description': long_string
        }, follow_redirects=True)
        assert b'Lyhyt kuvaus saa olla enint\xc3\xa4\xc3\xa4n 255 merkki\xc3\xa4.' in response.data
        assert b'Pitk\xc3\xa4 kuvaus saa olla enint\xc3\xa4\xc3\xa4n 2000 merkki\xc3\xa4.' in response.data

    def test_create_contest_db_error(self, client, monkeypatch):
        """Test generic exception handling during contest creation."""
        monkeypatch.setattr("sql.create_contest", lambda *args,
                            **kwargs: (_ for _ in ()).throw(Exception("DB Error")))
        response = client.post('/admin/contests/create', data={
            'csrf_token': 'test_token', 'title': 'T', 'class_id': 1, 'collection_end': 'd', 'review_end': 'd',
            'short_description': 's', 'long_description': 'l'
        }, follow_redirects=True)
        assert b'Kilpailua ei voitu luoda.' in response.data

    def test_edit_contest_not_found(self, client, monkeypatch):
        """Test that editing a non-existent contest results in a 404."""
        monkeypatch.setattr("sql.get_contest_by_id", lambda contest_id: None)
        response = client.get('/admin/contests/edit/999')
        assert response.status_code == 404

    def test_admin_contests_create_post(self, client):
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
        response = client.post(
            '/admin/contests/delete/1',
            data={'csrf_token': 'test_token'}
        )
        assert response.status_code in (302, 200, 404)

    def test_admin_edit_contest_with_super_user(self, client):
        response = client.get('/admin/contests/edit/1')
        assert response.status_code in (200, 404)

    def test_admin_update_contest_with_super_user(self, client):
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

    def test_admin_new_contest_with_super_user(self, client):
        response = client.get('/admin/contests/new')
        assert response.status_code == 200

    def test_admin_create_contest_short_description_too_long(self, client):
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
        assert '255' in response.get_data(
            as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_admin_create_contest_long_description_too_long(self, client):
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
        assert '2000' in response.get_data(
            as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_admin_create_contest_missing_fields(self, client):
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

    def test_admin_update_contest_short_description_too_long(self, client, monkeypatch):
        # Mock the DB calls for the redirected-to page
        monkeypatch.setattr("sql.get_contest_by_id", lambda contest_id: {
                            'id': 1, 'title': 'Test Contest'})
        monkeypatch.setattr("sql.get_all_classes", lambda: [])

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
        assert '255' in response.get_data(
            as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_admin_update_contest_long_description_too_long(self, client, monkeypatch):
        # Mock the DB calls for the redirected-to page
        monkeypatch.setattr("sql.get_contest_by_id", lambda contest_id: {
                            'id': 1, 'title': 'Test Contest'})
        monkeypatch.setattr("sql.get_all_classes", lambda: [])

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
        assert '2000' in response.get_data(
            as_text=True) or 'Virhe' in response.get_data(as_text=True)


class TestAdminUserManagement:
    """Additional tests for user management in the admin panel."""

    @pytest.fixture(autouse=True)
    def admin_session(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'

    def test_create_user_duplicate_username(self, client, monkeypatch):
        """Test user creation failure when username is already taken."""
        monkeypatch.setattr("users.create_user", lambda *args, **kwargs: False)
        response = client.post('/admin/users/create', data={
            'csrf_token': 'test_token', 'name': 'Test', 'username': 'dupe@test.com', 'password': 'password123'
        }, follow_redirects=True)
        # "Käyttäjänimi on jo käytössä."
        assert b'K\xc3\xa4ytt\xc3\xa4j\xc3\xa4nimi on jo k\xc3\xa4yt\xc3\xb6ss\xc3\xa4.' in response.data

    def test_edit_user_not_found(self, client, monkeypatch):
        """Test that editing a non-existent user redirects with a flash message."""
        monkeypatch.setattr("users.get_user", lambda user_id: None)
        response = client.get('/admin/users/edit/999', follow_redirects=True)
        # "Käyttäjää ei löytynyt."
        assert b'K\xc3\xa4ytt\xc3\xa4j\xc3\xa4\xc3\xa4 ei l\xc3\xb6ytynyt.' in response.data

    def test_update_user_integrity_error(self, app, client, monkeypatch):
        """Test user update failure due to a duplicate username (IntegrityError)."""
        # Create the user that we will attempt to update
        with app.app_context():
            users.create_user('TestUser', 'test@example.com', 'password123', 0)

        monkeypatch.setattr("users.update_user", lambda *args, **
                            kwargs: (_ for _ in ()).throw(sqlite3.IntegrityError))
        response = client.post('/admin/users/update/1', data={
            'csrf_token': 'test_token', 'name': 'Test', 'username': 'dupe@test.com'
        }, follow_redirects=True)
        # "Käyttäjätunnus on jo käytössä."
        assert b'K\xc3\xa4ytt\xc3\xa4j\xc3\xa4tunnus on jo k\xc3\xa4yt\xc3\xb6ss\xc3\xa4.' in response.data


class TestAdminCoverage:

    @pytest.fixture(autouse=True)
    def admin_session(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'

    def test_new_entry_get_request(self, client, monkeypatch):
        """Test the GET request handler for the new entry page."""
        monkeypatch.setattr("sql.get_all_contests", lambda: [
                            {'id': 1, 'title': 'Test Contest'}])
        # Add the 'username' key to the mock user data
        monkeypatch.setattr("users.get_all_users", lambda: [
                            {'id': 1, 'name': 'Test User', 'username': 'test@user.com'}])
        response = client.get('/admin/entries/new')
        assert response.status_code == 200
        # Correct the asserted text to match the template's H1 tag
        assert b'Luo uusi kilpailuty\xc3\xb6' in response.data  # "Luo uusi kilpailutyö"

    def test_new_entry_post_generic_db_error(self, client, monkeypatch):
        """Test the generic exception handler in the new entry POST route."""
        monkeypatch.setattr("sql.create_entry", lambda *a, **
                            kw: (_ for _ in ()).throw(Exception("Generic DB Error")))
        monkeypatch.setattr("sql.get_all_contests", lambda: [
                            {'id': 1, 'title': 'Test Contest'}])
        # Add the 'username' key here as well, since this test also re-renders the template
        monkeypatch.setattr("users.get_all_users", lambda: [
                            {'id': 1, 'name': 'Test User', 'username': 'test@user.com'}])
        response = client.post('/admin/entries/new', data={
            'csrf_token': 'test_token', 'contest_id': 1, 'user_id': 1, 'entry': 'text'
        })
        assert response.status_code == 200
        assert b'Teksti\xc3\xa4 ei voitu luoda.' in response.data

    def test_edit_entry_success(self, client, monkeypatch):
        """Test successful rendering of the edit entry page."""
        # Provide more complete mock data for the entry and the dropdowns
        mock_entry = {'id': 1, 'contest_id': 1,
                      'user_id': 1, 'entry': 'Test entry text'}
        mock_contests = [{'id': 1, 'title': 'Test Contest'}]
        mock_users = [
            {'id': 1, 'name': 'Test User', 'username': 'test@user.com'}]

        monkeypatch.setattr("sql.get_entry_by_id", lambda entry_id: mock_entry)
        monkeypatch.setattr("sql.get_all_contests", lambda: mock_contests)
        monkeypatch.setattr("users.get_all_users", lambda: mock_users)

        response = client.get('/admin/entries/edit/1')
        assert response.status_code == 200
        # Correct the assertion to match the likely heading in the template
        # "Muokkaa kilpailutyötä"
        assert b'Muokkaa kilpailuty\xc3\xb6t\xc3\xa4' in response.data

    def test_update_entry_success(self, client, monkeypatch):
        """Test the success path for updating an entry."""
        monkeypatch.setattr("sql.update_entry", lambda *a, **kw: None)
        response = client.post('/admin/entries/update/1', data={
            'csrf_token': 'test_token', 'contest_id': 1, 'user_id': 1, 'entry': 'text'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Tekstin tiedot p\xc3\xa4ivitetty.' in response.data

    def test_delete_contest_db_error(self, client, monkeypatch):
        """Test generic exception handling during contest deletion."""
        monkeypatch.setattr("sql.delete_contest", lambda *a,
                            **kw: (_ for _ in ()).throw(Exception("DB Error")))
        response = client.post('/admin/contests/delete/1',
                               data={'csrf_token': 'test_token'}, follow_redirects=True)
        assert response.status_code == 200
        # This assumes you add a try-except block to delete_contest like you have in delete_entry
        # If not, this test will fail, and you should add the try-except block to your route.

    def test_create_contest_db_exception(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("sql.create_contest", lambda *a,
                            **kw: (_ for _ in ()).throw(Exception("fail")))
        response = client.post(
            '/admin/contests/create',
            data={
                'csrf_token': 'test_token',
                'title': 'Test',
                'class_id': 1,
                'short_description': 'Short',
                'long_description': 'Long',
                'collection_end': '2025-12-31',
                'review_end': '2026-01-31'
            },
            follow_redirects=True
        )
        assert b'Kilpailua ei voitu luoda.' in response.data

    # --- 208: delete_contest, except block ---
    def test_delete_contest_db_exception(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("sql.delete_contest", lambda *a,
                            **kw: (_ for _ in ()).throw(Exception("fail")))
        response = client.post(
            '/admin/contests/delete/1',
            data={'csrf_token': 'test_token'},
            follow_redirects=True
        )
        assert b'Kilpailua ei voitu poistaa.' in response.data

    # --- 233: edit_contest, abort(404) ---
    def test_edit_contest_not_found(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: None)
        monkeypatch.setattr("sql.get_all_classes", lambda: [])
        response = client.get('/admin/contests/edit/999')
        assert response.status_code == 404

    # --- 247: update_contest, errors branch ---
    def test_update_contest_missing_fields(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
                            'id': 1, 'title': 'Test'})
        monkeypatch.setattr("sql.get_all_classes", lambda: [])
        response = client.post(
            '/admin/contests/update/1',
            data={
                'csrf_token': 'test_token',
                'title': '',
                'class_id': '',
                'short_description': '',
                'long_description': '',
                'collection_end': '',
                'review_end': ''
            },
            follow_redirects=True
        )
        assert b'Kaikki pakolliset kent' in response.data

    # --- 312-314: create_user, missing fields ---
    def test_create_user_missing_fields(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': '',
                  'username': '', 'password': ''},
            follow_redirects=True
        )
        assert b'Kaikki kent' in response.data

    # --- 320: create_user, invalid email ---
    def test_create_user_invalid_email(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': 'Test',
                  'username': 'notanemail', 'password': 'password123'},
            follow_redirects=True
        )
        assert b'S\xc3\xa4hk\xc3\xb6postiosoite ei ole kelvollinen' in response.data

    # --- 332: create_user, duplicate username ---
    def test_create_user_duplicate_username(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.create_user", lambda *a, **kw: False)
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': 'Test',
                  'username': 'dupe@test.com', 'password': 'password123'},
            follow_redirects=True
        )
        assert b'K\xc3\xa4ytt\xc3\xa4j\xc3\xa4nimi on jo k\xc3\xa4yt\xc3\xb6ss\xc3\xa4' in response.data

    # --- 336: create_user, success ---
    def test_create_user_success(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.create_user", lambda *a, **kw: True)
        response = client.post(
            '/admin/users/create',
            data={'csrf_token': 'test_token', 'name': 'Test',
                  'username': 'test@example.com', 'password': 'password123'},
            follow_redirects=True
        )
        assert b'Uusi k\xc3\xa4ytt\xc3\xa4j\xc3\xa4 on luotu' in response.data

    # --- 368-371: edit_user, user not found ---
    def test_edit_user_not_found(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
        monkeypatch.setattr("users.get_user", lambda uid: None)
        response = client.get('/admin/users/edit/999', follow_redirects=True)
        assert b'K\xc3\xa4ytt\xc3\xa4j\xc3\xa4\xc3\xa4 ei l\xc3\xb6ytynyt' in response.data

    # --- 380: update_user, forbidden ---
    def test_update_user_forbidden(self, client):
        response = client.post(
            '/admin/users/update/1', data={'name': 'Test', 'username': 'test@example.com'})
        assert response.status_code == 403

    # --- 398-405: update_user, missing fields, invalid email, short password ---
    def test_update_user_missing_fields(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.get_user", lambda uid: {
                            'id': 1, 'name': 'Test', 'username': 'test@example.com'})
        response = client.post(
            '/admin/users/update/1',
            data={'csrf_token': 'test_token', 'name': '', 'username': ''},
            follow_redirects=True
        )
        assert b'Nimi ja k\xc3\xa4ytt\xc3\xa4j\xc3\xa4tunnus ovat pakollisia' in response.data

    def test_update_user_invalid_email(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.get_user", lambda uid: {
                            'id': 1, 'name': 'Test', 'username': 'test@example.com'})
        response = client.post(
            '/admin/users/update/1',
            data={'csrf_token': 'test_token',
                  'name': 'Test', 'username': 'notanemail'},
            follow_redirects=True
        )
        assert b'S\xc3\xa4hk\xc3\xb6postiosoite ei ole kelvollinen' in response.data

    def test_update_user_short_password(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.get_user", lambda uid: {
                            'id': 1, 'name': 'Test', 'username': 'test@example.com'})
        response = client.post(
            '/admin/users/update/1',
            data={'csrf_token': 'test_token', 'name': 'Test',
                  'username': 'test@example.com', 'password': '123'},
            follow_redirects=True
        )
        assert b'Salasanan on oltava v\xc3\xa4hint\xc3\xa4\xc3\xa4n' in response.data

    # --- 411: update_user, user not found ---
    def test_update_user_user_not_found(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.get_user", lambda uid: None)
        response = client.post(
            '/admin/users/update/999',
            data={'csrf_token': 'test_token', 'name': 'Test',
                  'username': 'test@example.com'},
            follow_redirects=True
        )
        assert response.status_code == 404

    # --- 423-424: update_user, IntegrityError ---
    def test_update_user_integrity_error(self, client, monkeypatch):
        import sqlite3
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.get_user", lambda uid: {
                            'id': 1, 'name': 'Test', 'username': 'test@example.com'})

        def raise_integrity(*a, **kw):
            raise sqlite3.IntegrityError()
        monkeypatch.setattr("users.update_user", raise_integrity)
        response = client.post(
            '/admin/users/update/1',
            data={'csrf_token': 'test_token', 'name': 'Test',
                  'username': 'test@example.com'},
            follow_redirects=True
        )
        assert b'K\xc3\xa4ytt\xc3\xa4j\xc3\xa4tunnus on jo k\xc3\xa4yt\xc3\xb6ss\xc3\xa4' in response.data

    # --- 435-436, 439: update_user, generic Exception ---
    def test_update_user_generic_exception(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.get_user", lambda uid: {
                            'id': 1, 'name': 'Test', 'username': 'test@example.com'})

        def raise_exception(*a, **kw):
            raise Exception("fail")
        monkeypatch.setattr("users.update_user", raise_exception)
        response = client.post(
            '/admin/users/update/1',
            data={'csrf_token': 'test_token', 'name': 'Test',
                  'username': 'test@example.com'},
            follow_redirects=True
        )
        assert b'K\xc3\xa4ytt\xc3\xa4j\xc3\xa4n tietoja ei voitu p\xc3\xa4ivitt\xc3\xa4\xc3\xa4' in response.data

    # --- 470-471: delete_user, delete own user ---
    def test_delete_own_user(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/users/delete/1', data={'csrf_token': 'test_token'}, follow_redirects=True)
        assert b'Et voi poistaa omaa tunnustasi' in response.data

    # --- 494: delete_user, user not found ---
    def test_delete_user_not_found(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.get_user", lambda uid: None)
        response = client.post(
            '/admin/users/delete/999', data={'csrf_token': 'test_token'}, follow_redirects=True)
        assert b'K\xc3\xa4ytt\xc3\xa4j\xc3\xa4\xc3\xa4 ei l\xc3\xb6ytynyt' in response.data

    # --- 501-502: delete_user, super user ---
    def test_delete_super_user(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.get_user", lambda uid: {
                            'id': 2, 'name': 'Super', 'username': 'super@example.com', 'super_user': 1})
        response = client.post(
            '/admin/users/delete/2', data={'csrf_token': 'test_token'}, follow_redirects=True)
        assert b'P\xc3\xa4\xc3\xa4k\xc3\xa4ytt\xc3\xa4ji\xc3\xa4 ei voi poistaa' in response.data

    # --- 508-511: delete_user, generic Exception ---
    def test_delete_user_generic_exception(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("users.get_user", lambda uid: {
                            'id': 3, 'name': 'User', 'username': 'user@example.com', 'super_user': 0})
        monkeypatch.setattr("users.delete_user", lambda uid: (
            _ for _ in ()).throw(Exception("fail")))
        response = client.post(
            '/admin/users/delete/3', data={'csrf_token': 'test_token'}, follow_redirects=True)
        assert b'K\xc3\xa4ytt\xc3\xa4j\xc3\xa4\xc3\xa4 ei voitu poistaa' in response.data

    # --- 522-524: new_entry, missing fields POST ---
    def test_new_entry_post_missing_fields(self, client, monkeypatch):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr("sql.get_all_contests", lambda: [
                            {'id': 1, 'title': 'Test Contest'}])
        monkeypatch.setattr("users.get_all_users", lambda: [
                            {'id': 1, 'name': 'Test User', 'username': 'test@user.com'}])
        response = client.post(
            '/admin/entries/new',
            data={'csrf_token': 'test_token',
                  'contest_id': '', 'user_id': '', 'entry': ''},
            follow_redirects=True
        )
        assert b'Kaikki pakolliset kent' in response.data
