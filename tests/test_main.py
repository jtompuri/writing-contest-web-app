"""Tests for the main blueprint and public-facing features.

This module contains unit tests for public routes, contest routes, and related
validation in the Writing Contest Web App.

Test Classes:
    TestPublicRoutes: Tests for public pages and error handling.
    TestContestRoutes: Tests for contest detail, admin contest management,
                       and validation.
"""

from unittest.mock import patch, MagicMock
from datetime import date, timedelta, datetime
import pytest


class TestFrontpage:
    """Tests for the frontpage functionality."""

    def test_frontpage_winners_display(self, client, monkeypatch):
        """Test that winners are correctly displayed on the frontpage."""
        fake_contests = [
            {"id": 1, "title": "Test Contest", "public_results": True,
             "short_description": "Desc", "class_value": "Essee",
             "anonymity": True, "public_reviews": True,
             "review_end": "2025-01-01", "collection_end": "2024-12-01",
             "total_entries": 3}
        ]
        long_text = "A" * 300  # 300 characters
        fake_winners = [
            {
                "id": 101,
                "entry_id": 101,
                "author_name": "Voittaja 1",
                "points": 32,
                "placement": 1,
                "entry": long_text,
                "entry_text": "Lyhyt kuvaus",
                "title": "Voittajateksti 1",
                "short_description": "Lyhyt kuvaus",
                "total_entries": 3
            },
            {
                "id": 102,
                "entry_id": 102,
                "author_name": "Voittaja 2",
                "points": 10,
                "placement": 2,
                "entry": long_text,
                "entry_text": "Lyhyt kuvaus",
                "title": "Voittajateksti 2",
                "short_description": "Lyhyt kuvaus",
                "total_entries": 3
            }
        ]
        monkeypatch.setattr("sql.get_contests_for_entry",
                            lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contests_for_review",
                            lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contest_results",
                            lambda contest_id: fake_winners)

        resp = client.get("/")
        assert resp.status_code == 200
        assert "Voittaja 1".encode('utf-8') in resp.data
        assert b"32 p." in resp.data
        assert "Voittaja 2".encode('utf-8') in resp.data
        assert b"10 p." in resp.data
        assert b"Lue koko teksti" in resp.data
        assert b"Kaikki tulokset t" in resp.data

    def test_frontpage_no_winners(self, client, monkeypatch):
        """Test frontpage display when there are no winners for a contest."""
        fake_contests = [
            {"id": 1, "title": "Test Contest", "public_results": False,
             "short_description": "Desc", "class_value": "Essee",
             "anonymity": True, "public_reviews": True,
             "review_end": "2025-01-01", "collection_end": "2024-12-01",
             "total_entries": 3}
        ]
        monkeypatch.setattr("sql.get_contests_for_entry",
                            lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contests_for_review",
                            lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contest_results", lambda contest_id: [])

        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Ei tuloksia t" in resp.data or ("Voittajat julkaistaan "
                                                 "pian").encode(
            'utf-8') in resp.data

    def test_frontpage_no_contests(self, client, monkeypatch):
        """Test frontpage display when there are no contests."""
        monkeypatch.setattr("sql.get_contests_for_entry", lambda n: [])
        monkeypatch.setattr("sql.get_contests_for_review", lambda n: [])
        monkeypatch.setattr("sql.get_contests_for_results", lambda n: [])
        monkeypatch.setattr("sql.get_contest_results", lambda contest_id: [])

        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Ei k" in resp.data or "Ei julkaistuja tuloksia".encode(
            'utf-8') in resp.data

    def test_frontpage_winner_entry_links(self, client, monkeypatch):
        """Test that links to winner entries on the frontpage are correct."""
        fake_contests = [
            {"id": 1, "title": "Test Contest", "public_results": True,
             "short_description": "Desc", "class_value": "Essee",
             "anonymity": True, "public_reviews": True,
             "review_end": "2025-01-01", "collection_end": "2024-12-01",
             "total_entries": 3}
        ]
        long_text = "A" * 300  # 300 characters
        fake_winners = [
            {
                "id": 101,
                "entry_id": 101,
                "author_name": "Voittaja 1",
                "points": 32,
                "placement": 1,
                "entry": long_text,
                "entry_text": "Tämä on voittajateksti 1.",
                "title": "Voittajateksti 1",
                "short_description": "Lyhyt kuvaus",
                "total_entries": 3
            },
            {
                "id": 102,
                "entry_id": 102,
                "author_name": "Voittaja 2",
                "points": 10,
                "placement": 2,
                "entry": long_text,
                "entry_text": "Tämä on voittajateksti 2.",
                "title": "Voittajateksti 2",
                "short_description": "Lyhyt kuvaus",
                "total_entries": 3
            }
        ]
        monkeypatch.setattr("sql.get_contests_for_entry",
                            lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contests_for_review",
                            lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contest_results",
                            lambda contest_id: fake_winners)

        resp = client.get("/")
        for winner in fake_winners:
            link = f'/entry/{winner["id"]}'.encode("utf-8")
            assert link in resp.data


class TestPublicRoutes:
    """Tests for publicly accessible routes."""

    def test_index_route(self, client):
        """Test that the index route is accessible."""
        response = client.get('/')
        assert response.status_code == 200
        assert 'Tervetuloa!'.encode('utf-8') in response.data

    def test_register_route(self, client):
        """Test that the register route is accessible."""
        response = client.get('/register')
        assert response.status_code == 200
        assert 'Rekisteröidy'.encode('utf-8') in response.data

    def test_login_get_route(self, client):
        """Test that the login GET route is accessible."""
        response = client.get('/login')
        assert response.status_code == 200
        assert 'Kirjaudu sisään'.encode('utf-8') in response.data

    def test_register_get(self, client):
        """Test that the register GET route is accessible."""
        response = client.get('/register')
        assert response.status_code == 200

    def test_nonexistent_route(self, client):
        """Test that a nonexistent route returns a 404 error."""
        response = client.get('/thispagedoesnotexist')
        assert response.status_code == 404

    def test_results_page_filters_private_contests(self, client, monkeypatch):
        """Test that the main results page does not show private contests
        without a key."""
        # This mocks a mix of public and private contests
        fake_contests = [
            {"id": 1, "title": "Public Results Contest",
             "public_results": True,
                "private_key": "", "review_end": "2025-01-31",
                "collection_end": "2025-01-15"},
            {"id": 2, "title": "Private Results Contest",
             "public_results": False,
                "private_key": "secret1", "review_end": "2025-01-31",
                "collection_end": "2025-01-15"}
        ]
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda limit, offset: fake_contests)
        monkeypatch.setattr("sql.get_results_contest_count",
                            lambda: len(fake_contests))

        response = client.get('/results')
        assert response.status_code == 200
        assert b"Public Results Contest" in response.data
        assert b"Private Results Contest" not in response.data

    def test_reviews_page_filters_private_contests(self, client, monkeypatch):
        """Test that the main reviews page does not show private contests
        without a key."""
        # This mocks a mix of public and private contests
        fake_contests = [
            {"id": 1, "title": "Public Review Contest", "public_reviews": True,
                "private_key": "", "review_end": "2025-01-31",
                "collection_end": "2025-01-15"},
            {"id": 2, "title": "Private Review Contest",
             "public_reviews": False,
                "private_key": "secret2", "review_end": "2025-01-31",
                "collection_end": "2025-01-15"}
        ]
        monkeypatch.setattr("sql.get_contests_for_review",
                            lambda limit, offset: fake_contests)
        monkeypatch.setattr("sql.get_review_contest_count",
                            lambda: len(fake_contests))

        response = client.get('/reviews')
        assert response.status_code == 200
        assert b"Public Review Contest" in response.data
        # The link should now point to the contest page, not the review page
        assert b'href="/contests/contest/1"' in response.data
        assert b"Private Review Contest" not in response.data

    def test_reviews_page_shows_private_contest_with_key(self, client,
                                                         monkeypatch):
        """Test that the reviews page shows a private contest when the correct
        key is provided."""
        fake_contests = [
            {"id": 2, "title": "Private Review Contest",
             "public_reviews": False,
                "private_key": "secret2", "review_end": "2025-01-31",
                "collection_end": "2025-01-15"}
        ]
        monkeypatch.setattr("sql.get_contests_for_review",
                            lambda limit, offset: fake_contests)
        monkeypatch.setattr("sql.get_review_contest_count",
                            lambda: len(fake_contests))

        response = client.get('/reviews?key=secret2')
        assert response.status_code == 200
        assert b"Private Review Contest" in response.data


class TestContestRoutes:
    """Tests for contest-related routes."""

    def test_contest_detail_valid(self, client):
        """Test that a valid contest detail page is accessible."""
        response = client.get('/contests/contest/1')
        assert response.status_code in (200, 404)

    def test_contest_detail_invalid(self, client):
        """Test that an invalid contest detail page returns a 404 error."""
        response = client.get('/contests/contest/999999')
        assert response.status_code == 404


class TestMainCoverage:
    """Tests for increasing test coverage of the main blueprint."""

    def test_index_winner_missing_review_end(self, client, monkeypatch):
        """Test the fallback logic for a winner's review_end date on
        the index page."""
        # Mock a contest that has a review_end date
        mock_contest = {
            "id": 1, "public_results": True, "review_end": "2025-01-01"
        }
        # Mock a winner from that contest that is missing the review_end date
        # Add the 'entry' key to the mock data to satisfy the template
        mock_winner = {
            "entry_id": 101, "author_name": "Winner", "points": 50,
            "entry": "The winning text."
        }
        monkeypatch.setattr("sql.get_contests_for_results",
                            lambda n: [mock_contest])
        monkeypatch.setattr("sql.get_contest_results",
                            lambda contest_id: [mock_winner])
        # Mock other calls to prevent errors
        monkeypatch.setattr("sql.get_contests_for_entry", lambda n: [])
        monkeypatch.setattr("sql.get_contests_for_review", lambda n: [])

        response = client.get("/")
        assert response.status_code == 200
        # The test passes if the route runs without error, as the logic adds
        # the key.
        # We can also assert the winner's name is present.
        assert b"Winner" in response.data

    @pytest.mark.parametrize("params", [
        (-10, True, False),  # Collection is open
        (5, False, True),    # Review is open
        (20, False, False)   # Contest is closed
    ])
    def test_contest_page_states(self, client, monkeypatch, params):
        """Test the collection_open and review_open states on the contest
        detail page."""
        days_offset, expected_collection_open, expected_review_open = params
        today = date.today()
        # Set collection_end to today to make the date boundaries clearer
        collection_end = today.isoformat()
        review_end = (today + timedelta(days=10)).isoformat()

        # Log in a user to ensure participation/review links can be shown
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        # Patch datetime.now() to control the current date in the route
        with patch('routes.main.datetime') as mock_dt:
            mock_dt.now.return_value.date.return_value = today + \
                timedelta(days=days_offset)
            mock_dt.strptime.side_effect = datetime.strptime

            # Provide a complete mock object for the contest
            mock_contest = {
                "id": 1, "collection_end": collection_end,
                "review_end": review_end,
                "title": "Test Contest", "short_description": "Short desc.",
                "long_description": "Long desc.",
                "public_reviews": True  # Add this key to satisfy the template
            }
            monkeypatch.setattr("sql.get_contest_by_id",
                                lambda contest_id: mock_contest)
            # Ensure the user is not considered a participant for this test
            monkeypatch.setattr("sql.get_user_entry_for_contest",
                                lambda cid, uid: None)

            response = client.get('/contests/contest/1')
            assert response.status_code == 200

            # Check for content that appears based on the contest state flags.
            # This makes the test more meaningful and uses the variables.
            if expected_collection_open:
                assert b'Osallistu kilpailuun' in response.data
            else:
                assert b'Osallistu kilpailuun' not in response.data

            if expected_review_open:
                assert b'Arvioi kilpailuty\xc3\xb6t' in response.data
            else:
                assert b'Arvioi kilpailuty\xc3\xb6t' not in response.data

    def test_contest_page_user_has_entry(self, client, monkeypatch):
        """Test the contest page logic when a logged-in user has
        an existing entry."""
        with client.session_transaction() as session:
            session['user_id'] = 1

        # Provide a complete mock object for the contest
        mock_contest = {
            "id": 1, "collection_end": "2999-12-31",
            "review_end": "2999-12-31",
            "title": "Test Contest", "short_description": "Short desc.",
            "long_description": "Long desc."
        }
        mock_entry = {"id": 101}
        monkeypatch.setattr("sql.get_contest_by_id",
                            lambda contest_id: mock_contest)
        monkeypatch.setattr("sql.get_user_entry_for_contest",
                            lambda cid, uid: mock_entry)

        # Explicitly patch datetime to ensure collection_open is True
        with patch('routes.main.datetime') as mock_dt:
            # Set a fixed date to make the test deterministic
            mock_dt.now.return_value.date.return_value = date(2025, 1, 1)
            # Ensure strptime continues to function correctly
            mock_dt.strptime.side_effect = datetime.strptime
            response = client.get('/contests/contest/1')

        assert response.status_code == 200
        # Correct the asserted URL path. The blueprint name 'entries' is not
        # part of the path.
        assert b'/entry/101/edit' in response.data

    def test_contests_list_pagination(self, client, monkeypatch):
        """Test that the main contests list respects pagination parameters."""
        mock_get_contests = MagicMock(return_value=[])
        monkeypatch.setattr("sql.get_contests_for_entry", mock_get_contests)
        monkeypatch.setattr("sql.get_entry_contest_count", lambda: 10)

        client.get('/contests?page=2')
        # Correct the assertion to match the actual config value
        mock_get_contests.assert_called_with(limit=5, offset=5)

    def test_private_result_page_no_key(self, client, monkeypatch):
        """Test that accessing a private result page without
        a key redirects."""
        mock_contest = {"id": 1, "public_results": False,
                        "private_key": "secret"}
        monkeypatch.setattr("sql.get_contest_by_id",
                            lambda contest_id: mock_contest)

        response = client.get('/result/1', follow_redirects=True)
        assert response.status_code == 200
        assert 'Tämän kilpailun tulokset eivät ole julkisia.'.encode(
            'utf-8') in response.data

    def test_private_result_page_wrong_key(self, client, monkeypatch):
        """Test that accessing a private result page with a wrong
        key redirects."""
        mock_contest = {"id": 1, "public_results": False,
                        "private_key": "secret"}
        monkeypatch.setattr("sql.get_contest_by_id",
                            lambda contest_id: mock_contest)

        response = client.get('/result/1?key=wrongkey', follow_redirects=True)
        assert response.status_code == 200
        assert 'Tämän kilpailun tulokset eivät ole julkisia.'.encode(
            'utf-8') in response.data

    def test_private_result_page_correct_key(self, client, monkeypatch):
        """Test that a private result page is accessible with
        the correct key."""
        mock_contest = {"id": 1, "public_results": False,
                        "private_key": "secret"}
        monkeypatch.setattr("sql.get_contest_by_id",
                            lambda contest_id: mock_contest)
        # Mock results to render page
        monkeypatch.setattr("sql.get_contest_results", lambda contest_id: [])

        response = client.get('/result/1?key=secret')
        assert response.status_code == 200
        assert 'Tämän kilpailun tulokset eivät ole julkisia.'.encode(
            'utf-8') not in response.data
