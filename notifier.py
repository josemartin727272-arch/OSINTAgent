"""
notifier.py — Send email alerts for high-relevance findings.
Each alert is a card with: score, source link, summary, and why it was flagged.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from config import ALERT_EMAIL_FROM, ALERT_EMAIL_TO, ALERT_EMAIL_PASSWORD, ALERT_THRESHOLD

EVENT_TYPE_HE = {
    "demonstration": "הפגנה / עצרת",
    "boycott": "קריאה לחרם",
    "violence": "אירוע אלים / איום",
    "online_campaign": "קמפיין ברשת",
    "statement": "הצהרה / גינוי",
    "other": "אירוע כללי",
    "none": "לא מוגדר",
}


def _score_color(score: int) -> str:
    if score >= 8:
        return "#cc0000"
    if score >= 6:
        return "#e67e00"
    return "#2980b9"


def _build_card(a: dict) -> str:
    score = a.get("relevance_score", 0)
    color = _score_color(score)
    event_type = EVENT_TYPE_HE.get(a.get("event_type", "other"), "אירוע")
    location = a.get("location") or "לא צוין"
    link = a.get("link", "")
    title = a.get("title", "")
    source = a.get("source", "")
    published = a.get("published", "")
    summary_raw = a.get("summary", "")[:400]
    org = a.get("org_name", "")

    # Why was it flagged — plain language
    why_flagged = f"כתבה זו קיבלה ציון <b>{score}/10</b> כיוון שזוהו מילות מפתח הקשורות ל<b>{event_type}</b>"
    if location != "לא צוין":
        why_flagged += f" במיקום <b>{location}</b>"
    why_flagged += "."

    return f"""
    <div style="border:2px solid {color};border-radius:8px;padding:16px;margin-bottom:20px;
                font-family:Arial,sans-serif;direction:rtl;text-align:right;">

        <!-- Header row -->
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <span style="background:{color};color:white;font-size:18px;font-weight:bold;
                         padding:4px 12px;border-radius:20px;">{score}/10</span>
            <span style="color:#555;font-size:13px">{event_type} | {location}</span>
        </div>

        <!-- Title as link -->
        <h3 style="margin:0 0 6px 0;font-size:15px;">
            <a href="{link}" style="color:{color};text-decoration:none;">{title}</a>
        </h3>

        <!-- Source & date -->
        <p style="margin:0 0 10px 0;color:#777;font-size:12px;">
            📰 מקור: <b>{source}</b> &nbsp;|&nbsp; 📅 {published[:22] if published else "—"}
            &nbsp;|&nbsp; 🏢 ארגון: {org}
        </p>

        <!-- Why flagged -->
        <div style="background:#fff8e1;border-right:4px solid {color};
                    padding:8px 12px;margin-bottom:10px;font-size:13px;color:#333;">
            {why_flagged}
        </div>

        <!-- Article summary -->
        <div style="background:#f9f9f9;padding:10px;border-radius:4px;font-size:13px;
                    color:#444;margin-bottom:10px;">
            <b>תקציר הכתבה:</b><br>
            {summary_raw}...
        </div>

        <!-- Link button -->
        <a href="{link}"
           style="display:inline-block;background:{color};color:white;padding:8px 16px;
                  border-radius:4px;text-decoration:none;font-size:13px;font-weight:bold;">
            🔗 פתח את הכתבה המקורית
        </a>
    </div>
    """


def _build_html(alerts: list[dict]) -> str:
    cards = "".join(_build_card(a) for a in alerts)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return f"""
    <html>
    <body style="background:#f0f0f0;padding:20px;font-family:Arial,sans-serif;">
        <div style="max-width:700px;margin:0 auto;">

            <!-- Header -->
            <div style="background:#cc0000;color:white;padding:16px 20px;border-radius:8px 8px 0 0;
                        text-align:right;direction:rtl;">
                <h2 style="margin:0;font-size:20px;">🔔 OSINTAgent — {len(alerts)} התרעות חדשות</h2>
                <p style="margin:4px 0 0 0;font-size:13px;opacity:0.85;">דיווח מתאריך: {now}</p>
            </div>

            <!-- Summary bar -->
            <div style="background:#333;color:white;padding:10px 20px;font-size:13px;
                        text-align:right;direction:rtl;">
                סף התרעה: {ALERT_THRESHOLD}/10 &nbsp;|&nbsp;
                כתבות בסריקה זו: {len(alerts)} &nbsp;|&nbsp;
                <span style="color:#ff9900;">🔴 אדום = 8-10 &nbsp; 🟠 כתום = 6-7</span>
            </div>

            <!-- Cards -->
            <div style="background:white;padding:20px;border-radius:0 0 8px 8px;">
                {cards}
            </div>

            <!-- Footer -->
            <p style="text-align:center;color:#aaa;font-size:11px;margin-top:10px;">
                נשלח אוטומטית על ידי OSINTAgent | GitHub Actions
            </p>
        </div>
    </body>
    </html>
    """


def send_alert_email(alerts: list[dict]) -> None:
    if not alerts:
        print("[notifier] No alerts to send")
        return

    if not all([ALERT_EMAIL_FROM, ALERT_EMAIL_TO, ALERT_EMAIL_PASSWORD]):
        print("[notifier] Email credentials not configured — skipping")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔔 [OSINTAgent] {len(alerts)} התרעות חדשות — פרו"
    msg["From"] = ALERT_EMAIL_FROM
    msg["To"] = ALERT_EMAIL_TO

    msg.attach(MIMEText(_build_html(alerts), "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(ALERT_EMAIL_FROM, ALERT_EMAIL_PASSWORD)
            server.sendmail(ALERT_EMAIL_FROM, ALERT_EMAIL_TO, msg.as_bytes())
        print(f"[notifier] Alert email sent: {len(alerts)} items")
    except Exception as e:
        print(f"[notifier] Failed to send email: {e}")
        raise
