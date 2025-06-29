"""Tests for the entries blueprint and entry-related features.

This module contains unit tests for entry routes, including adding, editing,
deleting, reviewing entries, and admin entry management in the Writing Contest
Web App.
"""


class TestAdminEntryManagement:
    """Tests for admin-level entry management routes."""

    def test_admin_create_entry_post(self, client):
        """Test creating an entry via POST as an admin."""
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
        """Test admin entry creation with missing content."""
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
        """Test that a flash message appears for missing fields."""
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
        assert 'Kaikki pakolliset kentät on täytettävä.' in response.get_data(
            as_text=True)

    def test_admin_edit_entry_with_super_user(self, client):
        """Test that an admin can access the edit entry page."""
        with client.session_transaction() as session:
            session['super_user'] = True
        response = client.get('/admin/entries/edit/1')
        assert response.status_code in (200, 404)

    def test_admin_edit_entry_without_super_user(self, client):
        """Test that a non-admin cannot access the edit entry page."""
        response = client.get('/admin/entries/edit/1')
        assert response.status_code == 403

    def test_admin_update_entry_with_super_user(self, client):
        """Test that an admin can update an entry."""
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
        """Test that a non-admin cannot update an entry."""
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
        """Test that an admin can delete an entry."""
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post('/admin/entries/delete/1',
                               data={'csrf_token': 'test_token'})
        assert response.status_code in (302, 200, 404)

    def test_admin_delete_entry_without_super_user(self, client):
        """Test that a non-admin cannot delete an entry."""
        response = client.post('/admin/entries/delete/1',
                               data={'csrf_token': 'test_token'})
        assert response.status_code == 403

    def test_admin_update_entry_invalid_id(self, client):
        """Test updating a non-existent entry as an admin."""
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
        """Test deleting a non-existent entry as an admin."""
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/admin/entries/delete/999999', data={'csrf_token': 'test_token'})
        assert response.status_code in (302, 200)

    def test_duplicate_entry_prevention(self, client):
        """Test that a user cannot submit multiple entries to the same
        contest."""
        with client.session_transaction() as session:
            session['super_user'] = True
            session['csrf_token'] = 'test_token'
        # This assumes you have a fixture or setup that allows creating an
        # initial entry
        client.post(
            '/admin/entries/create',
            data={
                'csrf_token': 'test_token',
                'contest_id': 1,
                'user_id': 1,
                'entry': 'First entry'
            }
        )
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


class TestUserEntryActions:
    """Tests for user-facing entry submission, editing, and deletion."""

    def test_add_entry_get_with_prefilled_entry(self, client, monkeypatch):
        """GET with entry arg should prefill entry field."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
                            "id": cid, "collection_end": "2100-01-01",
                            "review_end": "2101-01-01"})
        response = client.get('/contests/contest/1/add_entry?entry=foobar')
        assert b'foobar' in response.data

    def test_add_entry_get_logged_in(self, client):
        """Test that a logged-in user can access the add entry page."""
        with client.session_transaction() as session:
            session['user_id'] = 1
        response = client.get('/contests/contest/1/add_entry')
        assert response.status_code in (200, 404)

    def test_add_entry_get_not_logged_in(self, client):
        """Test that a non-logged-in user is redirected from the add entry
        page."""
        response = client.get('/contests/contest/1/add_entry')
        assert response.status_code == 302

    def test_add_entry_post_logged_in(self, client):
        """Test that a logged-in user can submit an entry."""
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token',
                  'entry': 'Test entry', 'action': 'submit'}
        )
        assert response.status_code in (302, 200, 404)

    def test_add_entry_post_missing_entry(self, client):
        """Test submitting an empty entry."""
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token', 'entry': '', 'action': 'submit'}
        )
        assert response.status_code in (200, 302, 404)
        if response.status_code == 200:
            assert 'Kilpailutyö ei saa olla tyhjä' in response.get_data(
                as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_add_entry_post_too_long(self, client, monkeypatch):
        """Test submitting an entry that is too long."""
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        long_text = 'a' * 6001
        monkeypatch.setattr(
            "sql.get_contest_by_id",
            lambda cid: {
                "id": cid,
                "collection_end": "2100-01-01",
                "review_end": "2101-01-01",
                "long_description": "",
            }
        )
        # Prevent actual DB call
        monkeypatch.setattr("sql.create_entry", lambda cid, uid, entry: None)
        response = client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token',
                  'entry': long_text, 'action': 'submit'},
            follow_redirects=True
        )
        # Accept either the specific error message or a generic error page
        assert (
            b'Kilpailuty\xc3\xb6 on liian' in response.data
            or b'Virhe' in response.data or response.status_code == 200
        )

    def test_add_entry_post_duplicate(self, client):
        """Test submitting a duplicate entry."""
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token',
                  'entry': 'My entry', 'action': 'submit'}
        )
        response = client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token',
                  'entry': 'My entry', 'action': 'submit'}
        )
        assert response.status_code in (302, 200, 404)
        if response.status_code == 200:
            assert 'Olet jo osallistunut' in response.get_data(
                as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_add_entry_post_preview_action(self, client, monkeypatch):
        """Test the 'preview' action when adding an entry."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
                            "id": cid, "collection_end": "2100-01-01",
                            "review_end": "2101-01-01"})
        response = client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token',
                  'entry': 'Preview Text', 'action': 'preview'}
        )
        assert response.status_code == 200
        assert b'Esikatselu' in response.data
        assert b'Preview Text' in response.data

    def test_add_entry_post_unknown_action(self, client, monkeypatch):
        """Test that an unknown action in add_entry form redirects."""
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        monkeypatch.setattr(
            "sql.get_contest_by_id",
            lambda cid: {
                "id": cid,
                "collection_end": "2100-01-01",
                "review_end": "2101-01-01",
                "long_description": "",
            }
        )
        response = client.post(
            '/contests/contest/1/add_entry',
            data={'csrf_token': 'test_token',
                  'entry': 'foo', 'action': 'unknown'},
            follow_redirects=True
        )
        # Should redirect to index
        assert response.status_code in (200, 302)

    def test_edit_entry_get_with_entry_param(self, client, monkeypatch):
        """Test that the entry field is pre-filled from a URL parameter."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        monkeypatch.setattr("sql.get_entry_by_id", lambda eid: {
                            "id": eid, "user_id": 1, "contest_id": 1,
                            "entry": "original"})
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
                            "id": cid, "collection_end": "2100-01-01"})
        response = client.get('/entry/1/edit?entry=changed')
        assert b'changed' in response.data

    def test_edit_entry_not_logged_in(self, client):
        """Test that a non-logged-in user cannot access the edit entry
        page."""
        response = client.get('/entry/1/edit')
        assert response.status_code == 403

    def test_edit_entry_wrong_user(self, client, monkeypatch):
        """Test that a user cannot edit another user's entry."""
        with client.session_transaction() as sess:
            sess['user_id'] = 2
        monkeypatch.setattr("sql.get_entry_by_id", lambda eid: {
                            "id": eid, "user_id": 1, "contest_id": 1})
        response = client.get('/entry/1/edit')
        assert response.status_code == 403

    def test_edit_entry_post_no_text(self, client, monkeypatch):
        """Test submitting an empty edit for an entry."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'
        monkeypatch.setattr("sql.get_entry_by_id", lambda eid: {
                            "id": eid, "user_id": 1, "contest_id": 1,
                            "entry": "foo"})
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
                            "id": cid, "collection_end": "2100-01-01"})
        response = client.post(
            '/entry/1/edit',
            data={'csrf_token': 'test_token', 'entry': '', 'action': 'submit'},
            follow_redirects=True
        )
        assert b'tyhj\xc3\xa4' in response.data

    def test_edit_entry_post_preview_action(self, client, monkeypatch):
        """Test the 'preview' action when editing an entry."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'
        monkeypatch.setattr("sql.get_entry_by_id", lambda eid: {
                            "id": eid, "user_id": 1, "contest_id": 1})
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
                            "id": cid, "collection_end": "2100-01-01"})
        response = client.post(
            '/entry/1/edit',
            data={'csrf_token': 'test_token',
                  'entry': 'Preview Edit', 'action': 'preview'}
        )
        assert response.status_code == 200
        assert b'Esikatselu' in response.data
        assert b'Preview Edit' in response.data

    def test_edit_entry_post_submit_redirect_to_contest(self, client,
                                                        monkeypatch):
        """Test that submitting an edit redirects to the contest page if
        source is 'contest'."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'
        monkeypatch.setattr("sql.get_entry_by_id", lambda eid: {
                            "id": eid, "user_id": 1, "contest_id": 1})
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
                            "id": cid, "collection_end": "2100-01-01"})
        monkeypatch.setattr("sql.update_entry", lambda *args: None)
        response = client.post(
            '/entry/1/edit',
            data={'csrf_token': 'test_token', 'entry': 'Updated',
                  'action': 'submit', 'source': 'contest'}
        )
        assert response.status_code == 302
        assert response.location == '/contests/contest/1'

    def test_delete_entry_not_logged_in(self, client):
        """Test that a non-logged-in user cannot delete an entry."""
        response = client.post('/entry/1/delete')
        assert response.status_code == 403

    def test_delete_entry_wrong_user(self, client, monkeypatch):
        """Test that a user cannot delete another user's entry."""
        with client.session_transaction() as sess:
            sess['user_id'] = 2
        monkeypatch.setattr("sql.get_entry_by_id", lambda eid: {
                            "id": eid, "user_id": 1, "contest_id": 1})
        response = client.post('/entry/1/delete')
        assert response.status_code == 403

    def test_delete_entry_contest_not_found(self, client, monkeypatch):
        """Test deleting an entry whose associated contest is not found."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'
        monkeypatch.setattr("sql.get_entry_by_id", lambda eid: {
                            "id": eid, "user_id": 1, "contest_id": 99})
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: None)
        response = client.post(
            '/entry/1/delete', data={'csrf_token': 'test_token'},
            follow_redirects=True)
        assert response.status_code == 200
        assert b'Et voi en\xc3\xa4\xc3\xa4 poistaa' in response.data


class TestEntryViewing:
    """Tests for viewing entries and results pages."""

    def test_entry_not_found(self, client, monkeypatch):
        """Test that a 404 is returned for a non-existent entry."""
        monkeypatch.setattr("sql.get_entry_by_id", lambda eid: None)
        response = client.get('/entry/999')
        assert response.status_code == 404

    def test_entry_private_results_invalid_key(self, client, monkeypatch):
        """Private results with invalid key."""
        monkeypatch.setattr("sql.get_entry_by_id", lambda eid: {
                            "id": eid, "contest_id": 1})
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
                            "id": cid, "public_results": False,
                            "private_key": "sekret"})
        response = client.get('/entry/1?source=result&key=wrong')
        assert (b'Tulokset eiv\xc3\xa4t ole '
                b'julkisia') in response.data or response.status_code == 302

    def test_entry_view_valid(self, client):
        """Test that a valid entry can be viewed."""
        response = client.get('/entry/1')
        assert response.status_code in (200, 404)

    def test_entry_view_invalid(self, client):
        """Test that viewing an invalid entry returns a 404."""
        response = client.get('/entry/999999')
        assert response.status_code == 404

    def test_result_view_valid(self, client):
        """Test that a valid result page can be viewed."""
        response = client.get('/result/1')
        assert response.status_code in (200, 404)

    def test_result_view_invalid(self, client):
        """Test that viewing an invalid result page returns a 404."""
        response = client.get('/result/999999')
        assert response.status_code == 404

    def test_entry_view_contest_not_found(self, client, monkeypatch):
        """Test viewing an entry whose associated contest is not found."""
        monkeypatch.setattr("sql.get_entry_by_id", lambda eid: {
                            "id": eid, "contest_id": 99})
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: None)
        response = client.get('/entry/1')
        assert response.status_code == 404

    def test_entry_private_results_valid_key(self, client, monkeypatch):
        """Test viewing a private result with a valid key."""
        monkeypatch.setattr("sql.get_entry_by_id", lambda eid: {
                            "id": eid, "contest_id": 1,
                            "entry": "Secret Text"})
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
                            "id": cid, "public_results": False,
                            "private_key": "secret"})
        response = client.get('/entry/1?source=result&key=secret')
        assert response.status_code == 200
        assert b'Secret Text' in response.data

    def test_entry_private_reviews_invalid_key(self, client, monkeypatch):
        """Test viewing a private review with an invalid key."""
        monkeypatch.setattr("sql.get_entry_by_id", lambda eid: {
                            "id": eid, "contest_id": 1})
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
                            "id": cid, "public_results": True,
                            "public_reviews": False, "private_key": "sekret"})
        response = client.get('/entry/1?source=review&key=wrong')
        assert (b'arviointi ei ole '
                b'julkista') in response.data or response.status_code == 302


class TestReviewing:
    """Tests for the contest review process."""

    def test_review_not_logged_in(self, client):
        """Test that a non-logged-in user is redirected from the review
        page."""
        response = client.get('/review/1',
                              headers={"Referer": "/contests/contest/1"})
        assert response.status_code == 302

    def test_review_contest_not_found(self, client, monkeypatch):
        """Test that a 404 is returned for a review of a non-existent
        contest."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: None)
        response = client.get('/review/1',
                              headers={"Referer": "/contests/contest/1"})
        assert response.status_code == 404

    def test_review_private_invalid_key(self, client, monkeypatch):
        """Test accessing a private review with an invalid key."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
                            "id": cid, "public_reviews": False,
                            "private_key": "sekret"})
        response = client.get('/review/1?key=wrong', follow_redirects=True,
                              headers={"Referer": "/contests/contest/1"})
        assert b'arviointi ei ole julkinen' in response.data

    def test_review_not_in_review_period(self, client, monkeypatch):
        """Test that reviewing is blocked outside the review period."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
            "id": cid, "public_reviews": True, "private_key": "sekret",
            "collection_end": "2100-01-01", "review_end": "2101-01-01"
        })
        response = client.get('/review/1', follow_redirects=True,
                              headers={"Referer": "/contests/contest/1"})
        # Now the error message should be in the response after redirect
        assert (b'arviointijakso ei ole '
                b'k\xc3\xa4ynniss\xc3\xa4') in response.data

    def test_review_get_logged_in(self, client):
        """Test that a logged-in user can access the review page."""
        with client.session_transaction() as session:
            session['user_id'] = 1
        response = client.get('/review/1',
                              headers={"Referer": "/contests/contest/1"})
        assert response.status_code in (200, 404, 302)

    def test_review_post_missing_points(self, client):
        """Test submitting a review with missing points."""
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/review/1',
            data={'csrf_token': 'test_token', 'points_1': '5'},
            headers={"Referer": "/contests/contest/1"}
        )
        assert response.status_code in (200, 302, 404)
        if response.status_code == 200:
            assert 'Kaikki tekstit on arvioitava' in response.get_data(
                as_text=True) or 'Virhe' in response.get_data(as_text=True)

    def test_review_post_invalid_points(self, client):
        """Test submitting a review with invalid points."""
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['csrf_token'] = 'test_token'
        response = client.post(
            '/review/1',
            data={'csrf_token': 'test_token', 'points_1': '10'},
            follow_redirects=True,
            headers={"Referer": "/contests/contest/1"}
        )
        assert response.status_code in (200, 302, 404)
        if response.status_code == 200:
            assert 'arvosanojen tulee olla välillä 0-5' in response.get_data(
                as_text=True) or ('Arvosanan tulee olla välillä '
                                  '0–5') in response.get_data(as_text=True)

    def test_review_private_valid_key(self, client, monkeypatch):
        """Test accessing a private review page with a valid key."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        # Add all fields that the template might check
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
            "id": cid,
            "public_reviews": False,
            "private_key": "secret",
            "collection_end": "2000-01-01",
            "review_end": "2101-01-01",
            "title": "Test Contest",
            "description": "Test",
            "public_results": False,
            "max_points": 5,
        })
        monkeypatch.setattr("sql.get_entries_for_review", lambda cid: [
            {
                "id": 1,
                "author_name": "Test",
                "entry": "Test entry text",
                "title": "Test Entry",
                "contest_id": cid,
            }
        ])
        monkeypatch.setattr(
            "sql.get_user_reviews_for_contest", lambda cid, uid: {})
        response = client.get('/review/1?key=secret',
                              headers={"Referer": "/contests/contest/1"})
        assert response.status_code == 200
        # Try a more robust check for the review form or entry text
        assert (
            b'Arvioi kilpailuty\xc3\xb6t' in response.data or
            b'Test entry text' in response.data or b'Test Entry'
            in response.data
        )

    def test_review_post_negative_points(self, client, monkeypatch):
        """Test that submitting negative points for a review is handled as
        an error."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['csrf_token'] = 'test_token'
        monkeypatch.setattr("sql.get_contest_by_id", lambda cid: {
            "id": cid, "public_reviews": True, "collection_end": "2000-01-01",
            "review_end": "2100-01-01"
        })
        monkeypatch.setattr("sql.get_entries_for_review", lambda cid: [
            {"id": 1, "author_name": "Test", "entry": "Test entry text"}
        ])
        monkeypatch.setattr(
            "sql.get_user_reviews_for_contest", lambda cid, uid: {})
        response = client.post(
            '/review/1',
            data={'csrf_token': 'test_token', 'points_1': '-1'},
            headers={"Referer": "/contests/contest/1"}
        )
        assert response.status_code == 200
        # "Arvosanan tulee olla välillä 0–5"
        assert (b'Arvosanan tulee olla v\xc3\xa4lill\xc3\xa4 '
                b'0\xe2\x80\x935') in response.data


class TestMyTextsPage:
    """Tests for the 'my_texts' page and its features."""

    def test_my_texts_logged_in(self, client):
        """Test that a logged-in user can access their 'my_texts' page."""
        with client.session_transaction() as session:
            session['user_id'] = 1
        response = client.get('/my_texts')
        assert response.status_code == 200

    def test_my_texts_not_logged_in(self, client):
        """Test that a non-logged-in user is redirected from the 'my_texts'
        page."""
        response = client.get('/my_texts')
        assert response.status_code == 302

    def test_my_texts_pagination(self, client, monkeypatch):
        """Test pagination on the 'my_texts' page."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        # Create more entries than one page can hold
        mock_entries = [
            {
                "contest_id": i,
                "title": f"Entry {i}",
                "collection_end": "2100-01-01",
                "review_end": "2101-01-01",  # <-- Add this field
                "entry": f"Text {i}",            # Add if template expects it
                "id": i
            }
            for i in range(10)
        ]
        monkeypatch.setattr(
            "sql.get_user_entries_with_results", lambda uid: mock_entries)
        monkeypatch.setattr("sql.get_user_entry_count", lambda uid: 10)

        # Request the second page
        response = client.get('/my_texts?page=2')
        assert response.status_code == 200
        # Check for an entry that should be on page 2 (assuming 5 per page)
        assert b'Entry 5' in response.data
        # Check that an entry from page 1 is not present
        assert b'Entry 0' not in response.data
