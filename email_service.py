import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from extensions import db
from models import SendLog

def send_campaign_email(subject, html_body, recipients):
    cfg = current_app.config

    sent_count = 0
    failures = []
    account_index = 0

    smtp_accounts = cfg["SMTP_ACCOUNTS"]

    for email in recipients:
        if sent_count >= cfg["DAILY_EMAIL_LIMIT"]:
            break

        account = smtp_accounts[account_index % len(smtp_accounts)]
        account_index += 1

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = account["email"]
            msg["To"] = email
            msg["Subject"] = subject
            msg.attach(MIMEText(html_body, "html"))

            server = smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"])
            server.starttls()
            server.login(account["email"], account["password"])
            server.sendmail(account["email"], email, msg.as_string())
            server.quit()

            db.session.add(SendLog(
                recipient=email,
                sender=account["email"],
                status="SENT"
            ))

            sent_count += 1
            time.sleep(4)

        except Exception as e:
            failures.append(str(e))
            db.session.add(SendLog(
                recipient=email,
                sender=account["email"],
                status="FAILED",
                error=str(e)
            ))

        db.session.commit()

    send_report(cfg, sent_count, failures)
    return sent_count, failures

def resend_failed():
    cfg = current_app.config
    failed_logs = SendLog.query.filter_by(status="FAILED").limit(20).all()

    for log in failed_logs:
        try:
            send_campaign_email(
                "Retry Campaign",
                "<p>This is a retry email</p>",
                [log.recipient]
            )
            log.status = "RETRIED"
        except:
            pass

    db.session.commit()

def send_report(cfg, sent, failures):
    if not cfg["REPORT_EMAIL"]:
        return

    body = f"""
Campaign Report

Total Sent: {sent}
Failures: {len(failures)}

Errors:
{chr(10).join(failures[:5])}
"""

    msg = MIMEText(body)
    msg["Subject"] = "📊 Email Campaign Report"
    msg["From"] = cfg["SMTP_ACCOUNTS"][0]["email"]
    msg["To"] = cfg["REPORT_EMAIL"]

    server = smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"])
    server.starttls()
    server.login(
        cfg["SMTP_ACCOUNTS"][0]["email"],
        cfg["SMTP_ACCOUNTS"][0]["password"]
    )
    server.sendmail(msg["From"], cfg["REPORT_EMAIL"], msg.as_string())
    server.quit()
