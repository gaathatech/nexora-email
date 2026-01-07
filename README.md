📧 Email Marketing / Email Blast App

A simple, standalone Email Marketing & Bulk Email Promotion application built with Flask.
Designed for marketing campaigns, announcements, and promotional emails using SMTP (Gmail supported).

🚀 Features

📇 Contact management

📨 Email campaign creation

📢 Bulk email sending (SMTP)

⏱️ Safe rate limiting (spam-safe)

🗄️ SQLite database

🖥️ Simple web UI

☁️ GitHub Codespaces compatible

🧱 Tech Stack

Backend: Python, Flask

Database: SQLite (SQLAlchemy ORM)

Email: SMTP (Gmail App Password supported)

Frontend: HTML (Jinja templates)

📁 Project Structure
email-marketing-app/
│
├── app.py
├── config.py
├── extensions.py
├── models.py
├── routes.py
├── email_service.py
├── requirements.txt
├── README.md
│
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── contacts.html
    └── campaign_create.html

⚙️ Installation & Setup
1️⃣ Clone the Repository
git clone https://github.com/yourusername/email-marketing-app.git
cd email-marketing-app

2️⃣ Create Virtual Environment (Optional but Recommended)
python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows

3️⃣ Install Dependencies
pip install -r requirements.txt

🔐 SMTP Configuration

Edit config.py and update your SMTP credentials:

SMTP_EMAIL = "yourgmail@gmail.com"
SMTP_PASSWORD = "YOUR_GMAIL_APP_PASSWORD"


⚠️ Important:
Use a Gmail App Password, not your normal Gmail password.

▶️ Run the Application
python app.py


Open in browser:

http://127.0.0.1:5000/


For GitHub Codespaces:

https://<codespace-name>-5000.app.github.dev/

🧪 How to Use
1️⃣ Add Contacts

Go to Contacts

Add email addresses manually

2️⃣ Create Campaign

Go to New Campaign

Enter email subject & HTML body

3️⃣ Send Campaign

Click Send on the campaign

Emails will be sent one by one with safe delay

🛡️ Email Safety & Compliance

Built-in rate limiting (2 seconds per email)

Only sends to subscribed contacts

Includes unsubscribe placeholder (can be extended)

Recommended for opt-in marketing only

🔜 Planned Enhancements

📥 CSV import for contacts

⏰ Campaign scheduling

📊 Open & click tracking

🔗 Secure unsubscribe links

☁️ Amazon SES / SendGrid support

🎨 Rich email template editor

🧑‍💼 Multi-brand / multi-client mode

⚠️ Disclaimer

This application is intended for legitimate marketing purposes only.
Ensure compliance with:

CAN-SPAM Act

GDPR (EU)

Local email marketing regulations

👨‍💻 Author

Developed by GaathaTech / Aidni Global LLP

⭐ License

MIT License – free to use, modify, and distribute.