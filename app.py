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


@app.before_request
def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)


@app.template_filter("format_date")
def format_date(value):
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.strftime("%-d.%m.%Y")
    except ValueError:
        return value


def check_csrf():
    token = request.form.get("csrf_token")
    if not token or token != session.get("csrf_token"):
        abort(403)


def sanitize_input(text):
    if not isinstance(text, str):
        return ""

    text = text.strip()
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'on\w+=".*?"', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(javascript:|data:|vbscript:)', '', text, flags=re.IGNORECASE)

    return text


def is_valid_email(email):
    return re.match(r"^[^@]+@[^@]+\.[^@]+$", email)


def format_text(text, links_allowed=False):
    text = text.replace('\n', '<br />')
    text = re.sub(r' {2,}', lambda m: '&nbsp;' * len(m.group()), text)
    text = re.sub(r'\*(\S(?:.*?\S)?)\*', r'<strong>\1</strong>', text)
    text = re.sub(r'_(\S(?:.*?\S)?)_', r'<em>\1</em>', text)

    if links_allowed:
        email_regex = r'([\w\.-]+@[\w\.-]+\.\w+)'
        text = re.sub(email_regex, r'<a href="mailto:\1">\1</a>', text)

        url_regex = r'(?<!href=")(https?://[^\s<>"]+)'
        text = re.sub(url_regex, r'<a href="\1" target="_blank" rel="noopener">\1</a>', text)

    return Markup(text)


@app.template_filter('richtext')
def richtext_filter(s):
    return format_text(s, links_allowed=False)


@app.template_filter('richtext_with_links')
def richtext_with_links_filter(s):
    return format_text(s, links_allowed=True)


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
        stats=stats)


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/create", methods=["POST"])
def create():
    check_csrf()
    name = sanitize_input(request.form["name"])
    username = sanitize_input(request.form["username"])
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    if not username or len(username) > 50 or not name or len(name) > 50 or len(password1) > 50 or len(password2) > 50:
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: Tarkista syötteet.")
        return redirect("/register")

    if password1 != password2:
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: salasanat eivät ole samat.")
        return redirect("/register")

    if len(password1) < 8:
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: salasanan on oltava vähintään 6 merkkiä pitkä.")
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
            return render_template("login.html", next_page=next_page, username=username)

    return redirect("/login")


@app.route("/admin")
def admin():
    if not session.get("super_user"):
        abort(403)

    contest_count = sql.get_contest_count()
    user_count = users.get_user_count()
    entry_count = sql.get_entry_count()

    return render_template("admin/index.html", 
        contest_count=contest_count,
        user_count=user_count,
        entry_count=entry_count
    )


@app.route("/admin/contests")
def admin_contests():
    if not session.get("super_user"):
        abort(403)

    contests = sql.get_all_contests()
    return render_template("admin/contests.html", contests=contests)


@app.route("/admin/contests/new")
def admin_new_contest():
    if not session.get("super_user"):
        abort(403)

    classes = sql.get_all_classes()
    return render_template("admin/new_contest.html", classes=classes)


@app.route("/admin/contests/create", methods=["POST"])
def admin_create_contest():
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

    if not title or not class_id or not collection_end or not review_end or not short_description or not long_description:
        flash("Kaikki pakolliset kentät on täytettävä.")
        return redirect(url_for("admin_new_contest"))

    anonymity = 1 if form.get("anonymity") == "on" else 0
    public_reviews = 1 if form.get("public_reviews") == "on" else 0
    public_results = 1 if form.get("public_results") == "on" else 0

    try:
        sql.create_contest(title, class_id, short_description, long_description,
                           anonymity, public_reviews, public_results,
                           collection_end, review_end)
        flash("Kilpailu on luotu.")
        return redirect(url_for("admin_contests"))
    except Exception as e:
        print("Virhe kilpailun luomisessa:", e)
        flash("Kilpailua ei voitu luoda.")
        return redirect(url_for("admin_new_contest"))


@app.route("/admin/contests/delete/<int:contest_id>", methods=["POST"])
def delete_contest(contest_id):
    check_csrf()
    if not session.get("super_user"):
        abort(403)
    
    sql.delete_contest(contest_id)
    flash("Kilpailu on poistettu.")
    return redirect(url_for("admin_contests"))


@app.route("/admin/users")
def admin_users():
    if not session.get("super_user"):
        abort(403)
    users_list = users.get_all_users()
    return render_template("admin/users.html", users=users_list)


@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
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
    if not session.get("super_user"):
        abort(403)
    return render_template("admin/new_user.html")


@app.route("/admin/users/create", methods=["POST"])
def admin_create_user():
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
    if not session.get("super_user"):
        abort(403)

    user = users.get_user(user_id)
    if not user:
        flash("Käyttäjää ei löytynyt.")
        return redirect(url_for("admin_users"))

    return render_template("admin/edit_user.html", user=user)


@app.route("/admin/users/update/<int:user_id>", methods=["POST"])
def admin_update_user(user_id):
    if not session.get("super_user"):
        abort(403)

    name = sanitize_input(request.form["name"])
    username = sanitize_input(request.form["username"])
    is_super = 1 if request.form.get("is_super") == "on" else 0
    password = sanitize_input(request.form.get("password", ""))

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
                flash("Salasanan on oltava vähintään 6 merkkiä pitkä.")
                return redirect(url_for("admin_edit_user", user_id=user_id))
            users.update_password(user_id, password)

        flash("Käyttäjän tiedot päivitetty.")
        return redirect(url_for("admin_users"))
    except sqlite3.IntegrityError:
        flash("Käyttäjätunnus on jo käytössä.")
        return redirect(url_for("admin_edit_user", user_id=user_id))


@app.route("/admin/entries")
def admin_entries():
    if not session.get("super_user"):
        abort(403)
    entries = sql.get_all_entries()
    return render_template("admin/entries.html", entries=entries)


@app.route("/admin/contests/edit/<int:contest_id>")
def edit_contest(contest_id):
    if not session.get("super_user"):
        abort(403)

    contest = sql.get_contest_by_id(contest_id)
    classes = sql.get_all_classes()

    if not contest:
        abort(404)

    return render_template("admin/edit_contest.html", contest=contest, classes=classes)


@app.route("/admin/contests/update/<int:contest_id>", methods=["POST"])
def admin_update_contest(contest_id):
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

    if not title or not class_id or not collection_end or not review_end or not short_description or not long_description:
        flash("Kaikki pakolliset kentät on täytettävä.")
        return redirect(url_for("edit_contest", contest_id=contest_id))

    anonymity = 1 if form.get("anonymity") == "on" else 0
    public_reviews = 1 if form.get("public_reviews") == "on" else 0
    public_results = 1 if form.get("public_results") == "on" else 0

    sql.update_contest(contest_id, title, class_id, short_description, long_description,
                       anonymity, public_reviews, public_results,
                       collection_end, review_end)

    flash("Kilpailun tiedot päivitetty.")
    return redirect(url_for("admin_contests"))


@app.route("/contests/contest/<int:contest_id>/add_entry", methods=["GET", "POST"])
def add_entry(contest_id):
    check_csrf()
    if not session.get("user_id"):
        flash("Kirjaudu sisään osallistuaksesi kilpailuun.")
        return redirect(url_for("login", next_page=request.path))

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

    if request.method == "GET":
        entry = request.args.get("entry", "")
        return render_template("add_entry.html", contest=contest,
                               collection_ended=collection_ended,
                               review_ended=review_ended,
                               stats=stats, entry=entry)

    if request.method == "POST":
        action = request.form.get("action")
        entry = sanitize_input(request.form.get("entry", ""))

        if not entry:
            flash("Kilpailutyö ei saa olla tyhjä.")
            return redirect(url_for("add_entry", contest_id=contest_id))

        if action == "preview":
            return render_template("preview_entry.html", contest=contest,
                                entry=entry, collection_ended=collection_ended,
                                review_ended=review_ended, stats=stats)

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
    check_csrf()
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