from flask import Blueprint,render_template, request, redirect, flash
from flask_login import login_user, logout_user
from models.user import User
from extensions import db,bcrypt

auth = Blueprint("auth",__name__)

@auth.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username=request.form.get("username")
        email=request.form.get("email")
        password=request.form.get("password")

        existing_user=User.query.filter_by(email=email).first()

        if existing_user:
            flash("An account with this email already exists.", "danger")
            return redirect("/signup")
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully! Please log in.", "success")
        return redirect("/login")

    return render_template("signup.html")

@auth.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Welcome back !", "success")
            return redirect("/dashboard")
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@auth.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.","success")
    return redirect("/")