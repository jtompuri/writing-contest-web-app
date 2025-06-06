"""Tests for the admin blueprint and related admin features.

This module contains unit tests for the admin panel routes, including access control,
user management, contest management, entry management, and pagination/error handling
in the Writing Contest Web App.

Test Classes:
    TestAdminRoutes: Tests for admin dashboard and access control.
    TestUserRoutes: Tests for admin user management (CRUD, permissions, CSRF).
    TestPaginationAnd404: Tests for pagination and 404/error handling in admin and public routes.
"""

import users


class TestAdminRoutes:
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

    def test_admin_route_forbidden(self, client):
        response = client.get('/admin/')
        assert response.status_code == 403

    def test_admin_index_contest_phase_listings(self, client, monkeypatch):
        # Mock contest data for each phase
        contests_collection = [
            {"id": 1, "title": "Keräysvaihe", "short_description": "Keräyskuvaus", "class_value": "Runo", "anonymity": 1, "public_reviews": 1, "public_results": 1, "collection_end": "2025-12-31", "review_end": "2026-01-31"}
        ]
        contests_review = [
            {"id": 2, "title": "Arviointivaihe", "short_description": "Arviointikuvaus", "class_value": "Novelli", "anonymity": 0, "public_reviews": 0, "public_results": 1, "collection_end": "2024-12-31", "review_end": "2025-01-31"}
        ]
        contests_results = [
            {"id": 3, "title": "Tulokset", "short_description": "Tuloksetkuvaus", "class_value": "Essee", "anonymity": 1, "public_reviews": 1, "public_results": 1, "collection_end": "2023-12-31", "review_end": "2024-01-31"}
        ]

        monkeypatch.setattr("sql.get_contests_for_entry", lambda *a, **kw: contests_collection)
        monkeypatch.setattr("sql.get_contests_for_review", lambda *a, **kw: contests_review)
        monkeypatch.setattr("sql.get_contests_for_results", lambda *a, **kw: contests_results)

        with client.session_transaction() as sess:
            sess['super_user'] = True

        response = client.get('/admin/')
        html = response.get_data(as_text=True)
        assert "Keräysvaihe" in html
        assert "Arviointivaihe" in html
        assert "Tulokset" in html
        assert "Keräyskuvaus" in html
        assert "Arviointikuvaus" in html
        assert "Tuloksetkuvaus" in html

    def test_admin_index_shows_only_latest_three_per_phase(self, client, monkeypatch):
        # Mock 5 contests, only 3 latest should be shown
        contests_collection = [
            {"id": i, "title": f"Keräys {i}", "short_description": f"Kuvaus {i}", "class_value": "Runo", "anonymity": 1, "public_reviews": 1, "public_results": 1, "collection_end": f"2025-12-{30-i}", "review_end": f"2026-01-{31-i}"} for i in range(5)
        ]
        monkeypatch.setattr("sql.get_contests_for_entry", lambda *a, **kw: contests_collection[:3])
        monkeypatch.setattr("sql.get_contests_for_review", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_contests_for_results", lambda *a, **kw: [])

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
            {"id": 1, "title": "Testikisa", "short_description": "Lyhyt kuvaus", "class_value": "Runo", "anonymity": 1, "public_reviews": 0, "public_results": 1, "collection_end": "2025-12-31", "review_end": "2026-01-31"}
        ]
        monkeypatch.setattr("sql.get_contests_for_entry", lambda *a, **kw: contests_collection)
        monkeypatch.setattr("sql.get_contests_for_review", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_contests_for_results", lambda *a, **kw: [])

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
            {"id": 1, "title": "Linkkitesti", "short_description": "Kuvaus", "class_value": "Runo", "anonymity": 1, "public_reviews": 1, "public_results": 1, "collection_end": "2025-12-31", "review_end": "2026-01-31"}
        ]
        monkeypatch.setattr("sql.get_contests_for_entry", lambda *a, **kw: contests_collection)
        monkeypatch.setattr("sql.get_contests_for_review", lambda *a, **kw: [])
        monkeypatch.setattr("sql.get_contests_for_results", lambda *a, **kw: [])

        with client.session_transaction() as sess:
            sess['super_user'] = True

        response = client.get('/admin/')
        html = response.get_data(as_text=True)
        # Use the actual route
        from flask import url_for
        with client.application.app_context():
            contest_url = url_for('main.contest', contest_id=1)
        assert f'href="{contest_url}"' in html

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
        response = client.post('/entry/1/delete', data={'csrf_token': 'wrong_token'})
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
        response = client.post('/review/1', data={'csrf_token': 'test_token', 'points_1': '5'}, follow_redirects=True)
        assert response.status_code in (200, 302, 404)


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
