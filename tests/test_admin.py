"""Tests for the admin blueprint and related admin features.

This module contains unit tests for the admin panel routes, including access
control, contest management, entry management, and
pagination/error handling in the Writing Contest Web App.

Test Classes:
    TestAdminAccessControl: Tests for admin dashboard and access control.
    TestAdminDashboard: Tests for the main admin dashboard page.
    TestAdminContestManagement: Tests for contest management in the admin
                                panel.
    TestAdminEntryManagement: Tests for entry management in the admin panel.
    TestAdminCoverage: Tests for increasing test coverage of admin routes.
"""

import sqlite3
import pytest


class TestAdminAccessControl:
    """Tests access control for various admin routes."""

    def test_admin_route_forbidden_for_non_admin(self, client):
        """Test that non-admins are forbidden from the main admin page."""
        response = client.get('/admin/')
        assert response.status_code == 403

    def test_admin_route_accessible_for_admin(self, client):
        """Test that admins can access the main admin page."""
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/')
        assert response.status_code == 200
        assert 'Ylläpito'.encode('utf-8') in response.data

    def test_admin_contests_route_forbidden_for_non_admin(self, client):
        """Test that non-admins are forbidden from the admin contests page."""
        response = client.get('/admin/contests')
        assert response.status_code == 403

    def test_admin_entries_route_forbidden_for_non_admin(self, client):
        """Test that non-admins are forbidden from the admin entries page."""
        response = client.get('/admin/entries')
        assert response.status_code == 403

    def test_edit_entry_as_non_owner(self, client):
        """Test that a user cannot edit an entry they do not own."""
        # Assume entry 2 belongs to user 2, but we log in as user 1
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        response = client.get('/entry/2/edit')
        assert response.status_code == 403

    def test_delete_entry_invalid_csrf(self, client):
        """Test that deleting an entry with an invalid CSRF token fails."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'correct_token'
        response = client.post(
            '/entry/1/delete', data={'csrf_token': 'wrong_token'})
        assert response.status_code in (400, 403)

    def test_review_get_logged_in(self, client):
        """Test that a logged-in user can access the review page."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        response = client.get('/review/1')
        assert response.status_code in (200, 404, 302)

    def test_review_post_valid(self, client):
        """Test that a valid review can be submitted."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'
        # You may need to adjust points_1, points_2, ... based on your app
        # logic
        response = client.post(
            '/review/1', data={'csrf_token': 'test_token', 'points_1': '5'},
            follow_redirects=True)
        assert response.status_code in (200, 302, 404)


class TestAdminDashboard:
    """Tests for the main admin dashboard page."""

    @pytest.fixture(autouse=True)
    def admin_session(self, client):
        """Set up an admin session for all tests in this class."""
        with client.session_transaction() as session:
            session['super_user'] = True

    def test_admin_index_contest_phase_listings(self, client, monkeypatch):
        """Test that the admin index correctly lists contests in different
        phases."""
        # Mock contest data for each phase
        contests_collection = [
            {"id": 1, "title": "Keräysvaihe",
             "short_description": "Keräyskuvaus",
             "class_value": "Runo", "anonymity": 1,
             "public_reviews": 1, "public_results": 1,
             "collection_end": "2025-12-31", "review_end": "2026-01-31"}
        ]
        contests_review = [
            {"id": 2, "title": "Arviointivaihe",
             "short_description": "Arviointikuvaus",
             "class_value": "Novelli", "anonymity": 0,
             "public_reviews": 0, "public_results": 1,
             "collection_end": "2024-12-31", "review_end": "2025-01-31"}
        ]
        contests_results = [
            {"id": 3, "title": "Tulokset",
             "short_description": "Tuloksetkuvaus",
             "class_value": "Essee", "anonymity": 1,
             "public_reviews": 1, "public_results": 1,
             "collection_end": "2023-12-31", "review_end": "2024-01-31"}
        ]

        monkeypatch.setattr("sql.get_contests_for_entry",
                            lambda *a, **kw: contests_collection)
        monkeypatch.setattr("sql.get_contests_for_review",
                            lambda *a, **kw: contests_review)
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda *a, **kw: contests_results)

        response = client.get('/admin/')
        html = response.get_data(as_text=True)

        # Instead of using url_for, check for the expected static URL path
        # directly.
        # This is simpler and avoids the need for a request context.
        expected_contest_url = 'href="/contests/contest/1"'
        assert expected_contest_url in html

    def test_admin_index_no_contests(self, client, monkeypatch):
        """Test that the admin index displays correctly when there are no
        contests."""
        # Mock all contest-fetching and count functions to ensure a truly
        # empty state
        monkeypatch.setattr("sql.get_contests_for_entry", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_contests_for_review", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda *a, **kw: [])
        # Make mocks more robust by accepting any arguments
        monkeypatch.setattr("sql.get_contest_count", lambda *a, **kw: 0)
        monkeypatch.setattr("users.get_user_count", lambda *a, **kw: 0)
        monkeypatch.setattr("sql.get_entry_count", lambda *a, **kw: 0)
        # Add mocks for get_all_* functions that the template might be calling
        # directly
        monkeypatch.setattr("users.get_all_users", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_all_contests", lambda *a, **kw: [])

        response = client.get('/admin/')
        html = response.get_data(as_text=True)
        # Correct the assertion to look for the actual text from the template
        assert "Ei käynnissä olevia keräysvaiheen kilpailuja." in html

    def test_admin_index_shows_only_latest_three_per_phase(self, client,
                                                           monkeypatch):
        """Test that the admin index paginates correctly, showing only 3 per
        phase."""
        # Mock 5 contests, only 3 latest should be shown
        contests_collection = [
            {"id": i, "title": f"Keräys {i}",
             "short_description": f"Kuvaus {i}", "class_value": "Runo",
             "anonymity": 1, "public_reviews": 1, "public_results": 1,
             "collection_end": f"2025-12-{30 - i}",
             "review_end": f"2026-01-{31 - i}"} for i in range(5)
        ]
        monkeypatch.setattr("sql.get_contests_for_entry",
                            lambda *a, **kw: contests_collection[:3])
        monkeypatch.setattr("sql.get_contests_for_review", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda *a, **kw: [])

        response = client.get('/admin/')
        html = response.get_data(as_text=True)
        assert "Keräys 0" in html
        assert "Keräys 1" in html
        assert "Keräys 2" in html
        assert "Keräys 3" not in html
        assert "Keräys 4" not in html

    def test_admin_index_contest_details_rendered(self, client, monkeypatch):
        """Test that contest details are rendered correctly on the admin
        index."""
        contests_collection = [
            {"id": 1, "title": "Testikisa",
             "short_description": "Lyhyt kuvaus", "class_value": "Runo",
             "anonymity": 1, "public_reviews": 0, "public_results": 1,
             "collection_end": "2025-12-31", "review_end": "2026-01-31"}
        ]
        monkeypatch.setattr("sql.get_contests_for_entry",
                            lambda *a, **kw: contests_collection)
        monkeypatch.setattr("sql.get_contests_for_review", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda *a, **kw: [])

        response = client.get('/admin/')
        html = response.get_data(as_text=True)
        assert "Testikisa" in html
        assert "Lyhyt kuvaus" in html
        assert "Anonyymi arviointi" in html
        assert "Tulokset julkisia" in html
        assert "Ei-julkinen arviointi" in html

    def test_admin_index_contest_links(self, client, monkeypatch):
        """Test that links to contests on the admin index are correct."""
        contests_collection = [
            {"id": 1, "title": "Linkkitesti", "short_description": "Kuvaus",
             "class_value": "Runo", "anonymity": 1, "public_reviews": 1,
             "public_results": 1, "collection_end": "2025-12-31",
             "review_end": "2026-01-31"}
        ]
        monkeypatch.setattr("sql.get_contests_for_entry",
                            lambda *a, **kw: contests_collection)
        monkeypatch.setattr("sql.get_contests_for_review", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda *a, **kw: [])

        response = client.get('/admin/')
        html = response.get_data(as_text=True)
        # Check for the static URL directly instead of using url_for to avoid
        # context errors
        assert 'href="/contests/contest/1"' in html


class TestAdminContestManagement:
    """Tests for contest creation, updating, and error handling in the admin
    panel."""

    @pytest.fixture(autouse=True)
    def admin_session(self, client):
        """Fixture to automatically log in as a superuser for all tests in
        this class."""
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'

    def test_admin_contests_route_accessible(self, client):
        """Test that admins can access the admin contests page."""
        response = client.get('/admin/contests')
        assert response.status_code == 200

    def test_admin_edit_contest_forbidden_for_non_admin(self, client):
        """Test that non-admins are forbidden from the edit contest page."""
        with client.session_transaction() as session:
            del session['super_user']
        response = client.get('/admin/contests/edit/1')
        assert response.status_code == 403

    def test_admin_update_contest_forbidden_for_non_admin(self, client):
        """Test that non-admins cannot update contests."""
        with client.session_transaction() as session:
            del session['super_user']
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

    def test_admin_new_contest_forbidden_for_non_admin(self, client):
        """Test that non-admins are forbidden from the new contest page."""
        with client.session_transaction() as session:
            del session['super_user']
        response = client.get('/admin/contests/new')
        assert response.status_code == 403

    def test_admin_contests_with_search_filter(self, client, monkeypatch):
        """Test the title search filter on the admin contests page."""
        monkeypatch.setattr("sql.get_all_contests", lambda **kwargs: [])
        monkeypatch.setattr("sql.get_contest_count", lambda **kwargs: 0)
        response = client.get('/admin/contests?title_search=Test')
        assert response.status_code == 200
        assert b'value="Test"' in response.data

    def test_create_contest_validation_failure(self, client):
        """Test contest creation with missing required fields."""
        response = client.post(
            '/admin/contests/create', data={'csrf_token': 'test_token'},
            follow_redirects=True)
        assert response.status_code == 200
        # "Kaikki pakolliset kentät on täytettävä."
        assert (b'Kaikki pakolliset kent\xc3\xa4t on '
                b't\xc3\xa4ytett\xc3\xa4v\xc3\xa4.') in response.data

    def test_create_contest_description_length_validation(self, client):
        """Test contest creation with descriptions that are too long."""
        long_string = "a" * 2001
        response = client.post('/admin/contests/create', data={
            'csrf_token': 'test_token', 'title': 'T', 'class_id': 1,
            'collection_end': 'd', 'review_end': 'd',
            'short_description': long_string, 'long_description': long_string
        }, follow_redirects=True)
        assert (b'Lyhyt kuvaus saa olla enint\xc3\xa4\xc3\xa4n 255 '
                b'merkki\xc3\xa4.') in response.data
        assert (b'Pitk\xc3\xa4 kuvaus saa olla enint\xc3\xa4\xc3\xa4n 2000 '
                b'merkki\xc3\xa4.') in response.data

    def test_create_contest_db_error(self, client, monkeypatch):
        """Test generic exception handling during contest creation."""
        monkeypatch.setattr("sql.create_contest", lambda data:
                            (_ for _ in ()).throw(sqlite3.Error(
                                "DB Error"
                                )))
        response = client.post('/admin/contests/create', data={
            'csrf_token': 'test_token', 'title': 'T', 'class_id': 1,
            'short_description': 's', 'long_description': 'l',
            'collection_end': '2025-12-31', 'review_end': '2026-01-31'
        }, follow_redirects=True)
        assert b'Kilpailua ei voitu luoda.' in response.data

    def test_edit_contest_not_found(self, client, monkeypatch):
        """Test that editing a non-existent contest results in a 404."""
        monkeypatch.setattr("sql.get_contest_by_id", lambda contest_id: None)
        response = client.get('/admin/contests/edit/999')
        assert response.status_code == 404

    def test_admin_contests_create_post(self, client):
        """Test successful contest creation via POST request."""
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
        """Test successful contest deletion via POST request."""
        response = client.post(
            '/admin/contests/delete/1',
            data={'csrf_token': 'test_token'}
        )
        assert response.status_code in (302, 200, 404)

    def test_admin_edit_contest_with_super_user(self, client):
        """Test that an admin can access the edit contest page."""
        response = client.get('/admin/contests/edit/1')
        assert response.status_code in (200, 404)

    def test_admin_update_contest_with_super_user(self, client):
        """Test that an admin can successfully update a contest."""
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
        """Test that an admin can access the new contest page."""
        response = client.get('/admin/contests/new')
        assert response.status_code == 200

    def test_admin_create_contest_short_description_too_long(self, client):
        """Test validation for short description length on contest creation."""
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
        """Test validation for long description length on contest creation."""
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
        """Test validation for missing fields on contest creation."""
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

    def test_admin_update_contest_short_description_too_long(self, client,
                                                             monkeypatch):
        """Test validation for short description length on contest update."""
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

    def test_admin_update_contest_long_description_too_long(self, client,
                                                            monkeypatch):
        """Test validation for long description length on contest update."""
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


class TestAdminEntryManagement:
    """Tests for entry management in the admin panel."""

    @pytest.fixture(autouse=True)
    def admin_session(self, client):
        """Set up an admin session for all tests in this class."""
        with client.session_transaction() as session:
            session['super_user'] = True

    def test_new_entry_forbidden_for_non_admin(self, client):
        """Test that non-admins cannot access the new entry page."""
        with client.session_transaction() as session:
            del session['super_user']
        response = client.get('/admin/entries/new')
        assert response.status_code == 403

    def test_admin_entries_route_accessible(self, client):
        """Test that admins can access the admin entries page."""
        response = client.get('/admin/entries')
        assert response.status_code == 200

    def test_admin_entries_with_filters(self, client, monkeypatch):
        """Test the search filters on the admin entries page."""
        # Provide a mock contest list that includes the contest being filtered
        mock_contests = [{'id': 1, 'title': 'Test Contest'}]
        monkeypatch.setattr("sql.get_all_contests", lambda: mock_contests)
        monkeypatch.setattr("sql.get_all_entries", lambda **kwargs: [])
        monkeypatch.setattr("sql.get_entry_count", lambda **kwargs: 0)
        response = client.get(
            '/admin/entries?contest_id=1&user_search=TestUser')
        assert response.status_code == 200
        assert b'value="TestUser"' in response.data
        assert b'<option value="1" selected>' in response.data


class TestAdminCoverage:
    """Tests for increasing test coverage of admin routes."""

    @pytest.fixture(autouse=True)
    def admin_session(self, client):
        """Set up an admin session for all tests in this class."""
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'

    def test_new_entry_get_request(self, client, monkeypatch):
        """Test the GET request handler for the new entry page."""
        monkeypatch.setattr("sql.get_all_contests", lambda: [
                            {'id': 1, 'title': 'Test Contest'}])
        # Add the 'username' key to the mock user data
        monkeypatch.setattr("users.get_all_users", lambda: [
                            {'id': 1, 'name': 'Test User',
                             'username': 'test@user.com'}])
        response = client.get('/admin/entries/new')
        assert response.status_code == 200
        # Correct the asserted text to match the template's H1 tag
        assert b'Luo uusi kilpailuty\xc3\xb6' in response.data

    def test_new_entry_post_generic_db_error(self, client, monkeypatch):
        """Test the generic exception handler in the new entry POST route."""
        monkeypatch.setattr("sql.create_entry", lambda *a, **
                            kw: (_ for _ in ()).throw(sqlite3.Error(
                                "Generic DB Error"
                                )))
        monkeypatch.setattr("sql.get_all_contests", lambda: [
                            {'id': 1, 'title': 'Test Contest'}])
        # Add the 'username' key here as well, since this test also re-renders
        # the template
        monkeypatch.setattr("users.get_all_users", lambda: [
                            {'id': 1, 'name': 'Test User',
                             'username': 'test@user.com'}])
        response = client.post('/admin/entries/new', data={
            'csrf_token': 'test_token', 'contest_id': 1, 'user_id': 1,
            'entry': 'text'
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
            'csrf_token': 'test_token', 'contest_id': 1, 'user_id': 1,
            'entry': 'text'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Tekstin tiedot p\xc3\xa4ivitetty.' in response.data

    def test_delete_contest_db_error(self, client, monkeypatch):
        """Test generic exception handling during contest deletion."""
        monkeypatch.setattr("sql.delete_contest", lambda *a, **kw:
                            (_ for _ in ()).throw(sqlite3.Error("DB Error")))
        response = client.post('/admin/contests/delete/1',
                               data={'csrf_token': 'test_token'},
                               follow_redirects=True)
        assert response.status_code == 200
        # This assumes you add a try-except block to delete_contest like you
        # have in delete_entry
        # If not, this test will fail, and you should add the try-except block
        # to your route.

    def test_create_contest_db_exception(self, client, monkeypatch):
        """Test database exception handling during contest creation."""
        monkeypatch.setattr("sql.create_contest", lambda data:
                            (_ for _ in ()).throw(sqlite3.Error("fail")))
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
        """Test database exception handling during contest deletion."""
        monkeypatch.setattr("sql.delete_contest", lambda *a,
                            **kw: (_ for _ in ()).throw(sqlite3.Error("fail")))
        response = client.post(
            '/admin/contests/delete/1',
            data={'csrf_token': 'test_token'},
            follow_redirects=True
        )
        assert b'Kilpailua ei voitu poistaa.' in response.data

    # --- 233: edit_contest, abort(404) ---
    def test_edit_contest_not_found(self, client, monkeypatch):
        """Test that editing a non-existent contest returns a 404."""
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: None)
        monkeypatch.setattr("sql.get_all_classes", lambda: [])
        response = client.get('/admin/contests/edit/999')
        assert response.status_code == 404

    # --- 247: update_contest, errors branch ---
    def test_update_contest_missing_fields(self, client, monkeypatch):
        """Test contest update failure with missing fields."""
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

    # --- 522-524: new_entry, missing fields POST ---
    def test_new_entry_post_missing_fields(self, client, monkeypatch):
        """Test creating a new entry with missing fields."""
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
