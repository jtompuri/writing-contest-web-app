import sqlite3, re
from flask import Flask
from flask import redirect, render_template, request, abort, session, flash, url_for
from werkzeug.security import generate_password_hash
from markupsafe import Markup
from datetime import datetime
import db, config, users, secrets, sql

app = Flask(__name__)
app.secret_key = config.secret_key
app.teardown_appcontext(db.close_connection)

@app.template_filter("format_date")
def format_date(value):
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.strftime("%-d.%m.%Y")
    except ValueError:
        return value


def format_text(text):
    text = text.replace('\n', '<br />')
    text = re.sub(r' {2,}', lambda m: '&nbsp;' * len(m.group()), text)
    text = re.sub(r'\*(.*?)\*', r'<strong>\1</strong>', text)
    text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
    email_regex = r'([\w\.-]+@[\w\.-]+\.\w+)'
    text = re.sub(email_regex, r'<a href="mailto:\1">\1</a>', text)
    return Markup(text)


@app.template_filter('richtext')
def richtext_filter(s):
    return format_text(s)


@app.route("/")
def index():
    contests_for_entry = sql.get_contests_for_entry(3)
    contests_for_review = sql.get_contests_for_review(3)
    contests_for_results = sql.get_contests_for_results(3)
    return render_template("index.html",  contests_for_entry=contests_for_entry, 
                contests_for_review=contests_for_review, contests_for_results=contests_for_results)


@app.route("/contests/contest/<int:contest_id>")
def contest(contest_id):
    contest = sql.get_contest_by_id(contest_id)
    if not contest:
        abort(404)

    today = datetime.now().date()

    collection_end = datetime.strptime(contest["collection_end"], "%Y-%m-%d").date()
    review_end = datetime.strptime(contest["review_end"], "%Y-%m-%d").date()

    collection_ended = collection_end <= today
    review_ended = review_end <= today

    stats = {}
    if collection_ended:
        stats["entry_count"] = sql.get_entry_count(contest_id)
        stats["review_count"] = sql.get_review_count(contest_id)

    print("TODAY:", today)
    print("REVIEW_END:", review_end)
    print("REVIEW_ENDED:", review_ended)
    print("PUBLIC REVIEWS:", contest["public_reviews"])

    return render_template(
        "contest.html",
        contest=contest,
        collection_ended=collection_ended,
        review_ended=review_ended,
        stats=stats
    )

@app.route("/contests/contest/<int:contest_id>/add_entry")
def add_entry(contest_id):
    return render_template("add_entry.html", contest_id=contest_id)


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/create", methods=["POST"])
def create():
    name = request.form["name"]
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    if not username or len(username) > 50 or not name or len(name) > 50 or len(password1) > 50 or len(password2) > 50:
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: Tarkista syötteet.")
        return redirect("/register")
    
    if password1 != password2:
        flash("Virhe: salasanat eivät ole samat.")
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
        flash("Pääkäyttäjän tunnus on luotu. Tällä tunnuksella on täydet käyttöoikeudet.")
    else:
        flash("Tunnus on luotu.")
    
    return redirect(url_for("login", next_page="/"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        username = session.pop("form_data", {}).get("username", "")
        next_page = request.args.get("next_page", "/")
        return render_template("login.html", next_page=next_page, username=username)

    if request.method == "POST":
        username = request.form["username"]
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
            session["csrf_token"] = secrets.token_hex(16)

            return redirect(next_page)
        else:
            flash("Virhe: Väärä tunnus tai salasana.")
            return render_template("login.html", next_page=next_page, username=username)

    return redirect("/login")

@app.route("/admin")
def admin():
    if not session.get("super_user"):
        abort(403)
    return render_template("admin.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/contests")
def contests():
    return render_template("contests.html")


@app.route("/results")
def results():
    return render_template("results.html")


@app.route("/my_texts")
def my_texts():
    return render_template("my_texts.html")


@app.route("/terms_of_use")
def terms_of_use():
    return render_template("terms_of_use.html")