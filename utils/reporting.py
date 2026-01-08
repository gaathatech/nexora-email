"""
Advanced reporting module for email campaigns
"""
from datetime import datetime, timedelta
from models import SendLog, OpenLog, ClickLog, Campaign
from extensions import db
from sqlalchemy import and_, func

def get_campaign_report(campaign_id):
    """Generate comprehensive report for a campaign"""
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return None
    
    # Get send stats
    sent_logs = SendLog.query.filter_by(
        campaign_id=campaign_id,
        status="sent"
    ).all()
    
    failed_logs = SendLog.query.filter_by(
        campaign_id=campaign_id,
        status="failed"
    ).count()
    
    pending_logs = SendLog.query.filter_by(
        campaign_id=campaign_id,
        status="pending"
    ).count()
    
    sent_count = len(sent_logs)
    
    # Get engagement stats
    opens = OpenLog.query.filter_by(campaign_id=campaign_id).count()
    unique_opens = db.session.query(
        OpenLog.recipient
    ).filter_by(campaign_id=campaign_id).distinct().count()
    
    clicks = ClickLog.query.filter_by(campaign_id=campaign_id).count()
    unique_clicks = db.session.query(
        ClickLog.recipient
    ).filter_by(campaign_id=campaign_id).distinct().count()
    
    # Calculate rates
    open_rate = (opens / sent_count * 100) if sent_count > 0 else 0
    unique_open_rate = (unique_opens / sent_count * 100) if sent_count > 0 else 0
    click_rate = (clicks / sent_count * 100) if sent_count > 0 else 0
    unique_click_rate = (unique_clicks / sent_count * 100) if sent_count > 0 else 0
    
    # Get top performing links
    top_links = db.session.query(
        ClickLog.url,
        ClickLog.link_text,
        ClickLog.click_type,
        func.count(ClickLog.id).label('count')
    ).filter_by(campaign_id=campaign_id).group_by(
        ClickLog.url, ClickLog.link_text, ClickLog.click_type
    ).order_by(db.desc(func.count(ClickLog.id))).limit(10).all()
    
    # Device breakdown
    device_stats = db.session.query(
        OpenLog.device_type,
        func.count(OpenLog.id).label('count')
    ).filter_by(campaign_id=campaign_id).group_by(
        OpenLog.device_type
    ).all()
    
    # Click type breakdown
    click_type_stats = db.session.query(
        ClickLog.click_type,
        func.count(ClickLog.id).label('count')
    ).filter_by(campaign_id=campaign_id).group_by(
        ClickLog.click_type
    ).all()
    
    # Timeline data (hourly)
    timeline = db.session.query(
        func.strftime('%Y-%m-%d %H:00', OpenLog.opened_at).label('hour'),
        func.count(OpenLog.id).label('opens')
    ).filter_by(campaign_id=campaign_id).group_by(
        func.strftime('%Y-%m-%d %H:00', OpenLog.opened_at)
    ).order_by('hour').all()
    
    # Geographic data (if available via IP)
    # This is simplified; real implementation would use IP geolocation service
    
    return {
        'campaign': campaign,
        'sent': sent_count,
        'failed': failed_logs,
        'pending': pending_logs,
        'opens': opens,
        'unique_opens': unique_opens,
        'clicks': clicks,
        'unique_clicks': unique_clicks,
        'open_rate': f"{open_rate:.2f}%",
        'unique_open_rate': f"{unique_open_rate:.2f}%",
        'click_rate': f"{click_rate:.2f}%",
        'unique_click_rate': f"{unique_click_rate:.2f}%",
        'top_links': top_links,
        'device_stats': device_stats,
        'click_type_stats': click_type_stats,
        'timeline': timeline,
        'generated_at': datetime.utcnow().isoformat()
    }

def get_account_performance(days=7):
    """Get SMTP account performance over last N days"""
    from models import SmtpAccount
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    accounts = SmtpAccount.query.filter_by(is_active=True).all()
    performance = []
    
    for account in accounts:
        sent = SendLog.query.filter(
            and_(
                SendLog.sender == account.email,
                SendLog.status == "sent",
                SendLog.timestamp >= cutoff_date
            )
        ).count()
        
        failed = SendLog.query.filter(
            and_(
                SendLog.sender == account.email,
                SendLog.status == "failed",
                SendLog.timestamp >= cutoff_date
            )
        ).count()
        
        success_rate = (sent / (sent + failed) * 100) if (sent + failed) > 0 else 0
        
        performance.append({
            'email': account.email,
            'sent': sent,
            'failed': failed,
            'success_rate': f"{success_rate:.2f}%",
            'daily_limit': account.daily_limit
        })
    
    return performance

def generate_html_report(campaign_id):
    """Generate HTML formatted campaign report"""
    report = get_campaign_report(campaign_id)
    if not report:
        return None
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            .metrics {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 20px; margin: 20px 0; }}
            .metric {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #0066cc; }}
            .metric-label {{ color: #666; font-size: 12px; margin-top: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background: #0066cc; color: white; }}
        </style>
    </head>
    <body>
        <h1>Campaign Report: {report['campaign'].subject}</h1>
        <p>Generated: {report['generated_at']}</p>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{report['sent']}</div>
                <div class="metric-label">Emails Sent</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report['unique_opens']}</div>
                <div class="metric-label">Unique Opens ({report['unique_open_rate']})</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report['unique_clicks']}</div>
                <div class="metric-label">Unique Clicks ({report['unique_click_rate']})</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report['failed']}</div>
                <div class="metric-label">Failed</div>
            </div>
        </div>
        
        <h2>Top Performing Links</h2>
        <table>
            <tr><th>Link Text</th><th>Type</th><th>Clicks</th></tr>
    """
    
    for link in report['top_links']:
        html += f"<tr><td>{link.link_text or link.url}</td><td>{link.click_type}</td><td>{link.count}</td></tr>"
    
    html += """
        </table>
        
        <h2>Device Breakdown</h2>
        <table>
            <tr><th>Device</th><th>Opens</th></tr>
    """
    
    for device in report['device_stats']:
        device_type = device.device_type or 'Unknown'
        html += f"<tr><td>{device_type}</td><td>{device.count}</td></tr>"
    
    html += """
        </table>
    </body>
    </html>
    """
    
    return html
