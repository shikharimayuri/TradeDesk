import re

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_user, logout_user

from models.user import User
from extensions import db, bcrypt, limiter

auth = Blueprint("auth", __name__)


@auth.route("/signup", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def signup():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        # Validate username
        if not username or len(username) > 100:
            flash(
                "Username is required and must be at most 100 characters.",
                "danger",
            )
            return redirect(url_for("auth.signup"))

        # Validate email
        if (
            len(email) > 255
            or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)
        ):
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for("auth.signup"))

        # Validate password
        if len(password) < 12:
            flash(
                "Password must contain at least 12 characters.",
                "danger",
            )
            return redirect(url_for("auth.signup"))

        # Bcrypt supports passwords up to 72 bytes
        if len(password.encode("utf-8")) > 72:
            flash(
                "Password is too long. Please use at most 72 UTF-8 bytes.",
                "danger",
            )
            return redirect(url_for("auth.signup"))

        # Check for an existing email
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash(
                "An account with this email already exists.",
                "danger",
            )
            return redirect(url_for("auth.signup"))

        # Hash the password before storing it
        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
        )

        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "Unable to create your account. Please try again.",
                "danger",
            )
            return redirect(url_for("auth.signup"))

        flash(
            "Account created successfully! Please log in.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template("signup.html")


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@auth.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))