"""Provides utility functions for the Writing Contest Web App.

This module includes helpers for security (CSRF, input sanitization),
data validation (email), text formatting, and pagination.
"""

import re
from flask import abort, request, session
from markupsafe import Markup


def check_csrf():
    """Validates the CSRF token from a form submission.

    Aborts with a 403 error if the token is missing or invalid.
    """
    token = request.form.get("csrf_token")
    if not token or token != session.get("csrf_token"):
        abort(403)


def sanitize_input(text):
    """Strips potentially harmful HTML and script tags from a string.

    Args:
        text (str): The input string to sanitize.

    Returns:
        str: The sanitized string.
    """
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r'on\w+=".*?"', "", text, flags=re.IGNORECASE)
    text = re.sub(r"(javascript:|data:|vbscript:)", "", text,
                  flags=re.IGNORECASE)
    return text


def is_valid_email(email):
    """Validates if a string is a valid email address format.

    Args:
        email (str): The string to validate.

    Returns:
        A match object if the email format is valid, None otherwise.
    """
    return re.match(r"^[^@]+@[^@]+\.[^@]+$", email)


def format_text(text, links_allowed=False):
    """Converts plain text with simple markdown to safe HTML.

    Handles newlines, multiple spaces, bold (*word*), italics (_word_),
    and optionally auto-linking of URLs and email addresses.

    Args:
        text (str): The plain text to format.
        links_allowed (bool): Whether to convert URLs and emails to links.

    Returns:
        markupsafe.Markup: A safe HTML string for rendering in templates.
    """
    text = text.replace("\n", "<br>")
    text = re.sub(r" {2,}", lambda m: "&nbsp;" * len(m.group()), text)
    text = re.sub(r"\*(\S(?:.*?\S)?)\*", r"<strong>\1</strong>", text)
    text = re.sub(r"_(\S(?:.*?\S)?)_", r"<em>\1</em>", text)
    if links_allowed:
        email_regex = r"([\w\.-]+@[\w\.-]+\.\w+)"
        text = re.sub(email_regex, r'<a href="mailto:\1">\1</a>', text)
        url_regex = r'(?<!href=")(https?://[^\s<>"]+)'
        text = re.sub(url_regex,
                      r'<a href="\1" target="_blank" rel="noopener">\1</a>',
                      text)
    return Markup(text)


def total_pages(total_items, per_page):
    """Calculates the total number of pages for pagination."""
    return (total_items + per_page - 1) // per_page
