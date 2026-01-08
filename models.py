from extensions import db
from datetime import datetime, date

# Association table for Contact to ContactGroup many-to-many relationship
contact_group_association = db.Table(
    'contact_group_association',
    db.Column('contact_id', db.Integer, db.ForeignKey('contact.id'), primary_key=True),
    db.Column('contact_group_id', db.Integer, db.ForeignKey('contact_group.id'), primary_key=True)
)

class SmtpAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    daily_limit = db.Column(db.Integer, default=100)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, nullable=True)
    
    def get_today_sent_count(self):
        """Get emails sent today from this account"""
        from sqlalchemy import and_
        today = date.today()
        return SendLog.query.filter(
            and_(
                SendLog.sender == self.email,
                SendLog.status == "sent",
                db.func.date(SendLog.timestamp) == today
            )
        ).count()
    
    def can_send(self):
        """Check if account can send more emails today"""
        return self.is_active and self.get_today_sent_count() < self.daily_limit

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    subscribed = db.Column(db.Boolean, default=True)
    whatsapp = db.Column(db.String(20), nullable=True)
    groups = db.relationship('ContactGroup', secondary=contact_group_association, backref='contacts')

class ContactGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def contact_count(self):
        return len(self.contacts)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255))
    body_html = db.Column(db.Text)
    variant = db.Column(db.String(1), default="A")  # A or B
    status = db.Column(db.String(20), default="draft")  # draft, pending, paused, sent
    group_id = db.Column(db.Integer, db.ForeignKey('contact_group.id'), nullable=True)
    group = db.relationship('ContactGroup')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    total_recipients = db.Column(db.Integer, default=0)
    sent_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)

class SendLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    sender = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="pending")  # pending, sent, failed, bounced
    error = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    retry_count = db.Column(db.Integer, default=0)

class OpenLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    user_agent = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    device_type = db.Column(db.String(50), nullable=True)  # mobile, desktop, tablet
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)

class ClickLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    url = db.Column(db.Text, nullable=False)
    link_text = db.Column(db.String(255), nullable=True)  # Button text or link label
    click_type = db.Column(db.String(50), default="link")  # link, button, image
    user_agent = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)
    