import secrets
from datetime import datetime

from flask import Flask, session

import config
import db
from utils import format_text

from routes.main import main_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.entries import entries_bp

app = Flask(__name__)
app.secret_key = config.secret_key
app.teardown_appcontext(db.close_connection)

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(entries_bp)


@app.context_processor
def inject_site_name():
    return dict(site_name="Kirjoituskilpailut")


@app.context_processor
def inject_config():
    """Injects configuration constants into all templates."""
    return dict(
        TITLE_MAX_LENGTH=getattr(config, "TITLE_MAX_LENGTH", 100),
        SHORT_DESCRIPTION_MAX_LENGTH=getattr(config, "SHORT_DESCRIPTION_MAX_LENGTH", 255),
        LONG_DESCRIPTION_MAX_LENGTH=getattr(config, "LONG_DESCRIPTION_MAX_LENGTH", 2000),
        ENTRY_MAX_LENGTH=getattr(config, "ENTRY_MAX_LENGTH", 5000),
        FIELD_MAX_LENGTH=getattr(config, "FIELD_MAX_LENGTH", 50),
        PASSWORD_MIN_LENGTH=getattr(config, "PASSWORD_MIN_LENGTH", 8),
        DEFAULT_PER_PAGE=getattr(config, "DEFAULT_PER_PAGE", 5),
        ADMIN_PER_PAGE=getattr(config, "ADMIN_PER_PAGE", 20)
    )


@app.template_filter("format_date")
def format_date(value):
    """Formats a date string in 'YYYY-MM-DD' format to 'DD.MM.YYYY'."""
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return f"{dt.day}.{dt.month}.{dt.year}"
    except ValueError:
        return value


@app.before_request
def ensure_csrf_token():
    """Ensures a CSRF token is present in the session."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)


@app.template_filter('richtext')
def richtext_filter(s):
    """Applies rich text formatting without links."""
    return format_text(s, links_allowed=False)


@app.template_filter('richtext_with_links')
def richtext_with_links_filter(s):
    """Applies rich text formatting with links."""
    return format_text(s, links_allowed=True)
