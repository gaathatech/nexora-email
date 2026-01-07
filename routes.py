from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from extensions import db
from models import *
from email_service import send_campaign_email
from sqlalchemy import text
import random

main_routes = Blueprint("main", __name__)

@main_routes.route("/")
def dashboard():
    sent = SendLog.query.filter_by(status="SENT").count()
    opens = OpenLog.query.count()
    clicks = ClickLog.query.count()
    failed = SendLog.query.filter_by(status="FAILED").count()

    return render_template(
        "dashboard.html",
        sent=sent,
        opens=opens,
        clicks=clicks,
        failed=failed,
        campaigns=Campaign.query.all()
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

@main_routes.route("/campaign/new", methods=["GET", "POST"])
def new_campaign():
    if request.method == "POST":
        c = Campaign(
            subject=request.form["subject"],
            body_html=request.form["body"],
            variant=request.form.get("variant", "A")
        )
        db.session.add(c)
        db.session.commit()
        return redirect(url_for("main.dashboard"))

    return render_template("campaign_create.html")

@main_routes.route("/campaign/send/<int:id>")
def send_campaign(id):
    campaign = Campaign.query.get_or_404(id)
    contacts = Contact.query.filter_by(subscribed=True).all()
    emails = [c.email for c in contacts]

    sent, failed = send_campaign_email(
        campaign.subject,
        campaign.body_html,
        emails,
        campaign_id=campaign.id
    )

    flash(f"Sent {sent}, Failed {len(failed)}", "success")
    return redirect(url_for("main.dashboard"))

@main_routes.route("/track/open/<int:cid>/<path:email>")
def track_open(cid, email):
    db.session.add(OpenLog(campaign_id=cid, recipient=email))
    db.session.commit()
    return send_file("static/pixel.png", mimetype="image/png")

@main_routes.route("/track/click")
def track_click():
    cid = request.args.get("cid")
    email = request.args.get("email")
    url = request.args.get("url")

    db.session.add(ClickLog(campaign_id=cid, recipient=email, url=url))
    db.session.commit()
    return redirect(url)

@main_routes.route("/analytics")
def analytics():
    data = db.session.execute(text("""
        SELECT campaign_id,
        COUNT(DISTINCT recipient) AS sent,
        (SELECT COUNT(*) FROM open_log WHERE open_log.campaign_id = send_log.campaign_id) AS opens,
        (SELECT COUNT(*) FROM click_log WHERE click_log.campaign_id = send_log.campaign_id) AS clicks
        FROM send_log
        GROUP BY campaign_id
    """)).fetchall()

    return render_template("analytics.html", data=data)
