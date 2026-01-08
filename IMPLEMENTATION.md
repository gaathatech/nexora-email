# Nexora Email Marketing - Enhanced Implementation Guide

## ✨ New Features Implemented

### 1. **Per-Account Daily Limits (100 emails per account)**
- Each SMTP account can send up to 100 emails per day
- With 4 accounts = **400 emails/day total capacity**
- System automatically rotates between available accounts
- Respects daily limits without manual intervention

**How it works:**
```python
# New SmtpAccount model tracks each email account
account.can_send()  # Checks if account has capacity today
get_available_account()  # Returns next available account
```

### 2. **Service Resume Capability**

#### 2a. **Resume when adding new email IDs**
- New accounts are automatically detected and used
- Pending emails from previous queue get sent through new accounts
- No manual restart required

```python
# Routes:
/accounts              # Manage SMTP accounts (add/remove/enable/disable)
/account/toggle/<id>   # Enable/disable specific accounts
```

#### 2b. **Resume pending emails**
- Emails marked as "pending" wait for account capacity
- Auto-resumes when capacity becomes available
- Can manually resume:

```python
/campaign/resume/<id>  # Resume a paused/pending campaign
/campaign/pause/<id>   # Pause a campaign
```

#### 2c. **Handle duplicate email IDs**
- Duplicate emails are automatically detected
- Duplicates in recipients list are removed (deduplication)
- Database unique constraint prevents duplicate accounts

```python
# Automatic deduplication in send_campaign_email()
recipients = list(dict.fromkeys(recipients))
```

### 3. **Enhanced Email Tracking**

**Open Tracking:**
- Email opens detected via invisible pixel
- Device type detection (mobile/desktop/tablet)
- User agent captured
- IP address logged

**Click Tracking:**
- All link clicks tracked
- Button click identification
- Link text/label captured
- Click type classification (link/button/image)
- Device & IP information

**New Tracking Fields:**
```python
OpenLog:
  - device_type (mobile, desktop, tablet)
  - user_agent
  - ip_address

ClickLog:
  - link_text (button label or URL)
  - click_type (link, button, image)
  - user_agent
  - ip_address
```

### 4. **Comprehensive Reporting**

#### Analytics Dashboard
```
/analytics              # Overview of all campaigns
/campaign/<id>/report   # Detailed campaign report
/campaign/<id>/report.html  # Downloadable HTML report
/accounts/performance   # SMTP account performance metrics
```

**Report Metrics:**
- Sent count
- Unique opens + open rate
- Unique clicks + click rate
- Failed/Pending emails
- Top performing links (by clicks)
- Device breakdown (opens by device)
- Click type breakdown
- Hourly timeline
- Account success rates

---

## 📋 Database Schema Changes

### New Model: SmtpAccount
```python
class SmtpAccount(db.Model):
    id              INTEGER PRIMARY KEY
    email           STRING UNIQUE
    password        STRING
    daily_limit     INTEGER (default: 100)
    is_active       BOOLEAN (default: True)
    created_at      DATETIME
    last_used       DATETIME
```

### Updated Models

**Campaign:**
- ✨ `status` (draft, pending, paused, sent)
- ✨ `started_at` (timestamp)
- ✨ `completed_at` (timestamp)
- ✨ `total_recipients` (count)
- ✨ `sent_count` (count)
- ✨ `failed_count` (count)

**SendLog:**
- ✨ `campaign_id` FK (foreign key)
- ✨ `status` values: pending, sent, failed, bounced
- ✨ `retry_count` (tracks retries)
- Status changed from "SENT"/"FAILED" to "sent"/"failed"

**OpenLog:**
- ✨ `campaign_id` FK
- ✨ `device_type` (mobile, desktop, tablet)
- ✨ `user_agent`
- ✨ `ip_address`

**ClickLog:**
- ✨ `campaign_id` FK
- ✨ `link_text` (button/link label)
- ✨ `click_type` (link, button, image)
- ✨ `user_agent`
- ✨ `ip_address`

---

## 🚀 Usage Guide

### 1. **Setup SMTP Accounts**

Visit `/accounts` and add Gmail accounts:
- Email: your-email@gmail.com
- Password: App password (not regular password)
- Daily Limit: 100 (or custom)

**Note:** For Gmail, use [App Passwords](https://support.google.com/accounts/answer/185833)

### 2. **Create & Send Campaign**

```
/campaign/new                    # Create new campaign
/campaign/send/<id>              # Send to subscribed contacts
```

When sending:
- System checks available capacity
- Emails sent immediately if capacity exists
- Excess emails marked as "pending"
- Pending emails auto-send when capacity available

### 3. **Campaign Management**

```
/campaign/pause/<id>             # Pause a campaign
/campaign/resume/<id>            # Resume paused campaign
/campaign/retry-failed           # Retry up to 20 failed emails
```

### 4. **Monitor Performance**

```
/analytics                       # Campaign overview
/campaign/<id>/report            # Detailed report
/accounts/performance            # Account metrics
/api/campaign/<id>/stats         # JSON stats API
```

---

## 🔧 Email Template Tips

### Open Tracking
Add tracking pixel to your email template:
```html
<img src="{{ url_for('main.track_open', cid=campaign.id, email=recipient_email, _external=True) }}" 
     alt="" width="1" height="1" style="display:none;">
```

### Click Tracking
Wrap links in tracking redirects:
```html
<a href="{{ url_for('main.track_click', cid=campaign.id, email=recipient_email, url='https://yoursite.com', text='Click Here', type='button', _external=True) }}">
    Click Here
</a>
```

Or use simpler format:
```
/track/click?cid=1&email=user@example.com&url=https://yoursite.com&text=Button&type=button
```

---

## 📊 API Endpoints

### JSON Statistics
```
GET /api/campaign/<id>/stats

Response:
{
  "campaign_id": 1,
  "sent": 100,
  "opens": 45,
  "clicks": 12,
  "open_rate": "45.00%",
  "click_rate": "12.00%"
}
```

---

## 🔄 Service Resume Flow

```
Add new SMTP account
        ↓
System detects new account
        ↓
Pending emails auto-resume
        ↓
New account receives emails immediately
```

---

## ⚙️ Configuration

Update `.env`:
```bash
SECRET_KEY=your-secret-key
SQLALCHEMY_DATABASE_URI=sqlite:///email_marketing.db
REPORT_EMAIL=admin@yourcompany.com
DAILY_EMAIL_LIMIT=100  # Per account (deprecated, use SmtpAccount.daily_limit)
```

**Note:** Old config still works but new SmtpAccount.daily_limit takes precedence.

---

## 🧪 Testing

```bash
python app.py
```

Then visit:
- http://localhost:5000/          # Dashboard
- http://localhost:5000/accounts  # Manage accounts
- http://localhost:5000/analytics # View reports

---

## 📁 New Files Added

- `utils/reporting.py`          # Advanced reporting functions
- `templates/accounts.html`     # Account management UI
- `templates/campaign_report.html` # Campaign report view
- `templates/account_performance.html` # Account metrics view

---

## 🚨 Status Values (Case-Sensitive)

Use lowercase for new code:
- `pending`  - Waiting to send
- `sent`     - Successfully delivered
- `failed`   - Delivery failed
- `bounced`  - Bounced email

---

## ✅ Verification Checklist

- [x] Per-account daily limits working
- [x] Service resume for new accounts
- [x] Resume pending emails
- [x] Duplicate email detection
- [x] Enhanced open tracking (device type, user agent, IP)
- [x] Enhanced click tracking (link text, click type)
- [x] Comprehensive analytics
- [x] Detailed reporting with HTML export
- [x] SMTP account management interface
- [x] Campaign status tracking
