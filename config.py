"""
Configuration module for the Writing Contest Web App.

Attributes:
    secret_key (str): The secret key used for Flask session management and
                      CSRF protection.
    DATABASE (str): The SQLite database filename.
    DEFAULT_PER_PAGE (int): Default number of items per page for pagination.
    ADMIN_PER_PAGE (int): Number of items per page for admin views.
    SHORT_DESCRIPTION_MAX_LENGTH (int): Maximum length for short descriptions.
    LONG_DESCRIPTION_MAX_LENGTH (int): Maximum length for long descriptions.
    PASSWORD_MIN_LENGTH (int): Minimum password length for user accounts.
"""

SECRET_KEY = "8d394187c116a65f83ed7e0ee4ecf915"
SITE_TITLE = "Kirjoituskilpailut"
DATABASE = "database.db"
DEFAULT_PER_PAGE = 5
ADMIN_PER_PAGE = 20
TITLE_MAX_LENGTH = 100
SHORT_DESCRIPTION_MAX_LENGTH = 255
LONG_DESCRIPTION_MAX_LENGTH = 2000
ENTRY_MAX_LENGTH = 5000
FIELD_MAX_LENGTH = 50
PASSWORD_MIN_LENGTH = 8
