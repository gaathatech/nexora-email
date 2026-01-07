import os
import json
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    SQLALCHEMY_DATABASE_URI = "sqlite:///email_marketing.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

    DAILY_EMAIL_LIMIT = int(os.getenv("DAILY_EMAIL_LIMIT", 100))
    REPORT_EMAIL = os.getenv("REPORT_EMAIL")

    try:
        SMTP_ACCOUNTS = json.loads(os.getenv("SMTP_ACCOUNTS_JSON", "[]"))
        if not isinstance(SMTP_ACCOUNTS, list):
            raise ValueError("SMTP_ACCOUNTS_JSON must be a list")
    except Exception as e:
        print("❌ ERROR parsing SMTP_ACCOUNTS_JSON:", e)
        SMTP_ACCOUNTS = []

def get_config():
    return Config
