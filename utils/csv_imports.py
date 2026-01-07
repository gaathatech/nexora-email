import csv
from models import Contact
from extensions import db

def import_contacts_from_csv(file_path):
    added = 0
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            email = row.get("email")
            if not email:
                continue

            if not Contact.query.filter_by(email=email).first():
                db.session.add(Contact(email=email))
                added += 1

    db.session.commit()
    return added
