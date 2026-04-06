"""
notifier.py — Email alerts and periodic summary reports.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from collections import Counter

from config import ALERT_EMAIL_FROM, ALERT_EMAIL_TO, ALERT_EMAIL_PASSWORD, ALERT_THRESHOLD

EVENT_TYPE_HE = {
    "demonstration":   "הפגנה / עצרת",
    "boycott":         "קריאה לחרם",
    "violence":        "אירוע אלים / איום",
    "online_campaign": "קמפיין ברשת",
    "statement":       "הצהרה / גינוי",
    "other":           "אירוע כללי",
    "none":            "לא מוגדר",
}


def _score_color(score) -> str:
    score = int(score) if score else 0
    if score >= 8: return "#cc0000"
    if score >= 6: return "#e67e00"
    return "#2980b9"


def _check_credentials() -> bool:
    return all([ALERT_EMAIL_FROM, ALERT_EMAIL_TO, ALERT_EMAIL_PASSWORD])


def _send_email(subject: str, html_body: str, to: str = None) -> bool:
    if not _check_credentials():
        print("[notifier] Email credentials not configured — skipping")
        return False
    recipient = to or ALERT_EMAIL_TO
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = ALERT_EMAIL_FROM
    msg["To"]      = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(ALERT_EMAIL_FROM, ALERT_EMAIL_PASSWORD)
            server.sendmail(ALERT_EMAIL_FROM, recipient, msg.as_bytes())
        print(f"[notifier] Email sent to {recipient}")
        return True
    except Exception as e:
        print(f"[notifier] Failed: {e}")
        raise


# ── Alert Email ───────────────────────────────────────────────────────────────

def _build_alert_card(a: dict) -> str:
    score = int(a.get("relevance_score", 0))
    color = _score_color(score)
    event_type = EVENT_TYPE_HE.get(a.get("event_type", "other"), "אירוע")
    location = a.get("location") or "לא צוין"
    link = a.get("link", "")
    title = a.get("title", "")
    source = a.get("source", "")
    published = str(a.get("published", ""))
    summary_raw = str(a.get("summary", ""))[:400]
    org = a.get("org_name", "")
    return f"""
    <div style="border:2px solid {color};border-radius:8px;padding:16px;margin-bottom:20px;
                font-family:Arial,sans-serif;direction:rtl;text-align:right;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <span style="background:{color};color:white;font-size:18px;font-weight:bold;
                         padding:4px 12px;border-radius:20px;">{score}/10</span>
            <span style="color:#555;font-size:13px">{event_type} | {location}</span>
        </div>
        <h3 style="margin:0 0 6px 0;font-size:15px;">
            <a href="{link}" style="color:{color};text-decoration:none;">{title}</a>
        </h3>
        <p style="margin:0 0 10px 0;color:#777;font-size:12px;">
            📰 {source} &nbsp;|&nbsp; 📅 {published[:22] if published else "—"}
            &nbsp;|&nbsp; 🏢 {org}
        </p>
        <div style="background:#f9f9f9;padding:10px;border-radius:4px;font-size:13px;color:#444;margin-bottom:10px;">
            {summary_raw}
        </div>
        <a href="{link}" style="display:inline-block;background:{color};color:white;padding:8px 16px;
                                border-radius:4px;text-decoration:none;font-size:13px;font-weight:bold;">
            🔗 פתח כתבה
        </a>
    </div>"""


def send_alert_email(alerts: list) -> None:
    if not alerts:
        return
    cards = "".join(_build_alert_card(a) for a in alerts)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    html = f"""<html><body style="background:#f0f0f0;padding:20px;font-family:Arial,sans-serif;">
    <div style="max-width:700px;margin:0 auto;">
        <div style="background:#cc0000;color:white;padding:16px 20px;border-radius:8px 8px 0 0;text-align:right;direction:rtl;">
            <h2 style="margin:0;">🔔 OSINTAgent — {len(alerts)} התרעות חדשות</h2>
            <p style="margin:4px 0 0;font-size:13px;opacity:.85;">{now}</p>
        </div>
        <div style="background:white;padding:20px;border-radius:0 0 8px 8px;">{cards}</div>
        <p style="text-align:center;color:#aaa;font-size:11px;margin-top:10px;">OSINTAgent | GitHub Actions</p>
    </div></body></html>"""
    _send_email(f"🔔 [OSINTAgent] {len(alerts)} התרעות חדשות", html)


# ── Summary Reports ───────────────────────────────────────────────────────────

def _build_summary_html(records: list, period_label: str, period_he: str) -> str:
    total = len(records)
    if total == 0:
        return f"<p>אין נתונים לתקופה: {period_he}</p>"

    alerts = [r for r in records if str(r.get("is_alert","")).upper() in ("YES","TRUE","1")]
    avg_score = sum(float(r.get("relevance_score",0)) for r in records) / total if total else 0

    event_counts = Counter(r.get("event_type","other") for r in records)
    location_counts = Counter(r.get("location","") for r in records if r.get("location"))
    org_counts = Counter(r.get("org_name","") for r in records if r.get("org_name"))

    # Top 10 by score
    top10 = sorted(records, key=lambda x: float(x.get("relevance_score",0)), reverse=True)[:10]
    top_rows = ""
    for r in top10:
        score = r.get("relevance_score", 0)
        color = _score_color(score)
        top_rows += f"""<tr>
            <td style="padding:6px;border-bottom:1px solid #eee;font-size:12px;">{r.get('timestamp','')[:16]}</td>
            <td style="padding:6px;border-bottom:1px solid #eee;font-size:12px;">
                <a href="{r.get('link','')}" style="color:#333;">{str(r.get('title',''))[:70]}...</a>
            </td>
            <td style="padding:6px;border-bottom:1px solid #eee;text-align:center;">
                <span style="background:{color};color:white;padding:2px 8px;border-radius:10px;font-size:12px;">{score}</span>
            </td>
            <td style="padding:6px;border-bottom:1px solid #eee;font-size:12px;">{EVENT_TYPE_HE.get(r.get('event_type','other'),'')}</td>
        </tr>"""

    event_rows = "".join(
        f"<tr><td style='padding:4px 8px;'>{EVENT_TYPE_HE.get(et,et)}</td>"
        f"<td style='padding:4px 8px;font-weight:bold;'>{cnt}</td></tr>"
        for et, cnt in event_counts.most_common()
    )
    loc_rows = "".join(
        f"<tr><td style='padding:4px 8px;'>{loc}</td>"
        f"<td style='padding:4px 8px;font-weight:bold;'>{cnt}</td></tr>"
        for loc, cnt in location_counts.most_common(10)
    )
    org_rows = "".join(
        f"<tr><td style='padding:4px 8px;'>{org}</td>"
        f"<td style='padding:4px 8px;font-weight:bold;'>{cnt}</td></tr>"
        for org, cnt in org_counts.most_common(10)
    )

    return f"""<html><body style="background:#f4f4f4;padding:20px;font-family:Arial,sans-serif;">
<div style="max-width:800px;margin:0 auto;">

  <!-- Header -->
  <div style="background:#1a1a2e;color:white;padding:20px;border-radius:8px 8px 0 0;direction:rtl;text-align:right;">
    <h1 style="margin:0;font-size:22px;">📊 OSINTAgent — דו"ח {period_he}</h1>
    <p style="margin:6px 0 0;opacity:.8;">תקופה: {period_label}</p>
  </div>

  <!-- KPIs -->
  <div style="background:white;padding:20px;display:flex;gap:16px;flex-wrap:wrap;direction:rtl;">
    {"".join(f'''<div style="background:#f8f8f8;border-radius:8px;padding:16px 24px;text-align:center;min-width:120px;">
      <div style="font-size:28px;font-weight:bold;color:{c};">{v}</div>
      <div style="font-size:12px;color:#666;">{lbl}</div></div>'''
      for v, lbl, c in [
          (total, "סה״כ ממצאים", "#333"),
          (len(alerts), "התרעות", "#cc0000"),
          (f"{avg_score:.1f}", "ציון ממוצע", "#e67e00"),
          (len(event_counts), "סוגי אירועים", "#2980b9"),
          (len(location_counts), "מיקומים", "#27ae60"),
      ])}
  </div>

  <!-- Top Articles -->
  <div style="background:white;padding:20px;margin-top:2px;direction:rtl;text-align:right;">
    <h3 style="margin:0 0 12px;border-bottom:2px solid #cc0000;padding-bottom:6px;">🔝 10 הכתבות הרלוונטיות ביותר</h3>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="background:#f0f0f0;font-weight:bold;font-size:12px;">
        <th style="padding:6px;text-align:right;">תאריך</th>
        <th style="padding:6px;text-align:right;">כותרת</th>
        <th style="padding:6px;text-align:center;">ציון</th>
        <th style="padding:6px;text-align:right;">סוג</th>
      </tr>
      {top_rows}
    </table>
  </div>

  <!-- Stats side by side -->
  <div style="display:flex;gap:2px;margin-top:2px;">
    <div style="background:white;padding:16px;flex:1;direction:rtl;text-align:right;">
      <h4 style="margin:0 0 8px;">סוגי אירועים</h4>
      <table style="width:100%;">{event_rows}</table>
    </div>
    <div style="background:white;padding:16px;flex:1;direction:rtl;text-align:right;">
      <h4 style="margin:0 0 8px;">מיקומים</h4>
      <table style="width:100%;">{loc_rows}</table>
    </div>
    <div style="background:white;padding:16px;flex:1;direction:rtl;text-align:right;">
      <h4 style="margin:0 0 8px;">ארגונים</h4>
      <table style="width:100%;">{org_rows}</table>
    </div>
  </div>

  <p style="text-align:center;color:#aaa;font-size:11px;margin-top:12px;">
    נוצר אוטומטית ע״י OSINTAgent
  </p>
</div></body></html>"""


def send_weekly_summary(records: list, week_label: str) -> None:
    html = _build_summary_html(records, week_label, "שבועי")
    _send_email(f"📊 [OSINTAgent] דו\"ח שבועי — {week_label}", html)
    print(f"[notifier] Weekly summary sent ({len(records)} records)")


def send_monthly_summary(records: list, month_label: str) -> None:
    html = _build_summary_html(records, month_label, "חודשי")
    _send_email(f"📊 [OSINTAgent] דו\"ח חודשי — {month_label}", html)
    print(f"[notifier] Monthly summary sent ({len(records)} records)")


def send_annual_summary(records: list, year: str) -> None:
    html = _build_summary_html(records, year, "שנתי")
    _send_email(f"📊 [OSINTAgent] דו\"ח שנתי — {year}", html)
    print(f"[notifier] Annual summary sent ({len(records)} records)")
