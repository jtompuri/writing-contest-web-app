"""Admin blueprint routes for administrative actions.

This module contains routes for admin panel features such as managing contests,
users, and entries in the Writing Contest Web App.

Blueprints:
    admin_bp (Blueprint): Handles admin-related routes.
"""

from flask import (Blueprint, render_template, request, session, abort, flash,
                   redirect, url_for)

import config
import sql
import users
from utils import check_csrf, sanitize_input, is_valid_email, total_pages
import secrets
import sqlite3

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
def admin():
    """Renders the main admin dashboard page."""
    if not session.get("super_user"):
        abort(403)
    contest_count = sql.get_contest_count()
    user_count = users.get_user_count()
    entry_count = sql.get_entry_count()
    contests_collection = sql.get_contests_for_entry(limit=3)
    contests_review = sql.get_contests_for_review(limit=3)
    contests_results = sql.get_contests_for_results(limit=3)
    return render_template(
        "admin/index.html",
        contest_count=contest_count,
        user_count=user_count,
        entry_count=entry_count,
        contests_collection=contests_collection,
        contests_review=contests_review,
        contests_results=contests_results
    )


@admin_bp.route("/contests")
def admin_contests():
    """Renders the contest management page with pagination and search."""
    if not session.get("super_user"):
        abort(403)
    page = request.args.get("page", 1, type=int)
    per_page = config.ADMIN_PER_PAGE
    offset = (page - 1) * per_page

    # Sanitize filter input
    title_search = sanitize_input(request.args.get("title_search", "",
                                                   type=str).strip())

    contests = sql.get_all_contests(limit=per_page, offset=offset,
                                    title_search=title_search)
    total = sql.get_contest_count(title_search=title_search)

    return render_template(
        "admin/contests.html",
        contests=contests,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages(total, per_page),
        base_url="/admin/contests?page=",
        title_search=title_search
    )


@admin_bp.route("/users")
def admin_users():
    """Renders the user management page with pagination and filters."""
    if not session.get("super_user"):
        abort(403)
    page = request.args.get("page", 1, type=int)
    per_page = config.ADMIN_PER_PAGE
    offset = (page - 1) * per_page

    # Sanitize filter inputs
    name_search = sanitize_input(request.args.get("name_search", "",
                                                  type=str).strip())
    username_search = sanitize_input(request.args.get("username_search", "",
                                                      type=str).strip())
    super_user_filter = sanitize_input(request.args.get("super_user", ""))

    users_list = users.get_all_users(
        limit=per_page,
        offset=offset,
        name_search=name_search,
        username_search=username_search,
        super_user=super_user_filter
    )
    total = users.get_user_count(
        name_search=name_search,
        username_search=username_search,
        super_user=super_user_filter
    )

    return render_template(
        "admin/users.html",
        users=users_list,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages(total, per_page),
        base_url="/admin/users?page=",
        name_search=name_search,
        username_search=username_search,
        super_user_filter=super_user_filter
    )


@admin_bp.route("/entries")
def admin_entries():
    """Renders the entry management page with pagination and filters."""
    if not session.get("super_user"):
        abort(403)
    page = request.args.get("page", 1, type=int)
    per_page = config.ADMIN_PER_PAGE

    # Sanitize filter inputs
    contest_id = request.args.get("contest_id", type=int)
    user_search = sanitize_input(request.args.get("user_search", "",
                                                  type=str).strip())

    offset = (page - 1) * per_page

    contests = sql.get_all_contests()
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
        base_url="/admin/entries?page="
    )


@admin_bp.route("/contests/new")
def new_contest():
    """Renders the form for creating a new contest."""
    if not session.get("super_user"):
        abort(403)
    classes = sql.get_all_classes()
    return render_template("admin/new_contest.html", classes=classes)


@admin_bp.route("/contests/create", methods=["POST"])
def create_contest():
    """Handles the POST request to create a new contest."""
    check_csrf()
    if not session.get("super_user"):
        abort(403)

    form = request.form
    title = sanitize_input(form.get("title", ""))
    class_id_str = form.get("class_id", "")
    short_description = sanitize_input(form.get("short_description", ""))
    long_description = sanitize_input(form.get("long_description", ""))
    collection_end = form.get("collection_end", "")
    review_end = form.get("review_end", "")

    class_id = int(class_id_str) if class_id_str.isdigit() else None

    errors = []
    if (not title or not class_id or not collection_end or not review_end
       or not short_description or not long_description):
        errors.append("Kaikki pakolliset kentät on täytettävä.")

    if len(short_description) > 255:
        errors.append("Lyhyt kuvaus saa olla enintään 255 merkkiä.")

    if len(long_description) > 2000:
        errors.append("Pitkä kuvaus saa olla enintään 2000 merkkiä.")

    if errors:
        for error in errors:
            flash(error)
        return redirect(url_for("admin.new_contest"))

    anonymity = 1 if form.get("anonymity") == "on" else 0
    public_reviews = 1 if form.get("public_reviews") == "on" else 0
    public_results = 1 if form.get("public_results") == "on" else 0
    private_key = secrets.token_urlsafe(16)

    contest_data = {
        "title": title,
        "class_id": class_id,
        "short_description": short_description,
        "long_description": long_description,
        "anonymity": anonymity,
        "public_reviews": public_reviews,
        "public_results": public_results,
        "collection_end": collection_end,
        "review_end": review_end,
        "private_key": private_key
    }

    try:
        sql.create_contest(contest_data)
        flash("Kilpailu on luotu.")
        return redirect(url_for("admin.admin_contests"))
    except Exception as e:
        print("Virhe kilpailun luomisessa:", e)
        flash("Kilpailua ei voitu luoda.")
        return redirect(url_for("admin.new_contest"))


@admin_bp.route("/contests/delete/<int:contest_id>", methods=["POST"])
def delete_contest(contest_id):
    """Handles the POST request to delete a contest.

    Args:
        contest_id (int): The ID of the contest to delete.
    """
    check_csrf()
    if not session.get("super_user"):
        abort(403)
    try:
        sql.delete_contest(contest_id)
        flash("Kilpailu on poistettu.")
    except Exception as e:
        print(f"Virhe kilpailun poistossa: {e}")
        flash("Kilpailua ei voitu poistaa.")
    return redirect(url_for("admin.admin_contests"))


@admin_bp.route("/contests/edit/<int:contest_id>")
def edit_contest(contest_id):
    """Renders the form for editing an existing contest.

    Args:
        contest_id (int): The ID of the contest to edit.
    """
    if not session.get("super_user"):
        abort(403)
    contest = sql.get_contest_by_id(contest_id)
    classes = sql.get_all_classes()
    if not contest:
        abort(404)
    return render_template("admin/edit_contest.html", contest=contest,
                           classes=classes)


@admin_bp.route("/contests/update/<int:contest_id>", methods=["POST"])
def update_contest(contest_id):
    """Handles the POST request to update a contest's details.

    Args:
        contest_id (int): The ID of the contest to update.
    """
    check_csrf()
    if not session.get("super_user"):
        abort(403)

    form = request.form
    title = sanitize_input(form.get("title", ""))
    class_id_str = form.get("class_id", "")
    short_description = sanitize_input(form.get("short_description", ""))
    long_description = sanitize_input(form.get("long_description", ""))
    collection_end = form.get("collection_end", "")
    review_end = form.get("review_end", "")

    class_id = int(class_id_str) if class_id_str.isdigit() else None

    errors = []
    if (not title or not class_id or not collection_end or not review_end
       or not short_description or not long_description):
        errors.append("Kaikki pakolliset kentät on täytettävä.")

    if len(short_description) > 255:
        errors.append("Lyhyt kuvaus saa olla enintään 255 merkkiä.")

    if len(long_description) > 2000:
        errors.append("Pitkä kuvaus saa olla enintään 2000 merkkiä.")

    if errors:
        for error in errors:
            flash(error)
        return redirect(url_for("admin.edit_contest", contest_id=contest_id))

    anonymity = 1 if form.get("anonymity") == "on" else 0
    public_reviews = 1 if form.get("public_reviews") == "on" else 0
    public_results = 1 if form.get("public_results") == "on" else 0

    contest_data = {
        "title": title,
        "class_id": class_id,
        "short_description": short_description,
        "long_description": long_description,
        "anonymity": anonymity,
        "public_reviews": public_reviews,
        "public_results": public_results,
        "collection_end": collection_end,
        "review_end": review_end
    }

    sql.update_contest(contest_id, contest_data)

    flash("Kilpailun tiedot päivitetty.")
    return redirect(url_for("admin.admin_contests"))


@admin_bp.route("/users/new")
def new_user():
    """Renders the form for creating a new user."""
    if not session.get("super_user"):
        abort(403)
    return render_template("admin/new_user.html")


@admin_bp.route("/users/create", methods=["POST"])
def create_user():
    """Handles the POST request to create a new user."""
    check_csrf()
    if not session.get("super_user"):
        abort(403)

    name = sanitize_input(request.form.get("name", ""))
    username = sanitize_input(request.form.get("username", ""))
    password = request.form.get("password", "")
    is_super = 1 if request.form.get("is_super") == "on" else 0

    session["form_data"] = {
        "name": name,
        "username": username,
        "is_super": is_super
    }

    if not name or not username or not password:
        flash("Kaikki kentät ovat pakollisia.")
        return redirect(url_for("admin.new_user"))

    if not is_valid_email(username):
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: Sähköpostiosoite ei ole kelvollinen.")
        return redirect(url_for("admin.new_user"))

    success = users.create_user(name, username, password, is_super)
    if not success:
        flash("Käyttäjänimi on jo käytössä.")
        return redirect(url_for("admin.new_user"))

    session.pop("form_data", None)
    flash("Uusi käyttäjä on luotu.")
    return redirect(url_for("admin.admin_users"))


@admin_bp.route("/users/edit/<int:user_id>")
def edit_user(user_id):
    """Renders the form for editing an existing user.

    Args:
        user_id (int): The ID of the user to edit.
    """
    if not session.get("super_user"):
        abort(403)
    user = users.get_user(user_id)
    if not user:
        flash("Käyttäjää ei löytynyt.")
        return redirect(url_for("admin.admin_users"))
    return render_template("admin/edit_user.html", user=user)


@admin_bp.route("/users/update/<int:user_id>", methods=["POST"])
def update_user(user_id):
    """Handles the POST request to update a user's details.

    Args:
        user_id (int): The ID of the user to update.
    """
    check_csrf()  # Add CSRF check for security
    if not session.get("super_user"):
        abort(403)

    user = users.get_user(user_id)
    if not user:
        abort(404)  # Abort if user not found

    name = sanitize_input(request.form.get("name", ""))
    username = sanitize_input(request.form.get("username", ""))
    is_super = 1 if request.form.get("is_super") == "on" else 0
    password = request.form.get("password", "")

    # --- Validation Logic ---
    if not name or not username:
        flash("Nimi ja käyttäjätunnus ovat pakollisia.")
        return render_template("admin/edit_user.html", user=user)

    if not is_valid_email(username):
        flash("Virhe: Sähköpostiosoite ei ole kelvollinen.")
        return render_template("admin/edit_user.html", user=user)

    if password and len(password) < config.PASSWORD_MIN_LENGTH:
        flash(f"Salasanan on oltava vähintään {config.PASSWORD_MIN_LENGTH} "
              "merkkiä pitkä.")
        return render_template("admin/edit_user.html", user=user)
    # --- End Validation ---

    try:
        # Update user details
        users.update_user(user_id, name, username, is_super)

        if password:
            users.update_user_password(user_id, password)

        flash("Käyttäjän tiedot päivitetty.")
    except sqlite3.IntegrityError:
        flash("Käyttäjätunnus on jo käytössä.")
        return render_template("admin/edit_user.html", user=user)
    except Exception as e:
        print(f"Error updating user: {e}")
        flash("Käyttäjän tietoja ei voitu päivittää.")
        return render_template("admin/edit_user.html", user=user)

    return redirect(url_for("admin.admin_users"))


@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    """Handles the POST request to delete a user.

    Args:
        user_id (int): The ID of the user to delete.
    """
    check_csrf()
    if not session.get("super_user"):
        abort(403)

    # Prevent deleting oneself
    if int(user_id) == session.get("user_id", -1):
        flash("Et voi poistaa omaa tunnustasi.")
        return redirect(url_for("admin.admin_users"))

    user_to_delete = users.get_user(user_id)
    if not user_to_delete:
        # This handles the case of trying to delete a non-existent user
        flash("Käyttäjää ei löytynyt.")
        return redirect(url_for("admin.admin_users"))

    # Prevent deleting a superuser
    if user_to_delete["super_user"]:
        flash("Pääkäyttäjiä ei voi poistaa.")
        return redirect(url_for("admin.admin_users"))

    try:
        users.delete_user(user_id)
        flash("Käyttäjä on poistettu.")
    except Exception as e:
        print(f"Error deleting user: {e}")
        flash("Käyttäjää ei voitu poistaa.")

    return redirect(url_for("admin.admin_users"))


@admin_bp.route("/entries/new", methods=["GET", "POST"])
def new_entry():
    """Renders the form for creating a new entry and handles its submission."""
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
            return redirect(url_for("admin.admin_entries"))
        except Exception as e:
            if ("UNIQUE constraint failed" in str(e)
               or "duplicate key" in str(e)):
                flash("Tällä käyttäjällä on jo teksti tässä kilpailussa.")
            else:
                flash("Tekstiä ei voitu luoda.")
            return render_template(
                "admin/new_entry.html",
                contests=contests,
                users=users_list,
                entry=entry_text,
                selected_contest_id=contest_id,
                selected_user_id=user_id
            )

    return render_template("admin/new_entry.html", contests=contests,
                           users=users_list)


@admin_bp.route("/entries/create", methods=["POST"])
def create_entry():
    """Handles the POST request to create a new entry."""
    check_csrf()
    if not session.get("super_user"):
        abort(403)

    contest_id = request.form.get("contest_id")
    user_id = request.form.get("user_id")
    entry_text = sanitize_input(request.form.get("entry", ""))

    if not contest_id or not user_id or not entry_text:
        flash("Kaikki pakolliset kentät on täytettävä.")
        return redirect(url_for("admin.new_entry"))

    try:
        sql.create_entry(contest_id, user_id, entry_text)
        flash("Teksti on luotu.")
        return redirect(url_for("admin.admin_entries"))
    except Exception as e:
        print("Virhe tekstin luomisessa:", e)
        flash("Tekstiä ei voitu luoda.")
        return redirect(url_for("admin.new_entry"))


@admin_bp.route("/entries/edit/<int:entry_id>")
def edit_entry(entry_id):
    """Renders the form for editing an existing entry.

    Args:
        entry_id (int): The ID of the entry to edit.
    """
    if not session.get("super_user"):
        abort(403)
    entry = sql.get_entry_by_id(entry_id)
    contests = sql.get_all_contests()
    users_list = users.get_all_users()
    if not entry:
        abort(404)
    return render_template("admin/edit_entry.html", entry=entry,
                           contests=contests, users=users_list)


@admin_bp.route("/entries/update/<int:entry_id>", methods=["POST"])
def update_entry(entry_id):
    """Handles the POST request to update an entry.

    Args:
        entry_id (int): The ID of the entry to update.
    """
    check_csrf()
    if not session.get("super_user"):
        abort(403)

    contest_id = request.form.get("contest_id")
    user_id = request.form.get("user_id")
    entry_text = sanitize_input(request.form.get("entry", ""))

    if not contest_id or not user_id or not entry_text:
        flash("Kaikki pakolliset kentät on täytettävä.")
        return redirect(url_for("admin.edit_entry", entry_id=entry_id))

    try:
        sql.update_entry(entry_id, contest_id, user_id, entry_text)
        flash("Tekstin tiedot päivitetty.")
        return redirect(url_for("admin.admin_entries"))
    except Exception as e:
        print("Virhe tekstin päivittämisessä:", e)
        flash("Tekstiä ei voitu päivittää.")
        return redirect(url_for("admin.edit_entry", entry_id=entry_id))


@admin_bp.route("/entries/delete/<int:entry_id>", methods=["POST"])
def delete_entry(entry_id):
    """Handles the POST request to delete an entry.

    Args:
        entry_id (int): The ID of the entry to delete.
    """
    check_csrf()
    if not session.get("super_user"):
        abort(403)
    try:
        sql.delete_entry(entry_id)
        flash("Teksti on poistettu.")
    except Exception as e:
        print("Virhe tekstin poistossa:", e)
        flash("Tekstiä ei voitu poistaa.")
    return redirect(url_for("admin.admin_entries"))
