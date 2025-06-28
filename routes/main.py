"""Main blueprint routes for public and general pages.

This module contains the main (public) routes for the Writing Contest Web App,
including the index, contest listing, results, reviews, and terms of use.

Blueprints:
    main_bp (Blueprint): Handles public-facing routes.
"""

from datetime import datetime, date

from flask import (Blueprint, render_template, request, session, abort, flash,
                   url_for, redirect)

import config
import sql

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    contests_for_entry = sql.get_contests_for_entry(3)
    contests_for_review = sql.get_contests_for_review(3)
    contests_for_results = sql.get_contests_for_results(3)

    # Get winners for the latest contest with results
    winners = []
    latest_result = None
    if contests_for_results:
        # Find the latest contest with public_results == True
        for c in contests_for_results:
            if c["public_results"]:
                latest_result = dict(c)  # Convert Row to dict
                break
        if latest_result:
            winners = sql.get_contest_results(latest_result["id"])[:3]
            for i in range(len(winners)):
                winner = dict(winners[i])  # Convert Row to dict
                winner["id"] = winner.get("entry_id", winner.get("id"))
                # Only set contest-level fields if not present in the entry
                for field in [
                    "short_description", "class_value", "anonymity",
                    "public_reviews", "public_results", "review_end",
                    "collection_end", "total_entries"
                ]:
                    if field not in winner or winner[field] in (None, ""):
                        winner[field] = latest_result.get(field, "")
                winners[i] = winner  # Replace with dict

    today = date.today().isoformat()  # Add this line

    return render_template(
        "index.html",
        contests_for_entry=contests_for_entry,
        contests_for_review=contests_for_review,
        contests_for_results=contests_for_results,
        winners=winners,
        latest_result=latest_result,
        today=today  # Pass today to the template
    )


@main_bp.route("/contests/contest/<int:contest_id>")
def contest(contest_id):
    contest = sql.get_contest_by_id(contest_id)
    if not contest:
        abort(404)

    today = datetime.now().date()
    collection_end = datetime.strptime(contest["collection_end"],
                                       "%Y-%m-%d").date()
    review_end = datetime.strptime(contest["review_end"], "%Y-%m-%d").date()

    collection_open = today <= collection_end
    review_open = collection_end < today <= review_end

    has_entry = False
    user_entry_id = None
    if session.get("user_id"):
        entry = sql.get_user_entry_for_contest(contest_id, session["user_id"])
        if entry:
            has_entry = True
            user_entry_id = entry["id"]

    return render_template(
        "contest.html",
        contest=contest,
        collection_open=collection_open,
        review_open=review_open,
        has_entry=has_entry,
        user_entry_id=user_entry_id,
        source="contest"
    )


@main_bp.route("/contests")
def contests():
    page = request.args.get("page", 1, type=int)
    per_page = config.DEFAULT_PER_PAGE
    offset = (page - 1) * per_page

    contests = sql.get_contests_for_entry(limit=per_page, offset=offset)
    total = sql.get_entry_contest_count()
    today = date.today().isoformat()

    return render_template(
        "contests.html",
        contests=contests,
        page=page,
        per_page=per_page,
        total=total,
        today=today
    )


@main_bp.route("/results")
def results():
    page = request.args.get("page", 1, type=int)
    per_page = config.DEFAULT_PER_PAGE
    offset = (page - 1) * per_page

    contests = sql.get_contests_for_results(limit=per_page, offset=offset)
    total = sql.get_results_contest_count()
    today = date.today().isoformat()

    key = request.args.get("key")
    visible_contests = [
        c for c in contests if c["public_results"]
        or (key and c["private_key"] == key)
    ]

    return render_template(
        "results.html",
        contests=visible_contests,
        page=page,
        per_page=per_page,
        total=total,
        base_url="/results?page=",
        today=today,
        key=key
    )


@main_bp.route("/reviews")
def reviews():
    page = request.args.get("page", 1, type=int)
    per_page = config.DEFAULT_PER_PAGE
    offset = (page - 1) * per_page

    contests = sql.get_contests_for_review(limit=per_page, offset=offset)
    total = sql.get_review_contest_count()

    key = request.args.get("key")
    visible_contests = [
        c for c in contests if c["public_reviews"]
        or (key and c["private_key"] == key)
    ]

    return render_template(
        "reviews.html",
        contests=visible_contests,
        page=page,
        per_page=per_page,
        total=total,
        base_url="/reviews?page=",
        key=key
    )


@main_bp.route("/terms_of_use")
def terms_of_use():
    return render_template("terms_of_use.html")


@main_bp.route("/result/<int:contest_id>")
def result(contest_id):
    contest = sql.get_contest_by_id(contest_id)
    if not contest:
        abort(404)

    if not contest["public_results"]:
        private_key_param = request.args.get("key", "")
        if (not private_key_param
           or private_key_param != contest["private_key"]):
            flash("Tämän kilpailun tulokset eivät ole julkisia.")
            return redirect(url_for("main.results"))

    entries = sql.get_contest_results(contest_id)
    return render_template(
        "result.html",
        contest=contest,
        entries=entries
    )
