from flask import Flask,render_template
from config import Config
from extensions import db, bcrypt
from login_manager import login_manager
from routes.auth import auth
from flask_login import login_required

app=Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

app.register_blueprint(auth)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

if __name__=="__main__":
    app.run(debug=True)