import os
from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY environment variable is not configured.")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (
        os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    )

    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = URL.create(
            drivername="mysql+pymysql",
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", "3306")),
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }