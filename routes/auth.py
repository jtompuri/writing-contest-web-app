"""Authentication blueprint routes.

This module contains routes for user registration, login, and logout
for the Writing Contest Web App.

Blueprints:
    auth_bp (Blueprint): Handles authentication-related routes.
"""

from flask import Blueprint, render_template, request, session, flash, redirect, url_for

import users
from utils import check_csrf, sanitize_input, is_valid_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register")
def register():
    return render_template("register.html")

@auth_bp.route("/create", methods=["POST"])
def create():
    check_csrf()
    name = sanitize_input(request.form["name"])
    username = sanitize_input(request.form["username"])
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    if (not username or len(username) > 50 or not name or len(name) > 50 or len(password1) > 50 or len(password2) > 50):
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
        flash("Pääkäyttäjän tunnus on luotu. Tällä tunnuksella on täydet käyttöoikeudet.")
    else:
        flash("Tunnus on luotu.")

    return redirect(url_for("auth.login", next_page="/"))

@auth_bp.route("/login", methods=["GET", "POST"])
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

@auth_bp.route("/logout", methods=["POST"])
def logout():
    check_csrf()
    session.clear()
    return redirect("/")