"""
notifier.py — Send email alerts for high-relevance findings.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from config import ALERT_EMAIL_FROM, ALERT_EMAIL_TO, ALERT_EMAIL_PASSWORD, ALERT_THRESHOLD


def _build_html(alerts: list[dict]) -> str:
    rows = ""
    for a in alerts:
        score = a.get("relevance_score", 0)
        color = "#ff4444" if score >= 8 else "#ff9900"
        rows += f"""
        <tr>
            <td style="padding:8px;border:1px solid #ddd;font-weight:bold;color:{color}">{score}/10</td>
            <td style="padding:8px;border:1px solid #ddd">{a.get("org_name","")}</td>
            <td style="padding:8px;border:1px solid #ddd">{a.get("event_type","")}</td>
            <td style="padding:8px;border:1px solid #ddd">{a.get("location") or "—"}</td>
            <td style="padding:8px;border:1px solid #ddd">{a.get("event_date") or "—"}</td>
            <td style="padding:8px;border:1px solid #ddd">
                <a href="{a.get("link","")}">{a.get("title","")[:80]}</a>
            </td>
            <td style="padding:8px;border:1px solid #ddd">{a.get("summary_he","")}</td>
        </tr>"""

    return f"""
    <html><body>
    <h2 style="color:#cc0000">🔔 OSINTAgent — {len(alerts)} התרעות חדשות</h2>
    <p>דיווח מתאריך: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}</p>
    <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:13px">
        <tr style="background:#333;color:white">
            <th style="padding:8px">ציון</th>
            <th style="padding:8px">ארגון</th>
            <th style="padding:8px">סוג אירוע</th>
            <th style="padding:8px">מיקום</th>
            <th style="padding:8px">תאריך</th>
            <th style="padding:8px">כותרת</th>
            <th style="padding:8px">סיכום</th>
        </tr>
        {rows}
    </table>
    <p style="color:#888;font-size:11px">נשלח אוטומטית על ידי OSINTAgent | סף התרעה: {ALERT_THRESHOLD}/10</p>
    </body></html>
    """


def send_alert_email(alerts: list[dict]) -> None:
    """Send email with all high-relevance articles. Uses Gmail SMTP."""
    if not alerts:
        print("[notifier] No alerts to send")
        return

    if not all([ALERT_EMAIL_FROM, ALERT_EMAIL_TO, ALERT_EMAIL_PASSWORD]):
        print("[notifier] Email credentials not configured — skipping")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[OSINTAgent] {len(alerts)} התרעות — פרו"
    msg["From"] = ALERT_EMAIL_FROM
    msg["To"] = ALERT_EMAIL_TO

    html_content = _build_html(alerts)
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(ALERT_EMAIL_FROM, ALERT_EMAIL_PASSWORD)
            server.sendmail(ALERT_EMAIL_FROM, ALERT_EMAIL_TO, msg.as_bytes())
        print(f"[notifier] Alert email sent: {len(alerts)} items")
    except Exception as e:
        print(f"[notifier] Failed to send email: {e}")
        raise
