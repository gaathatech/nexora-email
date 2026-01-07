from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import text

from extensions import db
from models import Contact, Campaign, SendLog
from email_service import send_campaign_email, resend_failed

main_routes = Blueprint("main", __name__)

# ---------------- DASHBOARD ----------------

@main_routes.route("/", strict_slashes=False)
def dashboard():
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    contacts_count = Contact.query.count()
    return render_template(
        "dashboard.html",
        campaigns=campaigns,
        contacts_count=contacts_count
    )

# ---------------- CONTACTS ----------------

@main_routes.route("/contacts", methods=["GET", "POST"])
def contacts():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if email and not Contact.query.filter_by(email=email).first():
            db.session.add(Contact(email=email))
            db.session.commit()
            flash("Contact added", "success")
        else:
            flash("Duplicate or invalid email", "warning")

    contacts = Contact.query.order_by(Contact.id.desc()).all()
    return render_template("contacts.html", contacts=contacts)

# -------- BULK PASTE EMAILS (LINE BY LINE) --------

@main_routes.route("/contacts/bulk", methods=["POST"])
def bulk_contacts():
    raw = request.form.get("emails", "")

    raw = raw.replace(",", "\n")
    emails = [e.strip().lower() for e in raw.splitlines() if "@" in e]

    added = 0
    skipped = 0

    for email in emails:
        if Contact.query.filter_by(email=email).first():
            skipped += 1
            continue
        db.session.add(Contact(email=email))
        added += 1

    db.session.commit()
    flash(f"{added} added, {skipped} skipped", "success")
    return redirect(url_for("main.contacts"))

# ---------------- CSV IMPORT ----------------

@main_routes.route("/contacts/import", methods=["POST"])
def import_contacts():
    file = request.files.get("csv")
    if not file:
        flash("No CSV uploaded", "danger")
        return redirect(url_for("main.contacts"))

    count = 0
    for line in file.read().decode("utf-8").splitlines():
        email = line.strip().lower()
        if "@" not in email:
            continue
        if Contact.query.filter_by(email=email).first():
            continue
        db.session.add(Contact(email=email))
        count += 1

    db.session.commit()
    flash(f"{count} contacts imported", "success")
    return redirect(url_for("main.contacts"))

# ---------------- CAMPAIGNS ----------------

@main_routes.route("/campaign/new", methods=["GET", "POST"])
def new_campaign():
    if request.method == "POST":
        subject = request.form.get("subject")
        body = request.form.get("body")

        campaign = Campaign(
            subject=subject,
            body_html=body
        )
        db.session.add(campaign)
        db.session.commit()

        flash("Campaign created", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("campaign_create.html")

@main_routes.route("/campaign/send/<int:id>")
def send_campaign(id):
    campaign = Campaign.query.get_or_404(id)
    contacts = Contact.query.all()

    emails = [c.email for c in contacts]

    sent, failed = send_campaign_email(
        campaign.subject,
        campaign.body_html,
        emails
    )

    campaign.status = "sent"
    campaign.sent_count = sent
    db.session.commit()

    flash(f"Campaign sent: {sent} sent, {len(failed)} failed", "success")
    return redirect(url_for("main.dashboard"))

# ---------------- ANALYTICS ----------------

@main_routes.route("/analytics")
def analytics():
    total_sent = SendLog.query.filter_by(status="SENT").count()
    total_failed = SendLog.query.filter_by(status="FAILED").count()

    per_sender = db.session.execute(
        text("""
            SELECT sender, COUNT(*) AS total
            FROM send_log
            GROUP BY sender
        """)
    ).fetchall()

    return render_template(
        "analytics.html",
        total_sent=total_sent,
        total_failed=total_failed,
        per_sender=per_sender
    )

# ---------------- RESUME FAILED ----------------

@main_routes.route("/campaign/resume")
def resume_failed():
    resend_failed()
    flash("Retry attempted for failed emails", "info")
    return redirect(url_for("main.analytics"))

