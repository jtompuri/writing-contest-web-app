"""Tests for the main blueprint and public-facing features.

This module contains unit tests for public routes, contest routes, and related
validation in the Writing Contest Web App.

Test Classes:
    TestPublicRoutes: Tests for public pages and error handling.
    TestContestRoutes: Tests for contest detail, admin contest management, and validation.
"""


class TestFrontpage:
    def test_frontpage_winners_display(self, client, monkeypatch):
        fake_contests = [
            {"id": 1, "title": "Test Contest", "public_results": True, "short_description": "Desc", "class_value": "Essee",
             "anonymity": True, "public_reviews": True, "review_end": "2025-01-01", "collection_end": "2024-12-01",
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
        monkeypatch.setattr("sql.get_contests_for_entry", lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contests_for_review", lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contests_for_results", lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contest_results", lambda contest_id: fake_winners)

        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Voittaja 1" in resp.data
        assert b"32 p." in resp.data
        assert b"Voittaja 2" in resp.data
        assert b"10 p." in resp.data
        assert b"Lue koko teksti" in resp.data
        assert b"Kaikki tulokset t" in resp.data

    def test_frontpage_no_winners(self, client, monkeypatch):
        fake_contests = [
            {"id": 1, "title": "Test Contest", "public_results": False, "short_description": "Desc", "class_value": "Essee",
             "anonymity": True, "public_reviews": True, "review_end": "2025-01-01", "collection_end": "2024-12-01",
             "total_entries": 3}
        ]
        monkeypatch.setattr("sql.get_contests_for_entry", lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contests_for_review", lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contests_for_results", lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contest_results", lambda contest_id: [])

        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Ei tuloksia t" in resp.data or b"Voittajat julkaistaan pian" in resp.data

    def test_frontpage_no_contests(self, client, monkeypatch):
        monkeypatch.setattr("sql.get_contests_for_entry", lambda n: [])
        monkeypatch.setattr("sql.get_contests_for_review", lambda n: [])
        monkeypatch.setattr("sql.get_contests_for_results", lambda n: [])
        monkeypatch.setattr("sql.get_contest_results", lambda contest_id: [])

        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Ei k" in resp.data or b"Ei julkaistuja tuloksia" in resp.data

    def test_frontpage_winner_entry_links(self, client, monkeypatch):
        fake_contests = [
            {"id": 1, "title": "Test Contest", "public_results": True, "short_description": "Desc", "class_value": "Essee",
             "anonymity": True, "public_reviews": True, "review_end": "2025-01-01", "collection_end": "2024-12-01",
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
        monkeypatch.setattr("sql.get_contests_for_entry", lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contests_for_review", lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contests_for_results", lambda n: fake_contests)
        monkeypatch.setattr("sql.get_contest_results", lambda contest_id: fake_winners)

        resp = client.get("/")
        for winner in fake_winners:
            link = f'/entry/{winner["id"]}'.encode("utf-8")
            assert link in resp.data


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

    def test_results_page_filters_private_contests(self, client, monkeypatch):
        """Test that the main results page does not show private contests without a key."""
        # This mocks a mix of public and private contests
        fake_contests = [
            {"id": 1, "title": "Public Results Contest", "public_results": True, "private_key": "", "review_end": "2025-01-31", "collection_end": "2025-01-15"},
            {"id": 2, "title": "Private Results Contest", "public_results": False, "private_key": "secret1", "review_end": "2025-01-31", "collection_end": "2025-01-15"}
        ]
        monkeypatch.setattr("sql.get_contests_for_results", lambda limit, offset: fake_contests)
        monkeypatch.setattr("sql.get_results_contest_count", lambda: len(fake_contests))

        response = client.get('/results')
        assert response.status_code == 200
        assert b"Public Results Contest" in response.data
        assert b"Private Results Contest" not in response.data

    def test_reviews_page_filters_private_contests(self, client, monkeypatch):
        """Test that the main reviews page does not show private contests without a key."""
        # This mocks a mix of public and private contests
        fake_contests = [
            {"id": 1, "title": "Public Review Contest", "public_reviews": True, "private_key": "", "review_end": "2025-01-31", "collection_end": "2025-01-15"},
            {"id": 2, "title": "Private Review Contest", "public_reviews": False, "private_key": "secret2", "review_end": "2025-01-31", "collection_end": "2025-01-15"}
        ]
        monkeypatch.setattr("sql.get_contests_for_review", lambda limit, offset: fake_contests)
        monkeypatch.setattr("sql.get_review_contest_count", lambda: len(fake_contests))

        response = client.get('/reviews')
        assert response.status_code == 200
        assert b"Public Review Contest" in response.data
        assert b"Private Review Contest" not in response.data

    def test_reviews_page_shows_private_contest_with_key(self, client, monkeypatch):
        """Test that the reviews page shows a private contest when the correct key is provided."""
        fake_contests = [
            {"id": 2, "title": "Private Review Contest", "public_reviews": False, "private_key": "secret2", "review_end": "2025-01-31", "collection_end": "2025-01-15"}
        ]
        monkeypatch.setattr("sql.get_contests_for_review", lambda limit, offset: fake_contests)
        monkeypatch.setattr("sql.get_review_contest_count", lambda: len(fake_contests))

        response = client.get('/reviews?key=secret2')
        assert response.status_code == 200
        assert b"Private Review Contest" in response.data


class TestContestRoutes:
    def test_contest_detail_valid(self, client):
        response = client.get('/contests/contest/1')
        assert response.status_code in (200, 404)

    def test_contest_detail_invalid(self, client):
        response = client.get('/contests/contest/999999')
        assert response.status_code == 404
