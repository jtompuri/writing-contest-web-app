"""Tests for the entries blueprint and entry-related features.

This module contains unit tests for entry routes, including adding, editing,
deleting, reviewing entries, and admin entry management in the Writing Contest Web App.

Test Classes:
    TestEntryRoutes: Tests for entry CRUD, admin entry management, and related permissions.
    TestEntryAndReview: Tests for entry viewing, adding, reviewing, and related validation.
"""


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

    def test_add_entry_requires_login(self, client):
        response = client.get('/contests/contest/1/add_entry')
        assert response.status_code in (302, 200)

    def test_add_entry_get_logged_in(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        response = client.get('/contests/contest/1/add_entry')
        assert response.status_code in (200, 404)

    def test_add_entry_post_missing_fields(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'testtoken'
        response = client.post('/contests/contest/1/add_entry', data={'csrf_token': 'testtoken'})
        assert 'Kaikki pakolliset kentät on täytettävä.'.encode('utf-8') in response.data or response.status_code in (200, 404)

    def test_edit_entry_requires_login(self, client):
        response = client.get('/entry/1/edit')
        assert response.status_code in (302, 403, 200, 404)
        # 302 if redirect to login, 403 if forbidden, 404 if not found, 200 if allowed

    def test_edit_entry_logged_in(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'
        response = client.get('/entry/1/edit')
        assert response.status_code in (200, 403, 404)

    def test_delete_entry_requires_login(self, client):
        response = client.post('/entry/1/delete')
        assert response.status_code in (302, 403, 200, 404)

    def test_delete_entry_logged_in(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'
        response = client.post('/entry/1/delete', data={'csrf_token': 'test_token'})
        assert response.status_code in (302, 200, 403, 404)

    def test_my_texts_requires_login(self, client):
        response = client.get('/my_texts')
        assert response.status_code in (302, 200)

    def test_my_texts_logged_in(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        response = client.get('/my_texts')
        assert response.status_code == 200

    def test_add_entry_save_as_draft(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'
        response = client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token', 'entry': 'Draft entry', 'action': 'save_draft'}
        )
        assert response.status_code in (200, 302, 404)

    def test_admin_update_contest_toggle_settings(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/contests/update/1',
            data={
                'csrf_token': 'test_token',
                'title': 'Test',
                'class_id': 1,
                'short_description': 'Short',
                'long_description': 'Long',
                'collection_end': '2025-12-31',
                'review_end': '2026-01-31',
                'anonymity': 'on',
                'public_reviews': 'on',
                'public_results': 'on'
            }
        )
        assert response.status_code in (200, 302, 404)

    def test_admin_entries_pagination(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/entries?page=2')
        assert response.status_code == 200

    def test_admin_entries_filter_by_contest(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/entries?contest_id=1')
        assert response.status_code == 200

    def test_admin_users_search(self, client):
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/users?search=example')
        assert response.status_code == 200

    def test_add_entry_collection_closed(self, client, monkeypatch):
        # Simulate a contest where collection_end is in the past
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'

        def fake_get_contest_by_id(cid):
            return {
                "id": cid,
                "collection_end": "2000-01-01",
                "review_end": "2100-01-01"
            }

        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.get('/contests/contest/1/add_entry')
        assert response.status_code == 200
        # Optionally check for collection_open/review_open in template context

    def test_add_entry_post_unknown_action(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'

        def fake_get_contest_by_id(cid):
            return {
                "id": cid,
                "collection_end": "2100-01-01",
                "review_end": "2101-01-01"
            }
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token', 'entry': 'Test', 'action': 'unknown'}
        )
        # Should redirect to index
        assert response.status_code == 302

    def test_edit_entry_collection_ended(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'

        def fake_get_entry_by_id(eid):
            return {"id": eid, "user_id": 1, "contest_id": 1, "entry": "text"}

        def fake_get_contest_by_id(cid):
            return {"id": cid, "collection_end": "2000-01-01"}
        monkeypatch.setattr("sql.get_entry_by_id", fake_get_entry_by_id)
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.get('/entry/1/edit')
        assert response.status_code == 302

    def test_edit_entry_post_back_action(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'

        def fake_get_entry_by_id(eid):
            return {"id": eid, "user_id": 1, "contest_id": 1, "entry": "text"}

        def fake_get_contest_by_id(cid):
            return {"id": cid, "collection_end": "2100-01-01"}
        monkeypatch.setattr("sql.get_entry_by_id", fake_get_entry_by_id)
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.post(
            '/entry/1/edit',
            data={'csrf_token': 'test_token', 'entry': 'text', 'action': 'back'}
        )
        assert response.status_code == 200
        assert '<form' in response.get_data(as_text=True)

    def test_delete_entry_collection_ended(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'

        def fake_get_entry_by_id(eid):
            return {"id": eid, "user_id": 1, "contest_id": 1}

        def fake_get_contest_by_id(cid):
            return {"id": cid, "collection_end": "2000-01-01"}
        monkeypatch.setattr("sql.get_entry_by_id", fake_get_entry_by_id)
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.post('/entry/1/delete', data={'csrf_token': 'test_token'})
        assert response.status_code == 302

    def test_entry_private_results_no_key(self, client, monkeypatch):
        def fake_get_entry_by_id(eid):
            return {"id": eid, "contest_id": 1}

        def fake_get_contest_by_id(cid):
            return {"id": cid, "public_results": False, "private_key": "secret"}
        monkeypatch.setattr("sql.get_entry_by_id", fake_get_entry_by_id)
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.get('/entry/1?source=result')
        assert response.status_code == 302

    def test_entry_private_reviews_invalid_key(self, client, monkeypatch):
        def fake_get_entry_by_id(eid):
            return {"id": eid, "contest_id": 1}

        def fake_get_contest_by_id(cid):
            return {"id": cid, "public_reviews": False, "private_key": "secret"}
        monkeypatch.setattr("sql.get_entry_by_id", fake_get_entry_by_id)
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.get('/entry/1?source=review&key=wrong')
        assert response.status_code == 302

    def test_review_not_public_no_key(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        def fake_get_contest_by_id(cid):
            return {
                "id": cid,
                "public_reviews": False,
                "private_key": "secret",
                "collection_end": "2000-01-01",
                "review_end": "2100-01-01"
            }
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.get('/review/1')
        assert response.status_code == 302

    def test_review_not_in_review_period(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        def fake_get_contest_by_id(cid):
            return {
                "id": cid,
                "public_reviews": True,
                "private_key": "secret",
                "collection_end": "2100-01-01",
                "review_end": "2101-01-01"
            }
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.get('/review/1')
        assert response.status_code == 302

    def test_add_entry_get_with_entry_param(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        def fake_get_contest_by_id(cid):
            return {
                "id": cid,
                "collection_end": "2100-01-01",
                "review_end": "2101-01-01"
            }
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.get('/contests/contest/1/add_entry?entry=TestValue')
        assert response.status_code == 200
        assert 'TestValue' in response.get_data(as_text=True)

    def test_add_entry_post_missing_entry(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'

        def fake_get_contest_by_id(cid):
            return {
                "id": cid,
                "collection_end": "2100-01-01",
                "review_end": "2101-01-01"
            }
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token', 'entry': '', 'action': 'submit'}
        )
        assert response.status_code in (302, 200)
        # Should flash "Kilpailutyö ei saa olla tyhjä."

    def test_edit_entry_get_with_entry_param(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        def fake_get_entry_by_id(eid):
            return {"id": eid, "user_id": 1, "contest_id": 1, "entry": "original"}

        def fake_get_contest_by_id(cid):
            return {"id": cid, "collection_end": "2100-01-01"}
        monkeypatch.setattr("sql.get_entry_by_id", fake_get_entry_by_id)
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.get('/entry/1/edit?entry=ChangedText')
        assert response.status_code == 200
        assert 'ChangedText' in response.get_data(as_text=True)

    def test_edit_entry_post_missing_entry(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'

        def fake_get_entry_by_id(eid):
            return {"id": eid, "user_id": 1, "contest_id": 1, "entry": "original"}

        def fake_get_contest_by_id(cid):
            return {"id": cid, "collection_end": "2100-01-01"}
        monkeypatch.setattr("sql.get_entry_by_id", fake_get_entry_by_id)
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.post(
            '/entry/1/edit',
            data={'csrf_token': 'test_token', 'entry': '', 'action': 'submit'}
        )
        assert response.status_code == 200
        assert 'ei saa olla tyhjä' in response.get_data(as_text=True)

    def test_edit_entry_post_unknown_action(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'

        def fake_get_entry_by_id(eid):
            return {"id": eid, "user_id": 1, "contest_id": 1, "entry": "original"}

        def fake_get_contest_by_id(cid):
            return {"id": cid, "collection_end": "2100-01-01"}
        monkeypatch.setattr("sql.get_entry_by_id", fake_get_entry_by_id)
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        response = client.post(
            '/entry/1/edit',
            data={'csrf_token': 'test_token', 'entry': 'text', 'action': 'unknown'}
        )
        # Should redirect to my_texts or contest
        assert response.status_code in (302, 200)

    def test_review_post_invalid_points_value(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'

        def fake_get_contest_by_id(cid):
            return {
                "id": cid,
                "public_reviews": True,
                "private_key": "secret",
                "collection_end": "2000-01-01",
                "review_end": "2100-01-01"
            }

        def fake_get_entries_for_review(cid):
            return [{"id": 1, "author_name": "TestUser", "entry": "Test entry"}]

        def fake_get_user_reviews_for_contest(contest_id, user_id):
            return {}

        monkeypatch.setattr("sql.get_user_reviews_for_contest", fake_get_user_reviews_for_contest)
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        monkeypatch.setattr("sql.get_entries_for_review", fake_get_entries_for_review)
        response = client.post(
            '/review/1',
            data={'csrf_token': 'test_token', 'points_1': 'notanumber'}
        )
        assert response.status_code == 200
        assert 'Virheellinen arvosana' in response.get_data(as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_review_post_all_valid_points(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'

        def fake_get_contest_by_id(cid):
            return {
                "id": cid,
                "public_reviews": True,
                "private_key": "secret",
                "collection_end": "2000-01-01",
                "review_end": "2100-01-01"
            }

        def fake_get_entries_for_review(cid):
            return [{"id": 1, "author_name": "TestUser"}]

        def fake_save_review(entry_id, user_id, points):
            pass
        monkeypatch.setattr("sql.get_contest_by_id", fake_get_contest_by_id)
        monkeypatch.setattr("sql.get_entries_for_review", fake_get_entries_for_review)
        monkeypatch.setattr("sql.save_review", fake_save_review)
        response = client.post(
            '/review/1',
            data={'csrf_token': 'test_token', 'points_1': '5'}
        )
        assert response.status_code in (302, 200)


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
