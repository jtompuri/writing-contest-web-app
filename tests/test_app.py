"""Tests for core application setup, features, and custom template filters.

This module contains tests for application-wide functionalities that are not
specific to a single blueprint, such as CSRF token handling and custom Jinja2
template filters.
"""
from flask import render_template_string
from app import app


class TestAppFeatures:
    """Tests for core application features and configurations."""

    def test_ensure_csrf_token_creation(self, client):
        """Test that a CSRF token is created if not present in the session."""
        # The session is initially empty before the first request
        client.get('/')
        # After the request, check the session to see if the token was created.
        with client.session_transaction() as sess:
            assert 'csrf_token' in sess

    def test_ensure_csrf_token_preservation(self, client):
        """Test that an existing CSRF token is not overwritten on subsequent
        requests."""
        with client.session_transaction() as sess:
            sess['csrf_token'] = 'my-test-token'

        client.get('/')
        # After the request, check the session to ensure the token was
        # preserved.
        with client.session_transaction() as sess:
            assert sess['csrf_token'] == 'my-test-token'

    def test_richtext_filter(self):
        """Test the richtext filter for correct HTML escaping and line
        breaks."""
        with app.test_request_context():
            text_content = "Test *bold* and _italic_."

            # Test richtext filter
            rendered_no_links = render_template_string(
                "{{ content | richtext }}", content=text_content)
            assert "<strong>bold</strong>" in rendered_no_links
            assert "<em>italic</em>" in rendered_no_links

            # Test richtext_with_links filter
            rendered_with_links = render_template_string(
                "{{ content | richtext_with_links }}", content=text_content)
            assert "<strong>bold</strong>" in rendered_with_links
            assert "<em>italic</em>" in rendered_with_links
