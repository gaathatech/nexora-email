import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from extensions import db, socketio
from models import SendLog, SmtpAccount, Campaign
from datetime import datetime, date
from sqlalchemy import and_, or_

def get_available_account():
    """Get the next available SMTP account that hasn't hit daily limit"""
    today = date.today()
    account = SmtpAccount.query.filter(
        and_(
            SmtpAccount.is_active == True,
            SmtpAccount.daily_limit > db.func.coalesce(
                db.session.query(db.func.count(SendLog.id)).filter(
                    and_(
                        SendLog.sender == SmtpAccount.email,
                        SendLog.status == "sent",
                        db.func.date(SendLog.timestamp) == today
                    )
                ).correlate(SmtpAccount).scalar_subquery(),
                0
            )
        )
    ).order_by(SmtpAccount.last_used).first()
    return account

def send_campaign_email(subject, html_body, recipients, campaign_id=None):
    """
    Send campaign emails with per-account daily limits and resume capability.
    
    Args:
        subject: Email subject
        html_body: Email body in HTML format
        recipients: List of recipient emails
        campaign_id: Optional campaign ID for tracking
    
    Returns:
        (sent_count, failures, pending_count)
    """
    sent_count = 0
    failures = []
    pending_count = 0
    
    # Remove duplicates while preserving list
    recipients = list(dict.fromkeys(recipients))
    
    for recipient in recipients:
        # Find available account (respects per-account daily limits)
        account = get_available_account()
        
        if not account:
            # No account available - mark as pending for later
            if campaign_id:
                log = SendLog.query.filter_by(
                    campaign_id=campaign_id,
                    recipient=recipient,
                    status="pending"
                ).first()
                if not log:
                    db.session.add(SendLog(
                        campaign_id=campaign_id,
                        recipient=recipient,
                        sender="pending",
                        status="pending"
                    ))
            pending_count += 1
            continue
        
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = account.email
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(html_body, "html"))

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            # Remove spaces from app passwords (they're stored with spaces for readability)
            pwd = account.password.replace(" ", "")
            server.login(account.email, pwd)
            server.sendmail(account.email, recipient, msg.as_string())
            server.quit()

            # Log successful send
            log = SendLog(
                campaign_id=campaign_id,
                recipient=recipient,
                sender=account.email,
                status="sent",
                timestamp=datetime.utcnow()
            )
            db.session.add(log)
            
            # Update account last_used
            account.last_used = datetime.utcnow()
            
            sent_count += 1
            time.sleep(4)  # Rate limiting

        except Exception as e:
            error_msg = str(e)
            failures.append(error_msg)
            
            # Log failed send
            log = SendLog(
                campaign_id=campaign_id,
                recipient=recipient,
                sender=account.email if account else "unknown",
                status="failed",
                error=error_msg,
                timestamp=datetime.utcnow()
            )
            db.session.add(log)

        db.session.commit()

        # emit realtime update for UI
        try:
            if campaign_id and 'log' in locals():
                payload = {
                    'campaign_id': campaign_id,
                    'recipient': log.recipient,
                    'sender': log.sender,
                    'status': log.status,
                    'timestamp': log.timestamp.isoformat() if getattr(log, 'timestamp', None) else datetime.utcnow().isoformat()
                }
                socketio.emit('send_update', payload, namespace='/')
        except Exception:
            pass

    # Update campaign status
    if campaign_id:
        campaign = Campaign.query.get(campaign_id)
        if campaign:
            campaign.sent_count = sent_count
            campaign.failed_count = len(failures)
            if pending_count == 0 and sent_count > 0:
                campaign.status = "sent"
                campaign.completed_at = datetime.utcnow()
            elif pending_count > 0:
                campaign.status = "pending"
            db.session.commit()

    if sent_count > 0 or failures:
        send_report(sent_count, failures, pending_count)
    
    return sent_count, failures, pending_count

def resume_pending_campaign(campaign_id):
    """Resume a paused or pending campaign"""
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return 0, []
    
    # Get all pending emails for this campaign
    pending_logs = SendLog.query.filter_by(
        campaign_id=campaign_id,
        status="pending"
    ).all()
    
    recipients = [log.recipient for log in pending_logs]
    
    if not recipients:
        campaign.status = "sent"
        db.session.commit()
        return 0, []
    
    sent_count, failures, pending = send_campaign_email(
        campaign.subject,
        campaign.body_html,
        recipients,
        campaign_id=campaign_id
    )
    
    return sent_count, failures

def resend_failed(limit=20):
    """Retry failed emails (max 3 retries per email)"""
    failed_logs = SendLog.query.filter(
        and_(
            SendLog.status == "failed",
            SendLog.retry_count < 3
        )
    ).limit(limit).all()

    sent_count = 0
    for log in failed_logs:
        try:
            account = get_available_account()
            if not account:
                break
            
            msg = MIMEMultipart("alternative")
            msg["From"] = account.email
            msg["To"] = log.recipient
            msg["Subject"] = "[RETRY] " + ("Subject" if log.campaign_id else "Email")
            msg.attach(MIMEText("<p>Retry email delivery</p>", "html"))

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(account.email, account.password)
            server.sendmail(account.email, log.recipient, msg.as_string())
            server.quit()
            
            log.status = "sent"
            log.sender = account.email
            log.retry_count += 1
            sent_count += 1
            time.sleep(4)
            
        except Exception as e:
            log.retry_count += 1
            log.error = str(e)

    db.session.commit()
    return sent_count

def send_report(sent, failures, pending=0):
    """Send campaign report to configured email"""
    cfg = current_app.config
    if not cfg.get("REPORT_EMAIL"):
        return

    failure_text = "\n".join(failures[:10]) if failures else "None"
    
    body = f"""📊 EMAIL CAMPAIGN REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Successfully Sent: {sent}
❌ Failed: {len(failures)}
⏳ Pending (waiting for account capacity): {pending}

RECENT ERRORS (first 10):
{failure_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
"""

    try:
        accounts = SmtpAccount.query.filter_by(is_active=True).first()
        if not accounts:
            return
        
        msg = MIMEText(body)
        msg["Subject"] = "📊 Email Campaign Report"
        msg["From"] = accounts.email
        msg["To"] = cfg["REPORT_EMAIL"]

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(accounts.email, accounts.password)
        server.sendmail(accounts.email, cfg["REPORT_EMAIL"], msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send report: {e}")

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

