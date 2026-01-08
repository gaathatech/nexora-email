# Quick Reference - New Features

## 🎯 Main Routes

| Route | Purpose | Method |
|-------|---------|--------|
| `/accounts` | Manage SMTP accounts | GET/POST |
| `/accounts/performance` | Account metrics | GET |
| `/campaign/new` | Create campaign | GET/POST |
| `/campaign/send/<id>` | Send campaign | GET |
| `/campaign/pause/<id>` | Pause campaign | GET |
| `/campaign/resume/<id>` | Resume campaign | GET |
| `/campaign/retry-failed` | Retry failed emails | GET |
| `/campaign/<id>/report` | Detailed report | GET |
| `/campaign/<id>/report.html` | Download report | GET |
| `/analytics` | Campaign overview | GET |
| `/api/campaign/<id>/stats` | JSON API | GET |

---

## 📊 Database Queries

### Get today's send count by account
```python
from models import SendLog
from datetime import date
from sqlalchemy import and_

SendLog.query.filter(
    and_(
        SendLog.sender == 'account@gmail.com',
        SendLog.status == 'sent',
        db.func.date(SendLog.timestamp) == date.today()
    )
).count()
```

### Get pending emails for campaign
```python
SendLog.query.filter_by(
    campaign_id=1,
    status='pending'
).count()
```

### Get campaign engagement metrics
```python
campaign_id = 1
opens = OpenLog.query.filter_by(campaign_id=campaign_id).count()
clicks = ClickLog.query.filter_by(campaign_id=campaign_id).count()
sent = SendLog.query.filter_by(
    campaign_id=campaign_id, 
    status='sent'
).count()

open_rate = (opens / sent * 100) if sent > 0 else 0
```

---

## 🚀 Python API

### Send Campaign Programmatically
```python
from email_service import send_campaign_email

recipients = ['user1@example.com', 'user2@example.com']
sent, failed, pending = send_campaign_email(
    subject='Hello',
    html_body='<p>Welcome</p>',
    recipients=recipients,
    campaign_id=1  # optional
)

print(f"Sent: {sent}, Failed: {len(failed)}, Pending: {pending}")
```

### Resume Pending Campaign
```python
from email_service import resume_pending_campaign

sent, failures = resume_pending_campaign(campaign_id=1)
print(f"Resumed: {sent} emails")
```

### Get Campaign Report
```python
from utils.reporting import get_campaign_report

report = get_campaign_report(campaign_id=1)
print(f"Open rate: {report['unique_open_rate']}")
print(f"Click rate: {report['unique_click_rate']}")
print(f"Top links: {report['top_links']}")
```

---

## 📧 Email Template Examples

### Add Open Tracking
```html
<!-- Place at end of email body -->
<img src="{{ url_for('main.track_open', cid=campaign_id, email=recipient_email, _external=True) }}" 
     alt="" width="1" height="1" style="display:none;">
```

### Add Click Tracking (Button)
```html
<a href="{{ url_for('main.track_click', 
           cid=campaign_id, 
           email=recipient_email, 
           url='https://example.com/promo',
           text='Claim Offer',
           type='button',
           _external=True) }}"
   class="btn btn-primary">
    Claim Offer
</a>
```

### Simple Link Format
```
https://yourapp.com/track/click?cid=1&email=user@example.com&url=https://example.com&text=Link&type=link
```

---

## 🔄 Campaign Lifecycle

```
1. Create        → /campaign/new (Status: draft)
2. Send          → /campaign/send/<id> (Status: pending/sent)
3. Monitor       → /analytics
4. View Report   → /campaign/<id>/report
5. Pause/Resume  → /campaign/pause/<id>, /campaign/resume/<id>
6. Retry Failed  → /campaign/retry-failed
```

---

## ⚙️ Status Values (Use Lowercase)

| Status | Meaning |
|--------|---------|
| `draft` | Not yet sent |
| `pending` | Waiting for account capacity |
| `sent` | Successfully delivered |
| `failed` | Delivery failed (can retry) |
| `paused` | Campaign paused by user |
| `bounced` | Permanent failure |

---

## 📈 Key Metrics

| Metric | Definition |
|--------|-----------|
| **Open Rate** | (Unique Opens / Sent) × 100% |
| **Click Rate** | (Unique Clicks / Sent) × 100% |
| **Success Rate** | (Sent / Total) × 100% |
| **Device Opens** | Breakdown: mobile, desktop, tablet |
| **Click Type** | Breakdown: link, button, image |

---

## 🛠️ Troubleshooting

### Pending emails not resuming?
- Check SMTP account has capacity: `account.can_send()`
- Verify account is active: `account.is_active == True`
- Check daily limit: `account.daily_limit`

### No tracking data?
- Verify pixel URL in email template
- Check tracking routes are working: `/track/open/<cid>/<email>`
- Verify OpenLog/ClickLog records: `db.session.query(OpenLog).count()`

### Campaign stuck in pending?
- Manually resume: `/campaign/resume/<id>`
- Add more SMTP accounts to increase capacity
- Check account daily limits

---

## 📚 Related Files

- `models.py` - Database schema
- `email_service.py` - Sending & tracking logic
- `routes.py` - All web endpoints
- `utils/reporting.py` - Advanced reporting
- `IMPLEMENTATION.md` - Complete feature guide

---

**Version:** 2.0 (Enhanced)  
**Status:** ✅ Production Ready
