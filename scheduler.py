import time
from app import create_app
from models import Campaign
from email_service import send_campaign_email
from extensions import db

app = create_app()

with app.app_context():
    while True:
        campaign = Campaign.query.filter_by(status="draft").first()
        if campaign:
            emails = [c.email for c in campaign.contacts]
            sent, _ = send_campaign_email(
                campaign.subject,
                campaign.body_html,
                emails
            )
            campaign.status = "sent"
            campaign.sent_count = sent
            db.session.commit()

        time.sleep(86400)  # run once per day
