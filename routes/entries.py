"""Entries blueprint routes for user entry actions.

This module contains routes for adding, editing, deleting, and viewing contest
entries, as well as reviewing entries, for the Writing Contest Web App.

Blueprints:
    entries_bp (Blueprint): Handles entry-related routes.
"""

from datetime import datetime, date

from flask import (Blueprint, render_template, request, session, abort, flash,
                   url_for, redirect)

import config
import sql
from utils import check_csrf, sanitize_input

entries_bp = Blueprint('entries', __name__)


def _handle_add_entry_post(contest, collection_open, review_open):
    """Handles the POST logic for adding a new contest entry."""
    check_csrf()
    action = request.form.get("action")
    entry_text = sanitize_input(request.form.get("entry", ""))

    if not entry_text:
        flash("Kilpailutyö ei saa olla tyhjä.")
        return redirect(url_for("entries.add_entry",
                                contest_id=contest["id"]))

    if action == "preview":
        return render_template(
            "preview_entry.html",
            contest=contest,
            entry=entry_text,
            collection_open=collection_open,
            review_open=review_open
        )

    if action == "submit":
        user_id = session["user_id"]
        if sql.entry_exists(contest["id"], user_id):
            flash("Olet jo osallistunut tähän kilpailuun.")
            return redirect(url_for("main.contest", contest_id=contest["id"]))

        sql.create_entry(contest["id"], user_id, entry_text)
        flash("Kilpailutyö on tallennettu.")
        return redirect(url_for("main.contest", contest_id=contest["id"]))

    # Fallback for unknown actions
    return redirect(url_for("main.index"))


@entries_bp.route("/contests/contest/<int:contest_id>/add_entry",
                  methods=["GET", "POST"])
def add_entry(contest_id):
    """Renders the form for adding an entry and handles its submission.

    On GET, displays the submission form. On POST, handles previewing or
    submitting a new contest entry.

    Args:
        contest_id (int): The ID of the contest to add an entry to.
    """
    if not session.get("user_id"):
        flash("Kirjaudu sisään osallistuaksesi kilpailuun.")
        return redirect(url_for("auth.login", next_page=request.path))

    contest = sql.get_contest_by_id(contest_id)
    if not contest:
        abort(404)

    today = datetime.now().date()
    collection_end = datetime.strptime(contest["collection_end"],
                                       "%Y-%m-%d").date()
    review_end = datetime.strptime(contest["review_end"], "%Y-%m-%d").date()
    collection_open = today <= collection_end
    review_open = collection_end < today <= review_end

    if request.method == "POST":
        return _handle_add_entry_post(contest, collection_open, review_open)

    # This handles the GET request
    entry_text = request.args.get("entry", "")
    return render_template(
        "add_entry.html",
        contest=contest,
        collection_open=collection_open,
        review_open=review_open,
        entry=entry_text
    )


@entries_bp.route("/my_texts")
def my_texts():
    """Displays a paginated list of the current user's entries and results."""
    if not session.get("user_id"):
        flash("Kirjaudu sisään nähdäksesi omat tekstisi.")
        return redirect(url_for("auth.login", next_page=request.path))
    entries = sql.get_user_entries_with_results(session["user_id"])
    total = sql.get_user_entry_count(session["user_id"])
    review_count = sql.get_user_review_count(session["user_id"])
    today = date.today().isoformat()

    # Normalize: ensure each entry has .id for contest id
    normalized_entries = []
    for entry_data in entries:
        entry_data = dict(entry_data)
        if "contest_id" in entry_data:
            entry_data["id"] = entry_data["contest_id"]
        normalized_entries.append(entry_data)

    per_page = config.DEFAULT_PER_PAGE
    page = int(request.args.get("page", 1))
    start = (page - 1) * per_page
    end = start + per_page
    paginated_entries = normalized_entries[start:end]
    return render_template(
        "my_texts.html",
        all_entries=paginated_entries,
        total=total,
        per_page=per_page,
        page=page,
        today=today,
        review_count=review_count
    )


@entries_bp.route("/entry/<int:entry_id>")
def entry(entry_id):
    """Displays a single contest entry.

    Handles access control for private results or reviews via a 'key'
    URL parameter.

    Args:
        entry_id (int): The ID of the entry to display.
    """
    entry_data = sql.get_entry_by_id(entry_id)
    if not entry_data:
        abort(404)
    idx = request.args.get("idx")
    source = request.args.get("source")
    private_key_param = request.args.get("key", "")

    contest = sql.get_contest_by_id(entry_data["contest_id"])
    if not contest:
        abort(404)

    if source == "result" and not contest["public_results"]:
        if (not private_key_param or
           private_key_param != contest["private_key"]):
            flash("Tämän kilpailun tulokset eivät ole julkisia.")
            return redirect(url_for("main.results"))

    if source == "review" and not contest["public_reviews"]:
        if (not private_key_param
           or private_key_param != contest["private_key"]):
            flash("Tämän kilpailun arviointi ei ole julkista.")
            return redirect(url_for("main.reviews"))

    return render_template("entry.html", entry=entry_data,
                           now=date.today().isoformat(), idx=idx,
                           source=source)


def _validate_entry_edit_access(entry_id):
    """Validates if the current user can edit the specified entry."""
    if not session.get("user_id"):
        abort(403)

    entry_data = sql.get_entry_by_id(entry_id)
    if not entry_data or entry_data["user_id"] != session["user_id"]:
        abort(403)

    contest = sql.get_contest_by_id(entry_data["contest_id"])
    if not contest:
        flash("Kilpailua ei löytynyt.")
        return None, None

    collection_end = datetime.strptime(
        contest["collection_end"], "%Y-%m-%d").date()
    if collection_end < date.today():
        flash("Et voi enää muokata tätä tekstiä.")
        return None, None

    return entry_data, contest


def _handle_edit_entry_post(entry_data, contest, entry_id):
    """Handles the POST logic for editing an entry."""
    check_csrf()
    action = request.form.get("action")
    new_text = sanitize_input(request.form.get("entry", ""))
    source = request.form.get("source", "")

    if not new_text:
        flash("Teksti ei saa olla tyhjä.")
        return render_template("edit_entry.html", entry=entry_data,
                               contest=contest, source=source)

    if action == "preview":
        return render_template(
            "preview_entry.html", contest=contest, entry=new_text,
            edit_mode=True, entry_id=entry_id, source=source
        )

    if action == "back":
        entry_data = dict(entry_data)
        entry_data["entry"] = new_text
        return render_template("edit_entry.html", entry=entry_data,
                               contest=contest, source=source)

    if action == "submit":
        sql.update_entry(entry_id, entry_data["contest_id"],
                         session["user_id"], new_text)
        flash("Kilpailutyö on päivitetty.")
        if source == "contest":
            return redirect(url_for("main.contest",
                                    contest_id=entry_data["contest_id"]))
        return redirect(url_for("entries.my_texts"))

    # Fallback for unknown actions
    return redirect(url_for("entries.my_texts"))


@entries_bp.route("/entry/<int:entry_id>/edit", methods=["GET", "POST"])
def edit_entry(entry_id):
    """Renders the form for editing an entry and handles its update.

    On GET, displays the edit form. On POST, handles previewing or
    submitting the updated entry. Ensures the user owns the entry and
    the contest collection period is still open.

    Args:
        entry_id (int): The ID of the entry to edit.
    """
    entry_data, contest = _validate_entry_edit_access(entry_id)
    if not entry_data:
        return redirect(url_for("entries.my_texts"))

    if request.method == "POST":
        return _handle_edit_entry_post(entry_data, contest, entry_id)

    # This handles the GET request
    source = request.args.get("source", "")
    entry_text = request.args.get("entry")
    if entry_text is not None:
        entry_data = dict(entry_data)
        entry_data["entry"] = entry_text
    return render_template("edit_entry.html", entry=entry_data,
                           contest=contest, source=source)


@entries_bp.route("/entry/<int:entry_id>/delete", methods=["POST"])
def delete_entry(entry_id):
    """Handles the POST request to delete an entry.

    Ensures the user owns the entry and the contest collection period
    is still open.

    Args:
        entry_id (int): The ID of the entry to delete.
    """
    if not session.get("user_id"):
        abort(403)
    entry_data = sql.get_entry_by_id(entry_id)
    if not entry_data or entry_data["user_id"] != session["user_id"]:
        abort(403)
    contest = sql.get_contest_by_id(entry_data["contest_id"])
    today = date.today().isoformat()
    if not contest or contest["collection_end"] <= today:
        flash("Et voi enää poistaa tätä tekstiä.")
        return redirect(url_for("entries.my_texts"))
    sql.delete_entry(entry_id)
    flash("Teksti poistettu.")
    return redirect(url_for("entries.my_texts"))


@entries_bp.route("/review/<int:contest_id>", methods=["GET", "POST"])
def review(contest_id):
    """Renders the review page and handles submission of reviews.

    On GET, displays all entries for a contest for reviewing. On POST,
    validates and saves the user's reviews for all entries.

    Args:
        contest_id (int): The ID of the contest to review.
    """
    if not session.get("user_id"):
        flash("Kirjaudu sisään arvioidaksesi kilpailutöitä.")
        return redirect(url_for("auth.login", next_page=request.path))

    contest = sql.get_contest_by_id(contest_id)
    if not contest:
        abort(404)

    private_key_param = request.args.get("key", "")

    if not contest["public_reviews"]:
        if (not private_key_param
           or private_key_param != contest["private_key"]):
            flash("Tämän kilpailun arviointi ei ole julkinen.")
            return redirect(url_for("main.reviews"))

    today = datetime.now().date()
    collection_end = datetime.strptime(contest["collection_end"],
                                       "%Y-%m-%d").date()
    review_end = datetime.strptime(contest["review_end"], "%Y-%m-%d").date()
    if not collection_end <= today < review_end:
        flash("Kilpailun arviointijakso ei ole käynnissä.")
        return redirect(url_for("main.reviews"))

    entries = sql.get_entries_for_review(contest_id)

    if request.method == "POST":
        check_csrf()
        user_id = session["user_id"]
        errors = []
        rated_entry_ids = set()
        for entry_item in entries:
            key = f"points_{entry_item['id']}"
            value = request.form.get(key)
            if value is None or value == "":
                errors.append("Kaikki tekstit on arvioitava. Puuttuu: "
                              f"{entry_item['author_name']}")
            else:
                try:
                    points = int(value)
                    if points < 0 or points > 5:
                        errors.append("Arvosanan tulee olla välillä 0–5. "
                                      f"({entry_item['author_name']})")
                    else:
                        rated_entry_ids.add(entry_item["id"])
                except ValueError:
                    errors.append("Virheellinen arvosana: "
                                  f"{entry_item['author_name']}")

        if errors or len(rated_entry_ids) != len(entries):
            flash("Kaikki tekstit on arvioitava ja arvosanojen tulee olla "
                  "välillä 0-5.")
            for error in errors:
                flash(error)
            user_reviews = sql.get_user_reviews_for_contest(contest_id,
                                                            session["user_id"])
            return render_template("review.html", contest=contest,
                                   entries=entries, user_reviews=user_reviews)

        for entry_item in entries:
            points = int(request.form[f"points_{entry_item['id']}"])
            sql.save_review(entry_item["id"], user_id, points)
        flash("Arviot tallennettu.")
        return redirect(url_for("main.reviews"))

    if request.method == "GET":
        user_reviews = sql.get_user_reviews_for_contest(contest_id,
                                                        session["user_id"])
        return render_template(
            "review.html",
            contest=contest,
            entries=entries,
            user_reviews=user_reviews
        )

    return render_template(
        "review.html",
        contest=contest,
        entries=entries
    )
