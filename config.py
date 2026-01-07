import os

class Config:
    SECRET_KEY = "email-blast-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///email_marketing.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_EMAIL = "nexora.aidni@gmail.com"
    SMTP_PASSWORD = "mqas lqbv khyv dfzm"
