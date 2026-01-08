#!/bin/bash
set -e

echo "🚀 Nexora Email Engine - Setup & Run"
echo "===================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Install it first:"
    echo "   apt install python3 python3-pip"
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet

# Create required directories
echo "📁 Creating directories..."
mkdir -p instance static/uploads

# Initialize database
echo "🗄️  Initializing database..."
python3 << 'EOF'
from app import create_app
from extensions import db

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ Database initialized")
EOF

# Load SMTP accounts from .env
echo ""
echo "📧 Loading SMTP accounts from .env..."
python3 << 'EOF'
from app import create_app
from models import SmtpAccount
from config import Config

app = create_app()
with app.app_context():
    # Check if accounts exist
    count = SmtpAccount.query.count()
    if count > 0:
        print(f"✅ {count} accounts already in database")
    else:
        print("⚠️  No accounts loaded. Make sure .env has SMTP_ACCOUNTS_JSON")
EOF

echo ""
echo "===================================="
echo "✅ Setup complete!"
echo ""
echo "To start the app, run:"
echo "  ./run.sh"
echo ""
echo "The app will run on: http://127.0.0.1:5000"
echo "Access it from your phone browser once connected"
