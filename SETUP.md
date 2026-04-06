# OSINTAgent — Setup Guide

## Files Structure
```
OSINTAgent/
├── dashboard.py          ← Streamlit app (5 pages)
├── main.py               ← Scan entry point
├── scanner.py            ← Google News RSS fetcher
├── analyzer.py           ← Keyword scoring
├── notifier.py           ← Email alerts + summaries
├── sheets.py             ← Google Sheets layer
├── summary_runner.py     ← Periodic report sender
├── config.py             ← Config + constants
├── requirements.txt
└── .github/workflows/
    ├── osint_scan.yml    ← 5x/day scan
    ├── osint_summary.yml ← Weekly summary (Sunday 18:00 Lima)
    └── osint_monthly.yml ← Monthly summary (1st of month)
```

## GitHub Secrets Required
Go to: `Settings → Secrets and variables → Actions → New repository secret`

| Secret Name | Value |
|---|---|
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | Full JSON of service account |
| `SPREADSHEET_ID` | `1LP4rVIihIe0tpusUU8uEW-pVb2wLqiF7lG84ihMkTck` |
| `ALERT_EMAIL_FROM` | your@gmail.com |
| `ALERT_EMAIL_TO` | recipient@gmail.com |
| `ALERT_EMAIL_PASSWORD` | Gmail App Password (not your real password) |
| `GEMINI_API_KEY` | (optional — not used in current version) |

## Streamlit Cloud Deploy
1. Go to https://share.streamlit.io
2. New app → `Ambroseius/OSINTAgent` → branch: `main` → `dashboard.py`
3. Advanced → Secrets:
```toml
GOOGLE_SHEETS_CREDENTIALS_JSON = '''{ ... paste full JSON here ... }'''
SPREADSHEET_ID = "1LP4rVIihIe0tpusUU8uEW-pVb2wLqiF7lG84ihMkTck"
ALERT_EMAIL_FROM = "your@gmail.com"
ALERT_EMAIL_TO = "recipient@gmail.com"
ALERT_EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx"
```

## Scan Schedule (Peru Time / Lima UTC-5)
| Time Lima | Time UTC | Workflow |
|---|---|---|
| 07:00 | 12:00 | Scan |
| 10:00 | 15:00 | Scan |
| 13:00 | 18:00 | Scan |
| 16:00 | 21:00 | Scan |
| 19:00 | 00:00 | Scan |
| Sunday 18:00 | Sunday 23:00 | Weekly Summary Email |
| 1st of month 18:00 | 1st 23:00 | Monthly Summary Email |

## Dashboard Pages
1. **🚨 Findings** — All results with filters (score, event type, location, alerts only)
2. **🏢 Organizations** — Add/delete monitored orgs per country
3. **🔑 Keywords** — Add/toggle/delete keywords with weights (1/2/3)
4. **⚙️ Settings** — Change country, scan languages, alert threshold, email on/off
5. **📊 Reports** — Charts, top findings, send email summary manually

## Changing Country
In the dashboard → Settings → select country from dropdown.
This updates Google Sheets (Settings tab) and all future scans use the new country.

## Adding Languages
Settings → Scan Languages → check boxes.
Supports: Hebrew, English, Spanish, Arabic, French, Portuguese, German.

## UI Language
Top of sidebar: 3 buttons — עברית / English / Español
