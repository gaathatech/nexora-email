from extensions import db
from datetime import datetime

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    subscribed = db.Column(db.Boolean, default=True)
    whatsapp = db.Column(db.String(20), nullable=True)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255))
    body_html = db.Column(db.Text)
    variant = db.Column(db.String(1), default="A")  # A or B
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SendLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer)
    recipient = db.Column(db.String(255))
    sender = db.Column(db.String(255))
    status = db.Column(db.String(50))
    error = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class OpenLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer)
    recipient = db.Column(db.String(255))
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)

class ClickLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer)
    recipient = db.Column(db.String(255))
    url = db.Column(db.Text)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)
    