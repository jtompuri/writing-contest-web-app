import re
import secrets
import sqlite3
from datetime import datetime

from flask import (
    Flask, abort, flash, redirect, render_template, request, session, url_for
)
from markupsafe import Markup

import config
import db
import sql
import users

app = Flask(__name__)
app.secret_key = config.secret_key
app.teardown_appcontext(db.close_connection)


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


def check_csrf():
    """Checks the CSRF token in the request form against the session token."""
    token = request.form.get("csrf_token")
    if not token or token != session.get("csrf_token"):
        abort(403)


def sanitize_input(text):
    """Sanitizes input text to remove potentially harmful content."""
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r'<.*?>', '', text)  # Remove HTML tags
    text = re.sub(r'on\w+=".*?"', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(javascript:|data:|vbscript:)', '', text,
                  flags=re.IGNORECASE)
    return text


def is_valid_email(email):
    """Validates an email address."""
    return re.match(r"^[^@]+@[^@]+\.[^@]+$", email)


def format_text(text, links_allowed=False):
    """Formats text with HTML tags for styling. Allows links if specified."""
    text = text.replace('\n', '<br />')
    text = re.sub(r' {2,}', lambda m: '&nbsp;' * len(m.group()), text)
    text = re.sub(r'\*(\S(?:.*?\S)?)\*', r'<strong>\1</strong>', text)  # Bold
    text = re.sub(r'_(\S(?:.*?\S)?)_', r'<em>\1</em>', text)  # Italics

    if links_allowed:
        email_regex = r'([\w\.-]+@[\w\.-]+\.\w+)'
        text = re.sub(email_regex, r'<a href="mailto:\1">\1</a>', text)
        url_regex = r'(?<!href=")(https?://[^\s<>"]+)'
        text = re.sub(
            url_regex, r'<a href="\1" target="_blank" rel="noopener">\1</a>',
            text
            )

    return Markup(text)


def total_pages(total_items, per_page):
    """Calculates the total number of pages for pagination."""
    return (total_items + per_page - 1) // per_page


@app.template_filter('richtext')
def richtext_filter(s):
    """Applies rich text formatting without links."""
    return format_text(s, links_allowed=False)


@app.template_filter('richtext_with_links')
def richtext_with_links_filter(s):
    """Applies rich text formatting with links."""
    return format_text(s, links_allowed=True)


@app.route("/")
def index():
    """Renders the index page with contest information."""
    contests_for_entry = sql.get_contests_for_entry(3)
    contests_for_review = sql.get_contests_for_review(3)
    contests_for_results = sql.get_contests_for_results(3)
    return render_template(
        "index.html",
        contests_for_entry=contests_for_entry,
        contests_for_review=contests_for_review,
        contests_for_results=contests_for_results
    )


@app.route("/contests/contest/<int:contest_id>")
def contest(contest_id):
    """Displays a specific contest's details."""
    contest = sql.get_contest_by_id(contest_id)
    if not contest:
        abort(404)

    today = datetime.now().date()
    collection_end = datetime.strptime(
        contest["collection_end"], "%Y-%m-%d"
        ).date()
    review_end = datetime.strptime(contest["review_end"], "%Y-%m-%d").date()

    collection_ended = collection_end <= today
    review_ended = review_end <= today

    stats = {}
    if collection_ended:
        stats["entry_count"] = sql.get_entry_count(contest_id)
        stats["review_count"] = sql.get_review_count(contest_id)

    return render_template(
        "contest.html",
        contest=contest,
        collection_ended=collection_ended,
        review_ended=review_ended,
        stats=stats
    )


@app.route("/register")
def register():
    """Renders the registration page."""
    return render_template("register.html")


@app.route("/create", methods=["POST"])
def create():
    """Handles user registration."""
    check_csrf()
    name = sanitize_input(request.form["name"])
    username = sanitize_input(request.form["username"])
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    # Validate input lengths and match passwords
    if (not username or len(username) > 50 or not name or len(name) > 50 or
            len(password1) > 50 or len(password2) > 50):
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: Tarkista syötteet.")
        return redirect("/register")

    if password1 != password2:
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: salasanat eivät ole samat.")
        return redirect("/register")

    if len(password1) < 8:
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: salasanan on oltava vähintään 8 merkkiä pitkä.")
        return redirect("/register")

    if not is_valid_email(username):
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: Sähköpostiosoite ei ole kelvollinen.")
        return redirect("/register")

    user_count = users.get_user_count()
    is_super = 1 if user_count == 0 else 0

    success = users.create_user(name, username, password1, is_super)
    if not success:
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: tunnus on jo varattu.")
        return redirect("/register")

    session["form_data"] = {"username": username}
    if is_super:
        flash("Pääkäyttäjän tunnus on luotu. Tällä tunnuksella on täydet"
              " käyttöoikeudet.")
    else:
        flash("Tunnus on luotu.")

    return redirect(url_for("login", next_page="/"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login."""
    if request.method == "GET":
        username = session.pop("form_data", {}).get("username", "")
        next_page = request.args.get("next_page", "/")
        return render_template(
            "login.html", next_page=next_page, username=username
            )

    if request.method == "POST":
        check_csrf()
        username = sanitize_input(request.form["username"])
        password = request.form["password"]
        next_page = request.form.get("next_page", "/")

        user_id = users.check_login(username, password)
        if user_id:
            user = users.get_user(user_id)
            if user is None:
                flash("Virheellinen käyttäjätunnus.")
                return redirect("/login")

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["super_user"] = bool(user["super_user"])

            return redirect(next_page)
        else:
            flash("Virhe: Väärä tunnus tai salasana.")
            return render_template(
                "login.html", next_page=next_page, username=username
                )

    return redirect("/login")


@app.route("/admin")
def admin():
    """Renders the admin dashboard."""
    if not session.get("super_user"):
        abort(403)

    contest_count = sql.get_contest_count()
    user_count = users.get_user_count()
    entry_count = sql.get_entry_count()

    return render_template(
        "admin/index.html",
        contest_count=contest_count,
        user_count=user_count,
        entry_count=entry_count
    )


@app.route("/admin/contests")
def admin_contests():
    """Displays a list of contests in the admin panel."""
    if not session.get("super_user"):
        abort(403)
    page = request.args.get("page", 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    contests = sql.get_all_contests(limit=per_page, offset=offset)
    total = sql.get_contest_count()

    return render_template(
        "admin/contests.html",
        contests=contests,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages(total, per_page),
        base_url="/admin/contests?page="
    )


@app.route("/admin/contests/new")
def admin_new_contest():
    """Renders the page to create a new contest."""
    if not session.get("super_user"):
        abort(403)

    classes = sql.get_all_classes()
    return render_template("admin/new_contest.html", classes=classes)


@app.route("/admin/contests/create", methods=["POST"])
def admin_create_contest():
    """Handles the creation of a new contest."""
    check_csrf()
    if not session.get("super_user"):
        abort(403)

    form = request.form
    title = sanitize_input(form["title"])
    class_id = form["class_id"]
    short_description = sanitize_input(form["short_description"])
    long_description = sanitize_input(form["long_description"])
    collection_end = form["collection_end"]
    review_end = form["review_end"]

    # Ensure all required fields are filled
    if (not title or not class_id or not collection_end or not review_end or
            not short_description or not long_description):
        flash("Kaikki pakolliset kentät on täytettävä.")
        return redirect(url_for("admin_new_contest"))

    anonymity = 1 if form.get("anonymity") == "on" else 0
    public_reviews = 1 if form.get("public_reviews") == "on" else 0
    public_results = 1 if form.get("public_results") == "on" else 0

    try:
        sql.create_contest(
            title, class_id, short_description, long_description,
            anonymity, public_reviews, public_results,
            collection_end, review_end
        )
        flash("Kilpailu on luotu.")
        return redirect(url_for("admin_contests"))
    except Exception as e:
        print("Virhe kilpailun luomisessa:", e)
        flash("Kilpailua ei voitu luoda.")
        return redirect(url_for("admin_new_contest"))


@app.route("/admin/contests/delete/<int:contest_id>", methods=["POST"])
def delete_contest(contest_id):
    """Handles the deletion of a contest."""
    check_csrf()
    if not session.get("super_user"):
        abort(403)

    sql.delete_contest(contest_id)
    flash("Kilpailu on poistettu.")
    return redirect(url_for("admin_contests"))


@app.route("/admin/users")
def admin_users():
    """Displays a paginated list of users in the admin panel."""
    if not session.get("super_user"):
        abort(403)
    page = request.args.get("page", 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    users_list = users.get_all_users(limit=per_page, offset=offset)
    total = users.get_user_count()

    return render_template(
        "admin/users.html",
        users=users_list,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages(total, per_page),
        base_url="/admin/users?page="
    )


@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    """Handles the deletion of a user."""
    check_csrf()
    if not session.get("super_user"):
        abort(403)

    if int(user_id) == int(session.get("user_id", -1)):
        flash("Et voi poistaa omaa tunnustasi.")
        return redirect(url_for("admin_users"))

    if users.is_super_user(user_id):
        flash("Pääkäyttäjiä ei voi poistaa.")
        return redirect(url_for("admin_users"))

    users.delete_user(user_id)
    flash("Käyttäjä on poistettu.")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/new")
def admin_new_user():
    """Renders the page to create a new user."""
    if not session.get("super_user"):
        abort(403)
    return render_template("admin/new_user.html")


@app.route("/admin/users/create", methods=["POST"])
def admin_create_user():
    """Handles the creation of a new user."""
    check_csrf()
    if not session.get("super_user"):
        abort(403)

    name = sanitize_input(request.form["name"])
    username = sanitize_input(request.form["username"])
    password = request.form["password"]
    is_super = 1 if request.form.get("is_super") == "on" else 0

    session["form_data"] = {
        "name": name,
        "username": username,
        "is_super": is_super
    }

    # Ensure all fields are filled and email is valid
    if not name or not username or not password:
        flash("Kaikki kentät ovat pakollisia.")
        return redirect(url_for("admin_new_user"))

    if not is_valid_email(username):
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: Sähköpostiosoite ei ole kelvollinen.")
        return redirect(url_for("admin_new_user"))

    success = users.create_user(name, username, password, is_super)
    if not success:
        flash("Käyttäjänimi on jo käytössä.")
        return redirect(url_for("admin_new_user"))

    session.pop("form_data", None)
    flash("Uusi käyttäjä on luotu.")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/edit/<int:user_id>")
def admin_edit_user(user_id):
    """Renders the page to edit an existing user."""
    if not session.get("super_user"):
        abort(403)

    user = users.get_user(user_id)
    if not user:
        flash("Käyttäjää ei löytynyt.")
        return redirect(url_for("admin_users"))

    return render_template("admin/edit_user.html", user=user)


@app.route("/admin/users/update/<int:user_id>", methods=["POST"])
def admin_update_user(user_id):
    """Handles updating user details."""
    if not session.get("super_user"):
        abort(403)

    name = sanitize_input(request.form["name"])
    username = sanitize_input(request.form["username"])
    is_super = 1 if request.form.get("is_super") == "on" else 0
    password = sanitize_input(request.form.get("password", ""))

    # Validate input fields
    if not name or not username:
        flash("Nimi ja käyttäjätunnus ovat pakollisia.")
        return redirect(url_for("admin_edit_user", user_id=user_id))

    if not is_valid_email(username):
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: Sähköpostiosoite ei ole kelvollinen.")
        return redirect(url_for("admin_edit_user", user_id=user_id))

    try:
        users.update_user(user_id, name, username, is_super)

        if password:
            if len(password) < 8:
                flash("Salasanan on oltava vähintään 8 merkkiä pitkä.")
                return redirect(url_for("admin_edit_user", user_id=user_id))
            users.update_password(user_id, password)

        flash("Käyttäjän tiedot päivitetty.")
        return redirect(url_for("admin_users"))
    except sqlite3.IntegrityError:
        flash("Käyttäjätunnus on jo käytössä.")
        return redirect(url_for("admin_edit_user", user_id=user_id))


@app.route("/admin/contests/edit/<int:contest_id>")
def edit_contest(contest_id):
    """Renders the page to edit an existing contest."""
    if not session.get("super_user"):
        abort(403)

    contest = sql.get_contest_by_id(contest_id)
    classes = sql.get_all_classes()

    if not contest:
        abort(404)

    return render_template(
        "admin/edit_contest.html", contest=contest, classes=classes
        )


@app.route("/admin/contests/update/<int:contest_id>", methods=["POST"])
def admin_update_contest(contest_id):
    """Handles updating contest details."""
    check_csrf()
    if not session.get("super_user"):
        abort(403)

    form = request.form
    title = sanitize_input(form["title"])
    class_id = form["class_id"]
    short_description = sanitize_input(form["short_description"])
    long_description = sanitize_input(form["long_description"])
    collection_end = form["collection_end"]
    review_end = form["review_end"]

    # Ensure all required fields are filled
    if (not title or not class_id or not collection_end or not review_end or
            not short_description or not long_description):
        flash("Kaikki pakolliset kentät on täytettävä.")
        return redirect(url_for("edit_contest", contest_id=contest_id))

    anonymity = 1 if form.get("anonymity") == "on" else 0
    public_reviews = 1 if form.get("public_reviews") == "on" else 0
    public_results = 1 if form.get("public_results") == "on" else 0

    sql.update_contest(
        contest_id, title, class_id, short_description, long_description,
        anonymity, public_reviews, public_results,
        collection_end, review_end
    )

    flash("Kilpailun tiedot päivitetty.")
    return redirect(url_for("admin_contests"))


@app.route("/contests/contest/<int:contest_id>/add_entry",
           methods=["GET", "POST"])
def add_entry(contest_id):
    """Allows users to add an entry to a contest."""
    if not session.get("user_id"):
        flash("Kirjaudu sisään osallistuaksesi kilpailuun.")
        return redirect(url_for("login", next_page=request.path))

    contest = sql.get_contest_by_id(contest_id)
    if not contest:
        abort(404)

    today = datetime.now().date()
    collection_end = datetime.strptime(
        contest["collection_end"], "%Y-%m-%d"
        ).date()
    review_end = datetime.strptime(contest["review_end"], "%Y-%m-%d").date()
    collection_ended = collection_end <= today
    review_ended = review_end <= today

    stats = {}
    if collection_ended:
        stats["entry_count"] = sql.get_entry_count(contest_id)
        stats["review_count"] = sql.get_review_count(contest_id)

    if request.method == "GET":
        entry = request.args.get("entry", "")
        return render_template(
            "add_entry.html",
            contest=contest,
            collection_ended=collection_ended,
            review_ended=review_ended,
            stats=stats,
            entry=entry
        )

    if request.method == "POST":
        check_csrf()
        action = request.form.get("action")
        entry = sanitize_input(request.form.get("entry", ""))

        if not entry:
            flash("Kilpailutyö ei saa olla tyhjä.")
            return redirect(url_for("add_entry", contest_id=contest_id))

        if action == "preview":
            return render_template(
                "preview_entry.html",
                contest=contest,
                entry=entry,
                collection_ended=collection_ended,
                review_ended=review_ended,
                stats=stats
            )

        if action == "submit":
            user_id = session["user_id"]

            if sql.entry_exists(contest_id, user_id):
                flash("Olet jo osallistunut tähän kilpailuun.")
                return redirect(url_for("contest", contest_id=contest_id))

            sql.save_entry(contest_id, user_id, entry)
            flash("Kilpailutyö on tallennettu.")
            return redirect(url_for("contest", contest_id=contest_id))

    return redirect(url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    """Logs out the current user."""
    check_csrf()
    session.clear()
    return redirect("/")


@app.route("/contests")
def contests():
    """Displays a list of contests available for entry."""
    page = request.args.get("page", 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    contests = sql.get_contests_for_entry(limit=per_page, offset=offset)
    total = sql.get_entry_contest_count()

    return render_template(
        "contests.html",
        contests=contests,
        page=page,
        per_page=per_page,
        total=total
    )


@app.route("/results")
def results():
    """Displays contest results."""
    page = request.args.get("page", 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    contests = sql.get_contests_for_results(limit=per_page, offset=offset)
    total = sql.get_results_contest_count()

    return render_template(
        "results.html",
        contests=contests,
        page=page,
        per_page=per_page,
        total=total,
        base_url="/results?page="
    )


@app.route("/reviews")
def reviews():
    """Displays contests available for review."""
    page = request.args.get("page", 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    contests = sql.get_contests_for_review(limit=per_page, offset=offset)
    total = sql.get_review_contest_count()

    return render_template(
        "reviews.html",
        contests=contests,
        page=page,
        per_page=per_page,
        total=total,
        base_url="/reviews?page="
    )


@app.route("/my_texts")
def my_texts():
    """Displays the user's texts."""
    return render_template("my_texts.html")


@app.route("/terms_of_use")
def terms_of_use():
    """Displays the terms of use page."""
    return render_template("terms_of_use.html")


@app.route("/admin/entries")
def admin_entries():
    """Displays a paginated and filterable list of entries in the admin
        panel."""
    if not session.get("super_user"):
        abort(403)
    page = request.args.get("page", 1, type=int)
    per_page = 20

    contest_id = request.args.get("contest_id", type=int)
    user_search = request.args.get("user_search", "", type=str).strip()

    offset = (page - 1) * per_page

    # Fetch contests for the dropdown
    contests = sql.get_all_contests()

    # Fetch filtered entries and total count
    entries = sql.get_all_entries(
        limit=per_page,
        offset=offset,
        contest_id=contest_id,
        user_search=user_search
    )
    total = sql.get_entry_count(contest_id=contest_id, user_search=user_search)

    return render_template(
        "admin/entries.html",
        entries=entries,
        contests=contests,
        selected_contest_id=contest_id,
        user_search=user_search,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages(total, per_page),
        base_url="/admin/entries?"
    )


@app.route("/admin/new_entry", methods=["GET", "POST"])
def admin_new_entry():
    """Renders and handles the form to create a new entry as admin."""
    if not session.get("super_user"):
        abort(403)

    contests = sql.get_all_contests()
    users_list = users.get_all_users()

    if request.method == "POST":
        check_csrf()
        contest_id = request.form.get("contest_id")
        user_id = request.form.get("user_id")
        entry_text = sanitize_input(request.form.get("entry", ""))

        if not contest_id or not user_id or not entry_text:
            flash("Kaikki pakolliset kentät on täytettävä.")
            return render_template(
                "admin/new_entry.html",
                contests=contests,
                users=users_list,
                entry=entry_text,
                selected_contest_id=contest_id,
                selected_user_id=user_id
            )

        try:
            sql.create_entry(contest_id, user_id, entry_text)
            flash("Teksti on luotu.")
            return redirect(url_for("admin_entries"))
        except Exception as e:
            # Check for unique constraint violation
            if ("UNIQUE constraint failed" in str(e) or
                    "duplicate key" in str(e)):
                flash("Tällä käyttäjällä on jo teksti tässä kilpailussa.")
            else:
                print("Virhe tekstin luomisessa:", e)
                flash("Tekstiä ei voitu luoda.")
            return render_template(
                "admin/new_entry.html",
                contests=contests,
                users=users_list,
                entry=entry_text,
                selected_contest_id=contest_id,
                selected_user_id=user_id
            )

    return render_template(
        "admin/new_entry.html", contests=contests, users=users_list
        )


@app.route("/admin/entries/create", methods=["POST"])
def admin_create_entry():
    """Handles the creation of a new entry."""
    check_csrf()
    if not session.get("super_user"):
        abort(403)

    contest_id = request.form["contest_id"]
    user_id = request.form["user_id"]
    entry_text = sanitize_input(request.form.get("entry", ""))

    if not contest_id or not user_id or not entry_text:
        flash("Kaikki pakolliset kentät on täytettävä.")
        return redirect(url_for("admin_new_entry"))

    try:
        sql.create_entry(contest_id, user_id, entry_text)
        flash("Teksti on luotu.")
        return redirect(url_for("admin_entries"))
    except Exception as e:
        print("Virhe tekstin luomisessa:", e)
        flash("Tekstiä ei voitu luoda.")
        return redirect(url_for("admin_new_entry"))


@app.route("/admin/entries/edit/<int:entry_id>")
def admin_edit_entry(entry_id):
    """Renders the page to edit an existing entry."""
    if not session.get("super_user"):
        abort(403)
    entry = sql.get_entry_by_id(entry_id)
    contests = sql.get_all_contests()
    users_list = users.get_all_users()
    if not entry:
        abort(404)
    return render_template(
        "admin/edit_entry.html", entry=entry,
        contests=contests, users=users_list
        )


@app.route("/admin/entries/update/<int:entry_id>", methods=["POST"])
def admin_update_entry(entry_id):
    """Handles updating entry details."""
    check_csrf()
    if not session.get("super_user"):
        abort(403)

    contest_id = request.form["contest_id"]
    user_id = request.form["user_id"]
    entry_text = sanitize_input(request.form.get("entry", ""))

    if not contest_id or not user_id or not entry_text:
        flash("Kaikki pakolliset kentät on täytettävä.")
        return redirect(url_for("admin_edit_entry", entry_id=entry_id))

    try:
        sql.update_entry(entry_id, contest_id, user_id, entry_text)
        flash("Tekstin tiedot päivitetty.")
        return redirect(url_for("admin_entries"))
    except Exception as e:
        print("Virhe tekstin päivittämisessä:", e)
        flash("Tekstiä ei voitu päivittää.")
        return redirect(url_for("admin_edit_entry", entry_id=entry_id))


@app.route("/admin/entries/delete/<int:entry_id>", methods=["POST"])
def admin_delete_entry(entry_id):
    """Handles the deletion of an entry."""
    check_csrf()
    if not session.get("super_user"):
        abort(403)
    try:
        sql.delete_entry(entry_id)
        flash("Teksti on poistettu.")
    except Exception as e:
        print("Virhe tekstin poistossa:", e)
        flash("Tekstiä ei voitu poistaa.")
    return redirect(url_for("admin_entries"))
