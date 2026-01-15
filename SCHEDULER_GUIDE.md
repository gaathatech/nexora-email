# Scheduled Batch Email Sending Guide

## Overview
The app now uses **APScheduler** to send emails in batches instead of all at once. This prevents hitting Gmail's daily sending limits while ensuring reliable delivery.

## How It Works

### 1. **Email Queueing**
- When you click "Send Campaign", emails are **queued** instead of sent immediately
- Queue is stored in memory and survives app restarts via database persistence
- You get instant feedback: "Queued 1,234 emails for sending"

### 2. **Batch Sending** (Every 30 seconds)
- Scheduler automatically sends **max 10 emails per batch**
- Rate limiting: 2-second delay between emails
- Respects per-account daily limits (100 emails/account/day)
- Rotates between available accounts

### 3. **Automatic Retry** (Every 5 minutes)
- Failed emails automatically retry (max 3 retries per email)
- Only retries if account capacity available
- Useful for temporary network issues

## Benefits

### ✅ Respects Gmail Limits
- Regular Gmail: 500 emails/day per account
- With 6 accounts: Can send ~3,000 emails/day spread over time
- Prevents "Daily user sending limit exceeded" errors

### ✅ Reliable Delivery
- Batch system provides better reliability
- Automatic retry mechanism
- Real-time progress tracking in dashboard

### ✅ Better User Experience
- Immediate feedback (no waiting for all emails to send)
- See progress in dashboard as batches go out
- Can queue multiple campaigns and they send in order

## Configuration

### Batch Size
Edit [email_service.py](email_service.py#L360):
```python
batch = EMAIL_QUEUE[:10]  # Change 10 to your batch size
```

### Batch Interval
Edit [email_service.py](email_service.py#L333):
```python
trigger=IntervalTrigger(seconds=30)  # Change 30 to desired seconds
```

### Retry Interval
Edit [email_service.py](email_service.py#L342):
```python
trigger=IntervalTrigger(minutes=5)  # Change 5 to desired minutes
```

## Monitoring

### Check Queue Status
```bash
python -c "
from app import app
with app.app_context():
    from email_service import EMAIL_QUEUE
    print(f'Emails in queue: {len(EMAIL_QUEUE)}')
"
```

### Monitor Daily Sending
Check dashboard:
- **Sent**: Total sent today
- **Failed**: Total failed (requires retry)
- **Pending**: Still in queue waiting to send

### View Logs
Scheduler logs appear in app output:
```
📤 Batch sent: 10 emails, 0 failures. Queue remaining: 234
🔄 Retried 2 failed emails
```

## Troubleshooting

### Emails Not Sending
1. Check if scheduler is running: Look for "✅ Email scheduler started" on app startup
2. Verify accounts have capacity: Check "Accounts" page
3. Check for errors: Review app logs for authentication issues

### Queue Growing Too Large
- Reduce batch interval (e.g., 20 seconds instead of 30)
- Increase batch size (e.g., 15 instead of 10)
- Verify SMTP accounts are working correctly

### Still Hitting Daily Limits
- Lower the per-account daily limit (100 → 80)
- Spread sending across more days
- Use Google Workspace accounts (higher limits)

## Database Schema Updates

The scheduler uses existing tables:
- **SendLog**: Tracks all sent/failed emails
- **SmtpAccount**: Stores account info and daily limits
- **Campaign**: Tracks campaign progress

No schema migration needed - fully backward compatible!

## Performance Notes

- **Memory Usage**: Queue stored in RAM (~1KB per email)
- **CPU Usage**: Minimal - mostly idle between batches
- **Database Queries**: One INSERT per email + one UPDATE per batch
- **Typical Throughput**: 20 emails/minute (10 per 30s batch)

## Next Steps

1. **Test It**: Send a small campaign and watch the dashboard
2. **Monitor**: Check logs for any authentication issues
3. **Tune**: Adjust batch size/interval based on your needs
4. **Scale**: Add more Gmail accounts if needed (max 6 recommended)

