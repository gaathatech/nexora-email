# Nexora Email Marketing App

Independent bulk email campaign manager - runs on **Linux, Mac, Windows, or Android (Termux)**.

## ✨ Features
- ✉️ Email campaigns with A/B variants
- 👥 Contact groups & management
- 📧 Multi-Gmail SMTP rotation (4 accounts)
- 📊 Daily send limits per account
- 📈 Live campaign tracking & analytics
- 📱 Device/IP detection for opens & clicks
- 🔄 Automatic retry on failure
- 💾 SQLite local database

## 🚀 Quick Start

### **Option 1: Termux (Android Phone)** 📱
See [TERMUX_SETUP.md](TERMUX_SETUP.md) for complete instructions!

```bash
apt install python3 python3-pip git
git clone https://github.com/gaathatech/nexora-email.git
cd nexora-email
bash setup.sh
bash run.sh
```

Then open: `http://127.0.0.1:5000`

### **Option 2: Linux/Mac/Windows**

```bash
pip install -r requirements.txt
python app.py
```

Then open: `http://127.0.0.1:5000`

### **Option 3: Docker**

```bash
docker build -t nexora .
docker run -p 5000:5000 nexora
```

---

## ⚙️ Configuration

Create a `.env` file with your Gmail app passwords:

```env
FLASK_ENV=production
SECRET_KEY=your-secret-key

SMTP_ACCOUNTS_JSON=[
  { "email": "account1@gmail.com", "password": "APP_PASSWORD" },
  { "email": "account2@gmail.com", "password": "APP_PASSWORD" },
  { "email": "account3@gmail.com", "password": "APP_PASSWORD" },
  { "email": "account4@gmail.com", "password": "APP_PASSWORD" }
]
```

**Note:** Use [Gmail App Passwords](https://myaccount.google.com/apppasswords) (not your regular password)

---

## 📝 Usage

1. **Add Contacts**: Go to Contacts → paste emails
2. **Create Groups**: Go to Groups → create group → add contacts
3. **Create Campaign**: Go to Campaigns → write email → select target group
4. **Send**: Preview email → click "Send Campaign"
5. **Track**: View live progress on dashboard & analytics

---

## 🌐 Access from Other Devices

If running on your phone/server, access from another device:

```bash
# Find your IP (in another terminal)
ifconfig

# Then open in browser on another device
http://<YOUR_IP>:5000
```

---

## 📁 Project Structure

```
nexora-email/
├── app.py                 # Flask app entry point
├── models.py              # Database models
├── routes.py              # URL endpoints
├── email_service.py       # SMTP sending logic
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
├── setup.sh              # Setup script
├── run.sh                # Run script
├── Dockerfile            # Docker containerization
├── docker-compose.yml    # Docker Compose config
├── templates/            # HTML templates
└── static/               # CSS/JS files
```

---

## 🛠️ Troubleshooting

### Gmail Authentication Fails
- Use app passwords from [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- Enable 2-factor authentication on Gmail account
- Update `.env` with new passwords and restart app

### Port 5000 Already in Use
```bash
pkill -f "python app.py"
```

### Database Issues
```bash
rm instance/email_marketing.db
bash setup.sh
```

---

## 📱 Termux-Specific

See [TERMUX_SETUP.md](TERMUX_SETUP.md) for detailed Termux instructions!

---

## 📄 License

MIT License - Use freely!

## 🚀 Ready to Go!

Start sending emails from your phone now!
