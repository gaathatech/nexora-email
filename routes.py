from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Contact, Campaign
from email_service import send_campaign_email

main_routes = Blueprint("main", __name__)

@main_routes.route("/", strict_slashes=False)
def dashboard():
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    contacts_count = Contact.query.count()
    return render_template("dashboard.html", campaigns=campaigns, contacts_count=contacts_count)

@main_routes.route("/contacts", methods=["GET", "POST"])
def contacts():
    if request.method == "POST":
        email = request.form["email"]
        name = request.form.get("name")

        if not Contact.query.filter_by(email=email).first():
            db.session.add(Contact(email=email, name=name))
            db.session.commit()
            flash("Contact added", "success")

    contacts = Contact.query.all()
    return render_template("contacts.html", contacts=contacts)

@main_routes.route("/campaign/new", methods=["GET", "POST"])
def new_campaign():
    if request.method == "POST":
        campaign = Campaign(
            subject=request.form["subject"],
            body_html=request.form["body"]
        )
        db.session.add(campaign)
        db.session.commit()
        return redirect(url_for("main.dashboard"))

    return render_template("campaign_create.html")

@main_routes.route("/campaign/send/<int:id>")
def send_campaign(id):
    campaign = Campaign.query.get_or_404(id)
    contacts = Contact.query.filter_by(subscribed=True).all()

    emails = [c.email for c in contacts]
    sent = send_campaign_email(campaign.subject, campaign.body_html, emails)

    campaign.status = "sent"
    campaign.sent_count = sent
    db.session.commit()

    flash(f"Campaign sent to {sent} contacts", "success")
    return redirect(url_for("main.dashboard"))
