"""Authentication blueprint routes.

This module contains routes for user registration, login, and logout
for the Writing Contest Web App.

Blueprints:
    auth_bp (Blueprint): Handles authentication-related routes.
"""

from flask import (Blueprint, render_template, request, session, flash,
                   redirect, url_for)

import users
from utils import check_csrf, sanitize_input, is_valid_email

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register")
def register():
    """Renders the user registration page."""
    return render_template("register.html")


@auth_bp.route("/create", methods=["POST"])
def create():
    """Handles the user registration form submission."""
    check_csrf()
    name = sanitize_input(request.form.get("name", ""))
    username = sanitize_input(request.form.get("username", ""))
    password = request.form.get("password1", "")
    password2 = request.form.get("password2", "")

    errors = []
    if not name or len(name) > 50:
        errors.append("Nimi on pakollinen ja saa olla enintään 50 merkkiä.")
    if not username or len(username) > 50:
        errors.append(
            "Sähköposti on pakollinen ja saa olla enintään 50 merkkiä.")
    elif not is_valid_email(username):
        errors.append("Sähköpostiosoite ei ole kelvollinen.")

    if len(password) < 8 or len(password) > 50:
        errors.append(
            "Salasanan on oltava vähintään 8 ja enintään 50 merkkiä pitkä.")
    if password != password2:
        errors.append("Salasanat eivät ole samat.")

    if errors:
        session["form_data"] = {"name": name, "username": username}
        for error in errors:
            flash(error)
        return redirect(url_for("auth.register"))

    user_count = users.get_user_count()
    is_super = 1 if user_count == 0 else 0

    success = users.create_user(name, username, password, is_super)
    if not success:
        session["form_data"] = {"name": name, "username": username}
        flash("Virhe: tunnus on jo varattu.")
        return redirect(url_for("auth.register"))

    session["form_data"] = {"username": username}
    if is_super:
        flash("Pääkäyttäjän tunnus on luotu. Tällä tunnuksella on täydet "
              "käyttöoikeudet.")
    else:
        flash("Tunnus on luotu.")

    return redirect(url_for("auth.login", next_page="/"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login for both GET and POST requests."""
    if request.method == "GET":
        username = session.pop("form_data", {}).get("username", "")
        next_page = request.args.get("next_page", "/")
        session["next_page"] = next_page
        return render_template("login.html", username=username)

    check_csrf()
    username = sanitize_input(request.form["username"])
    password = request.form["password"]
    user_id = users.check_login(username, password)

    if not user_id:
        flash("Virheellinen käyttäjätunnus tai salasana.")
        session["form_data"] = {"username": username}
        return redirect(url_for("auth.login"))

    user = users.get_user(user_id)
    if not user:
        # This case is unlikely if check_login succeeds, but good for robustness
        flash("Virheellinen käyttäjätunnus tai salasana.")
        session["form_data"] = {"username": username}
        return redirect(url_for("auth.login"))

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["super_user"] = user["super_user"]
    session.pop("form_data", None)
    next_page = session.pop("next_page", "/")
    return redirect(next_page)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Logs the current user out by clearing the session."""
    check_csrf()
    session.clear()
    return redirect("/")


@auth_bp.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    """Renders the profile edit page and handles profile updates."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = users.get_user(session["user_id"])
    if not user:
        flash("Käyttäjää ei löytynyt.")
        return redirect("/")
    if request.method == "POST":
        check_csrf()
        name = sanitize_input(request.form["name"])
        password1 = request.form.get("password1", "")
        password2 = request.form.get("password2", "")
        errors = []
        if not name or len(name) > 50:
            errors.append("Nimi ei saa olla tyhjä tai liian pitkä.")
        if password1 or password2:
            if password1 != password2:
                errors.append("Salasanat eivät täsmää.")
            elif len(password1) < 8:
                errors.append("Salasanan on oltava vähintään 8 merkkiä pitkä.")
        if errors:
            for error in errors:
                flash(error)
            return render_template("edit_profile.html", user=user)
        users.update_user_name(user["id"], name)
        if password1:
            users.update_user_password(user["id"], password1)
        flash("Profiili päivitetty.")
        return redirect(url_for("auth.edit_profile"))
    return render_template("edit_profile.html", user=user)


@auth_bp.route("/profile/delete", methods=["POST"])
def delete_profile():
    """Handles the permanent deletion of the current user's profile."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    check_csrf()
    users.delete_user(session["user_id"])
    session.clear()
    flash("Profiili poistettu pysyvästi.")
    return redirect("/")
