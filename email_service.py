import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

def send_campaign_email(subject, html_body, recipients):
    cfg = current_app.config

    server = smtplib.SMTP(cfg["SMTP_SERVER"], cfg["SMTP_PORT"])
    server.starttls()
    server.login(cfg["SMTP_EMAIL"], cfg["SMTP_PASSWORD"])

    sent = 0

    for email in recipients:
        msg = MIMEMultipart("alternative")
        msg["From"] = cfg["SMTP_EMAIL"]
        msg["To"] = email
        msg["Subject"] = subject

        footer = """
        <hr>
        <p style="font-size:12px;color:#777">
        You are receiving this email because you subscribed.<br>
        <a href="#">Unsubscribe</a>
        </p>
        """

        msg.attach(MIMEText(html_body + footer, "html"))
        server.sendmail(cfg["SMTP_EMAIL"], email, msg.as_string())
        sent += 1
        time.sleep(2)  # safe rate limit

    server.quit()
    return sent
