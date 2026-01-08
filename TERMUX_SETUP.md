# 🚀 Nexora Email Engine - Termux Setup Guide

Run Nexora Email Engine on your Android phone using Termux!

## ⚡ Quick Start (3 steps)

### 1️⃣ Install Termux
- Download **Termux** from F-Droid or Google Play Store
- Open Termux

### 2️⃣ Clone & Setup
```bash
# Update packages
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip git

# Clone the repository
git clone https://github.com/gaathatech/nexora-email.git
cd nexora-email

# Run setup
bash setup.sh
```

### 3️⃣ Start the App
```bash
bash run.sh
```

You'll see:
```
 * Running on http://127.0.0.1:5000
```

---

## 📱 Access from Your Phone

Once the app is running, open your phone's browser and go to:
```
http://127.0.0.1:5000
```

Or if accessing from another device on the same network, find your phone's IP:
```bash
# In another Termux tab
ifconfig
```

Then access from other device:
```
http://<YOUR_PHONE_IP>:5000
```

---

## ⚙️ Setup .env File

**Before running setup.sh**, create a `.env` file with your SMTP accounts:

```bash
# In Termux
nano .env
```

Paste this (update with YOUR app passwords):
```
FLASK_ENV=production
DATABASE_URL=sqlite:///instance/email_marketing.db
SECRET_KEY=your-secret-key-here

SMTP_ACCOUNTS_JSON=[
  { "email": "your1@gmail.com", "password": "app_password_here" },
  { "email": "your2@gmail.com", "password": "app_password_here" },
  { "email": "your3@gmail.com", "password": "app_password_here" },
  { "email": "your4@gmail.com", "password": "app_password_here" }
]
```

Press **Ctrl+X**, then **Y**, then **Enter** to save.

---

## 🐳 Docker Option (Advanced)

If you have Docker on your phone:

```bash
# Build
docker build -t nexora-email .

# Run
docker run -p 5000:5000 -v $(pwd)/.env:/app/.env:ro nexora-email

# Or with docker-compose
docker-compose up -d
```

---

## 📊 Features

✅ **Campaign Management** - Create and send email campaigns  
✅ **Contact Groups** - Organize contacts by groups  
✅ **Multi-Account SMTP** - Send from 4 Gmail accounts with daily limits  
✅ **Live Tracking** - Monitor email opens, clicks, device type  
✅ **Analytics Dashboard** - Real-time sending progress and reports  

---

## 🔧 Troubleshooting

### App won't start
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check if port 5000 is in use
netstat -tuln | grep 5000

# Kill existing process
pkill -f "python.*app.py"
```

### Gmail authentication errors
1. Generate new app passwords: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Update `.env` with new passwords
3. Restart: `bash run.sh`

### Database locked
```bash
# Reset database
rm instance/email_marketing.db
bash setup.sh
```

### Keep app running in background
```bash
# Run in background with nohup
nohup bash run.sh > nexora.log 2>&1 &

# Or in a new Termux session
# Press Volume + C to open new session
```

---

## 📝 Default Credentials

**Dashboard**: http://127.0.0.1:5000  
**Contacts**: http://127.0.0.1:5000/contacts  
**Groups**: http://127.0.0.1:5000/groups  
**Analytics**: http://127.0.0.1:5000/analytics  

No login required - all data is stored locally on your phone!

---

## 📞 Need Help?

Check logs:
```bash
tail -f nexora.log
```

Or view app logs during runtime - they print to your terminal.

---

**Happy emailing! 📧**
