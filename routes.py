from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from extensions import db
from models import *
from email_service import send_campaign_email, resume_pending_campaign, resend_failed
from utils.reporting import get_campaign_report, get_account_performance, generate_html_report
from sqlalchemy import text, and_
from datetime import date

main_routes = Blueprint("main", __name__)

@main_routes.route("/")
def dashboard():
    sent = SendLog.query.filter_by(status="sent").count()
    opens = OpenLog.query.count()
    clicks = ClickLog.query.count()
    failed = SendLog.query.filter_by(status="failed").count()
    pending = SendLog.query.filter_by(status="pending").count()
    
    # Get SMTP account stats
    accounts = SmtpAccount.query.filter_by(is_active=True).all()
    account_stats = []
    today = date.today()
    
    for acc in accounts:
        sent_today = SendLog.query.filter(
            and_(
                SendLog.sender == acc.email,
                SendLog.status == "sent",
                db.func.date(SendLog.timestamp) == today
            )
        ).count()
        account_stats.append({
            'email': acc.email,
            'sent_today': sent_today,
            'daily_limit': acc.daily_limit,
            'remaining': acc.daily_limit - sent_today
        })

    return render_template(
        "dashboard.html",
        sent=sent,
        opens=opens,
        clicks=clicks,
        failed=failed,
        pending=pending,
        campaigns=Campaign.query.all(),
        account_stats=account_stats
    )

@main_routes.route("/contacts", methods=["GET", "POST"])
def contacts():
    if request.method == "POST":
        raw = request.form.get("emails", "")
        whatsapp = request.form.get("whatsapp")

        raw = raw.replace(",", "\n")
        emails = [e.strip() for e in raw.splitlines() if "@" in e]

        added = 0
        for email in emails:
            if not Contact.query.filter_by(email=email).first():
                db.session.add(Contact(email=email, whatsapp=whatsapp))
                added += 1
        db.session.commit()
        flash(f"{added} contacts added", "success")

    return render_template("contacts.html", contacts=Contact.query.all())

@main_routes.route("/groups", methods=["GET", "POST"])
def manage_groups():
    """Manage contact groups"""
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description", "")
        
        if ContactGroup.query.filter_by(name=name).first():
            flash("Group name already exists", "warning")
        else:
            group = ContactGroup(name=name, description=description)
            db.session.add(group)
            db.session.commit()
            flash(f"Group '{name}' created", "success")
    
    groups = ContactGroup.query.all()
    return render_template("groups.html", groups=groups)

@main_routes.route("/group/<int:id>")
def group_detail(id):
    """View group details and manage contacts"""
    group = ContactGroup.query.get_or_404(id)
    return render_template("group_detail.html", group=group)

@main_routes.route("/group/<int:id>/add-contacts", methods=["POST"])
def add_contacts_to_group(id):
    """Add contacts to a group via CSV/paste"""
    group = ContactGroup.query.get_or_404(id)
    raw = request.form.get("emails", "")
    
    raw = raw.replace(",", "\n")
    emails = [e.strip() for e in raw.splitlines() if "@" in e and e.strip()]
    
    added = 0
    for email in emails:
        contact = Contact.query.filter_by(email=email).first()
        if not contact:
            contact = Contact(email=email)
            db.session.add(contact)
            db.session.flush()
        
        if contact not in group.contacts:
            group.contacts.append(contact)
            added += 1
    
    db.session.commit()
    flash(f"{added} contacts added to group '{group.name}'", "success")
    return redirect(url_for("main.group_detail", id=id))

@main_routes.route("/group/<int:id>/remove-contact/<int:contact_id>")
def remove_contact_from_group(id, contact_id):
    """Remove a contact from a group"""
    group = ContactGroup.query.get_or_404(id)
    contact = Contact.query.get_or_404(contact_id)
    
    if contact in group.contacts:
        group.contacts.remove(contact)
        db.session.commit()
        flash(f"Contact {contact.email} removed from group", "success")
    
    return redirect(url_for("main.group_detail", id=id))

@main_routes.route("/group/<int:id>/delete")
def delete_group(id):
    """Delete a group"""
    group = ContactGroup.query.get_or_404(id)
    group_name = group.name
    db.session.delete(group)
    db.session.commit()
    flash(f"Group '{group_name}' deleted", "success")
    return redirect(url_for("main.manage_groups"))

@main_routes.route("/campaign/new", methods=["GET", "POST"])
def new_campaign():
    if request.method == "POST":
        group_id = request.form.get("group_id")
        c = Campaign(
            subject=request.form["subject"],
            body_html=request.form["body"],
            variant=request.form.get("variant", "A"),
            group_id=int(group_id) if group_id else None
        )
        db.session.add(c)
        db.session.commit()
        return redirect(url_for("main.dashboard"))

    groups = ContactGroup.query.all()
    return render_template("campaign_create.html", groups=groups)

@main_routes.route("/campaign/send/<int:id>")
def send_campaign(id):
    campaign = Campaign.query.get_or_404(id)
    
    # Get contacts from selected group or all subscribed contacts
    if campaign.group_id:
        group = ContactGroup.query.get(campaign.group_id)
        if not group:
            flash("Group not found", "error")
            return redirect(url_for("main.dashboard"))
        contacts = [c for c in group.contacts if c.subscribed]
        group_name = f" in group '{group.name}'"
    else:
        contacts = Contact.query.filter_by(subscribed=True).all()
        group_name = " (all contacts)"
    
    emails = [c.email for c in contacts]
    
    if not emails:
        flash(f"No subscribed contacts{group_name} to send to", "warning")
        return redirect(url_for("main.dashboard"))
    
    campaign.total_recipients = len(emails)
    campaign.status = "pending"
    campaign.started_at = db.func.now()
    db.session.commit()

    sent, failed, pending = send_campaign_email(
        campaign.subject,
        campaign.body_html,
        emails,
        campaign_id=campaign.id
    )

    msg = f"✅ Sent: {sent} | ❌ Failed: {len(failed)} | ⏳ Pending: {pending}{group_name}"
    flash(msg, "success")
    return redirect(url_for("main.dashboard"))

@main_routes.route("/track/open/<int:cid>/<path:email>")
def track_open(cid, email):
    from flask import request
    
    # Extract device type from user agent
    user_agent = request.headers.get('User-Agent', '')
    device_type = 'mobile' if any(x in user_agent.lower() for x in ['mobile', 'android', 'iphone']) else 'desktop'
    
    log = OpenLog(
        campaign_id=cid,
        recipient=email,
        user_agent=user_agent,
        ip_address=request.remote_addr,
        device_type=device_type
    )
    db.session.add(log)
    db.session.commit()
    
    # Return invisible tracking pixel
    return send_file("static/pixel.png", mimetype="image/png")

@main_routes.route("/track/click")
def track_click():
    from flask import request
    
    cid = request.args.get("cid")
    email = request.args.get("email")
    url = request.args.get("url")
    link_text = request.args.get("text", "")
    click_type = request.args.get("type", "link")  # link or button
    
    user_agent = request.headers.get('User-Agent', '')
    
    log = ClickLog(
        campaign_id=cid,
        recipient=email,
        url=url,
        link_text=link_text,
        click_type=click_type,
        user_agent=user_agent,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    # Redirect to actual URL
    return redirect(url)

@main_routes.route("/campaign/resume/<int:id>")
def resume_campaign(id):
    """Resume a pending or paused campaign"""
    campaign = Campaign.query.get_or_404(id)
    
    if campaign.status not in ["pending", "paused"]:
        flash("Campaign is not pending or paused", "warning")
        return redirect(url_for("main.dashboard"))
    
    sent, failed = resume_pending_campaign(id)
    flash(f"Resumed: {sent} sent, {len(failed)} failed", "success")
    return redirect(url_for("main.dashboard"))

@main_routes.route("/campaign/pause/<int:id>")
def pause_campaign(id):
    """Pause a campaign"""
    campaign = Campaign.query.get_or_404(id)
    campaign.status = "paused"
    db.session.commit()
    flash("Campaign paused", "success")
    return redirect(url_for("main.dashboard"))

@main_routes.route("/campaign/retry-failed")
def retry_failed_emails():
    """Retry up to 20 failed emails"""
    sent = resend_failed(limit=20)
    flash(f"Retried {sent} failed emails", "success")
    return redirect(url_for("main.dashboard"))

@main_routes.route("/accounts", methods=["GET", "POST"])
def manage_accounts():
    """Manage SMTP accounts"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        daily_limit = int(request.form.get("daily_limit", 100))
        
        # Check for duplicates
        if SmtpAccount.query.filter_by(email=email).first():
            flash("Email account already exists", "warning")
        else:
            acc = SmtpAccount(email=email, password=password, daily_limit=daily_limit)
            db.session.add(acc)
            db.session.commit()
            flash(f"Account {email} added", "success")
    
    accounts = SmtpAccount.query.all()
    return render_template("accounts.html", accounts=accounts)

@main_routes.route("/account/delete/<int:id>")
def delete_account(id):
    """Delete an SMTP account"""
    acc = SmtpAccount.query.get_or_404(id)
    db.session.delete(acc)
    db.session.commit()
    flash(f"Account {acc.email} deleted", "success")
    return redirect(url_for("main.manage_accounts"))

@main_routes.route("/account/toggle/<int:id>")
def toggle_account(id):
    """Enable/Disable an SMTP account"""
    acc = SmtpAccount.query.get_or_404(id)
    acc.is_active = not acc.is_active
    db.session.commit()
    status = "enabled" if acc.is_active else "disabled"
    flash(f"Account {acc.email} {status}", "success")
    return redirect(url_for("main.manage_accounts"))

@main_routes.route("/analytics")
def analytics():
    campaigns = Campaign.query.all()
    
    analytics_data = []
    for campaign in campaigns:
        sent_count = SendLog.query.filter_by(
            campaign_id=campaign.id,
            status="sent"
        ).count()
        
        open_count = OpenLog.query.filter_by(campaign_id=campaign.id).count()
        click_count = ClickLog.query.filter_by(campaign_id=campaign.id).count()
        unique_clicks = db.session.query(ClickLog.recipient).filter_by(
            campaign_id=campaign.id
        ).distinct().count()
        
        # Get top performing links
        top_links = db.session.query(
            ClickLog.url,
            ClickLog.link_text,
            db.func.count(ClickLog.id).label('count')
        ).filter_by(campaign_id=campaign.id).group_by(
            ClickLog.url, ClickLog.link_text
        ).order_by(db.desc(db.func.count(ClickLog.id))).limit(5).all()
        
        open_rate = (open_count / sent_count * 100) if sent_count > 0 else 0
        click_rate = (click_count / sent_count * 100) if sent_count > 0 else 0
        
        analytics_data.append({
            'campaign': campaign,
            'sent': sent_count,
            'opens': open_count,
            'clicks': click_count,
            'unique_clicks': unique_clicks,
            'open_rate': f"{open_rate:.1f}%",
            'click_rate': f"{click_rate:.1f}%",
            'top_links': top_links
        })

    return render_template("analytics.html", data=analytics_data)

@main_routes.route("/campaign/<int:id>/report")
def campaign_report(id):
    """Detailed campaign report"""
    report = get_campaign_report(id)
    if not report:
        flash("Campaign not found", "error")
        return redirect(url_for("main.analytics"))
    
    return render_template("campaign_report.html", report=report)

@main_routes.route("/campaign/<int:id>/report.html")
def campaign_report_html(id):
    """Download HTML report"""
    html = generate_html_report(id)
    if not html:
        flash("Campaign not found", "error")
        return redirect(url_for("main.analytics"))
    
    return html, 200, {'Content-Type': 'text/html'}

@main_routes.route("/accounts/performance")
def account_performance():
    """Account performance metrics"""
    performance = get_account_performance(days=7)
    return render_template("account_performance.html", performance=performance)

@main_routes.route("/api/campaign/<int:id>/stats")
def api_campaign_stats(id):
    """API endpoint for campaign statistics"""
    report = get_campaign_report(id)
    if not report:
        return jsonify({'error': 'Campaign not found'}), 404
    
    return jsonify({
        'campaign_id': id,
        'sent': report['sent'],
        'opens': report['unique_opens'],
        'clicks': report['unique_clicks'],
        'open_rate': report['unique_open_rate'],
        'click_rate': report['unique_click_rate']
    })


@main_routes.route("/api/campaign/<int:id>/progress")
def api_campaign_progress(id):
    """Return live sending progress for a campaign"""
    campaign = Campaign.query.get(id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404

    total = campaign.total_recipients or 0
    sent = SendLog.query.filter_by(campaign_id=id, status='sent').count()
    failed = SendLog.query.filter_by(campaign_id=id, status='failed').count()
    pending = SendLog.query.filter_by(campaign_id=id, status='pending').count()

    # Per-account usage
    accounts = SmtpAccount.query.filter_by(is_active=True).all()
    today = date.today()
    acc_stats = []
    for acc in accounts:
        sent_today = SendLog.query.filter(
            and_(
                SendLog.sender == acc.email,
                SendLog.status == 'sent',
                db.func.date(SendLog.timestamp) == today
            )
        ).count()
        acc_stats.append({
            'email': acc.email,
            'sent_today': sent_today,
            'daily_limit': acc.daily_limit,
            'remaining': max(acc.daily_limit - sent_today, 0)
        })

    return jsonify({
        'campaign_id': id,
        'subject': campaign.subject,
        'status': campaign.status,
        'total': total,
        'sent': sent,
        'failed': failed,
        'pending': pending,
        'accounts': acc_stats
    })

@main_routes.route('/api/campaign/<int:id>/logs')
def api_campaign_logs(id):
    """Return recent send logs for a campaign"""
    logs = SendLog.query.filter_by(campaign_id=id).order_by(SendLog.timestamp.desc()).limit(200).all()
    out = []
    for l in logs:
        out.append({
            'id': l.id,
            'recipient': l.recipient,
            'sender': l.sender,
            'status': l.status,
            'error': l.error,
            'timestamp': l.timestamp.isoformat() if getattr(l,'timestamp',None) else None,
            'retry_count': getattr(l,'retry_count',0)
        })
    return jsonify(out)