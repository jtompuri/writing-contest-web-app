from flask import session, render_template_string
from app import app


class TestAppFeatures:
    """Tests for core application features defined in app.py."""

    def test_ensure_csrf_token_creation(self, client):
        """Test that a CSRF token is created if not present in the session."""
        # The session is initially empty before the first request
        client.get('/')
        # After the request, the token should be in the session
        assert 'csrf_token' in session
        assert len(session['csrf_token']) == 32  # secrets.token_hex(16)

    def test_ensure_csrf_token_preservation(self, client):
        """Test that an existing CSRF token is not overwritten on subsequent requests."""
        with client.session_transaction() as sess:
            sess['csrf_token'] = 'my-test-token'

        client.get('/')
        assert session['csrf_token'] == 'my-test-token'

    def test_format_date_filter_invalid_value(self):
        """Test the format_date filter with an invalid date to cover the ValueError."""
        with app.test_request_context():
            # This should trigger the `except` block and return the original value
            rendered = render_template_string("{{ 'not-a-date' | format_date }}")
            assert rendered == "not-a-date"

    def test_config_injection(self):
        """Test that config values are injected into the template context."""
        with app.test_request_context():
            # Test that one of the config values is available in the template
            rendered = render_template_string("{{ SITE_TITLE }}")
            assert rendered == "Kirjoituskilpailut"

    def test_richtext_filters_are_registered(self):
        """Test that the richtext filters are registered and can be called."""
        with app.test_request_context():
            text_content = "Test *bold* and _italic_."

            # Test richtext filter
            rendered_no_links = render_template_string("{{ content | richtext }}", content=text_content)
            assert "<strong>bold</strong>" in rendered_no_links
            assert "<em>italic</em>" in rendered_no_links

            # Test richtext_with_links filter
            rendered_with_links = render_template_string("{{ content | richtext_with_links }}", content=text_content)
            assert "<strong>bold</strong>" in rendered_with_links
            assert "<em>italic</em>" in rendered_with_links
