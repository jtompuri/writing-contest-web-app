import sqlite3
from flask import Flask
from flask import redirect, render_template, request, abort, session, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
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

@app.route("/")
def index():
    contests_for_entry = sql.get_contests_for_entry()
    contests_for_review = sql.get_contests_for_review()
    contests_for_results = sql.get_contests_for_results()
    return render_template("index.html",  contests_for_entry=contests_for_entry, 
                contests_for_review=contests_for_review, contests_for_results=contests_for_results)


@app.route("/contest/<int:contest_id>")
def contest(contest_id):
    contest = sql.get_contest_by_id(contest_id)
    if not contest:
        abort(404)
    return render_template("contest.html", contest=contest)

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

    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (name, username, password_hash) VALUES (?, ?, ?)"
        db.execute(sql, [name, username, password_hash])
    except sqlite3.IntegrityError:
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: tunnus on jo varattu.")
        return redirect("/register")

    session["form_data"] = {"username": username}
    flash("Tunnus on luotu.")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", next_page=request.referrer)

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        next_page = request.form.get("next_page", "/")

        user_id = users.check_login(username, password)
        if user_id:
            session["user_id"] = user_id
            session["csrf_token"] = secrets.token_hex(16)
            return redirect(next_page)
        else:
            flash("Virhe: Väärä tunnus tai salasana.")
            return render_template("login.html", next_page=next_page)

    return redirect("/login")

@app.route("/logout")
def logout():
    del session["user_id"]
    del session["csrf_token"]
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