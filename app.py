from flask import Flask
from config import get_config
from extensions import db, socketio
from routes import main_routes
import json
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())

    db.init_app(app)
    if socketio:
        socketio.init_app(app, cors_allowed_origins='*')
    app.register_blueprint(main_routes)

    with app.app_context():
        db.create_all()
        
        # Auto-load SMTP accounts from .env to database
        _load_smtp_accounts_from_env()

    return app

def _load_smtp_accounts_from_env():
    """Load SMTP accounts from SMTP_ACCOUNTS_JSON in .env to database"""
    from models import SmtpAccount
    
    try:
        accounts_json = os.getenv("SMTP_ACCOUNTS_JSON", "[]")
        accounts_data = json.loads(accounts_json)
        
        if not accounts_data:
            print("⚠️  No SMTP accounts in SMTP_ACCOUNTS_JSON")
            return
        
        # Check how many are already in DB
        existing = SmtpAccount.query.filter(
            SmtpAccount.email.in_([a.get("email") for a in accounts_data])
        ).count()
        
        if existing >= len(accounts_data):
            print(f"✅ All {len(accounts_data)} SMTP accounts already loaded")
            return
        
        # Add missing accounts
        for acc_data in accounts_data:
            email = acc_data.get("email")
            password = acc_data.get("password")
            
            if not email or not password:
                continue
            
            # Check if already exists
            existing_acc = SmtpAccount.query.filter_by(email=email).first()
            if not existing_acc:
                new_acc = SmtpAccount(
                    email=email,
                    password=password,
                    daily_limit=100,
                    is_active=True
                )
                db.session.add(new_acc)
        
        db.session.commit()
        
        # Show loaded accounts
        all_accs = SmtpAccount.query.all()
        print(f"✅ Loaded {len(all_accs)} SMTP accounts:")
        for acc in all_accs:
            print(f"  - {acc.email} (active={acc.is_active}, limit={acc.daily_limit})")
    
    except Exception as e:
        print(f"⚠️  Failed to load SMTP accounts: {e}")

app = create_app()

if __name__ == "__main__":
    socketio.run(app, debug=True)
