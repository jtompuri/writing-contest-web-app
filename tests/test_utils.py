"""Unit tests for utility functions.

This module contains tests for utility functions such as input sanitization,
email validation, date formatting, text formatting, and pagination logic
in the Writing Contest Web App.

Test Classes:
    TestUtils: Tests for sanitize_input, is_valid_email, format_date,
               format_text, and total_pages.
"""

from app import format_date
from utils import sanitize_input, is_valid_email, format_text, total_pages


class TestUtils:
    """Tests for various utility functions."""

    def test_sanitize_input(self):
        """Tests basic input sanitization."""
        assert sanitize_input(
            '<script>alert("test")</script>') == 'alert("test")'
        assert sanitize_input('  clean text  ') == 'clean text'
        assert sanitize_input(123) == ''

    def test_sanitize_input_script(self):
        """Tests that script tags are removed from input."""
        assert sanitize_input('<script>alert(1)</script>') == 'alert(1)'

    def test_sanitize_input_event_handler(self):
        """Tests that HTML event handlers are removed from input."""
        assert sanitize_input('<div onclick="evil()">test</div>') == 'test'

    def test_sanitize_input_non_string(self):
        """Tests that non-string input is handled gracefully."""
        assert sanitize_input(None) == ''
        assert sanitize_input(123) == ''

    def test_is_valid_email(self):
        """Tests email validation with valid and invalid formats."""
        assert is_valid_email('test@example.com')
        assert not is_valid_email('invalid-email')
        assert not is_valid_email('test@.com')

    def test_format_date(self):
        """Tests the standard date formatting."""
        assert format_date('2023-10-05') == '5.10.2023'
        assert format_date('2024-05-29') == '29.5.2024'

    def test_format_date_invalid(self):
        """Tests that invalid date strings are returned as-is."""
        assert format_date('not-a-date') == 'not-a-date'

    def test_format_text(self):
        """Tests basic text formatting (newlines, markdown)."""
        assert format_text('Hello\nWorld') == 'Hello<br>World'
        assert format_text('*bold*') == '<strong>bold</strong>'
        assert format_text('_italic_') == '<em>italic</em>'

    def test_format_text_with_links(self):
        """Tests that URLs are converted to links when enabled."""
        text = 'Check this: https://example.com'
        result = format_text(text, links_allowed=True)
        assert '<a href="https://example.com"' in result

    def test_total_pages(self):
        """Tests the pagination page count calculation."""
        assert total_pages(0, 10) == 0
        assert total_pages(5, 10) == 1
        assert total_pages(20, 10) == 2
        assert total_pages(21, 10) == 3
