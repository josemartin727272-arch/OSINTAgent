"""
config.py — OSINTAgent central configuration.
Secrets from environment variables. UI settings stored in Google Sheets (Settings tab).
"""

import os
from dotenv import load_dotenv
load_dotenv()

# ── Secrets (env / GitHub Actions Secrets) ──────────────────────────────────
GEMINI_API_KEY               = os.environ.get("GEMINI_API_KEY", "")
GOOGLE_SHEETS_CREDENTIALS_JSON = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON", "")
SPREADSHEET_ID               = os.environ.get("SPREADSHEET_ID", "1LP4rVIihIe0tpusUU8uEW-pVb2wLqiF7lG84ihMkTck")
ALERT_EMAIL_FROM             = os.environ.get("ALERT_EMAIL_FROM", "")
ALERT_EMAIL_TO               = os.environ.get("ALERT_EMAIL_TO", "")
ALERT_EMAIL_PASSWORD         = os.environ.get("ALERT_EMAIL_PASSWORD", "")

# ── Defaults (can be overridden from Settings sheet) ────────────────────────
DEFAULT_COUNTRY      = "Peru"
DEFAULT_COUNTRY_CODE = "PE"
DEFAULT_LANGUAGES    = ["es", "en", "he"]   # Spanish, English, Hebrew
ALERT_THRESHOLD      = 6
LOOKBACK_HOURS       = 48

# ── Sheet tab names ──────────────────────────────────────────────────────────
SHEET_ORGANIZATIONS = "Organizations"
SHEET_RESULTS       = "Results"
SHEET_KEYWORDS      = "Keywords"
SHEET_SETTINGS      = "Settings"
SHEET_SCAN_LOG      = "ScanLog"

# ── Supported UI languages ───────────────────────────────────────────────────
UI_LANGUAGES = {
    "עברית":   "he",
    "English": "en",
    "Español": "es",
}

# ── Supported scan languages ─────────────────────────────────────────────────
SCAN_LANGUAGES = {
    "עברית (he)":   "he",
    "English (en)": "en",
    "Español (es)": "es",
    "Arabic (ar)":  "ar",
    "Français (fr)":"fr",
    "Deutsch (de)": "de",
    "Português (pt)":"pt",
}

# ── Country presets ──────────────────────────────────────────────────────────
COUNTRY_PRESETS = {
    "Peru":          "PE",
    "Argentina":     "AR",
    "Chile":         "CL",
    "Colombia":      "CO",
    "Mexico":        "MX",
    "Brazil":        "BR",
    "Spain":         "ES",
    "United States": "US",
    "United Kingdom":"GB",
    "Germany":       "DE",
    "France":        "FR",
    "Custom":        "",
}

RESULTS_HEADERS = [
    "timestamp", "org_name", "title", "link", "source", "published",
    "lang", "relevance_score", "event_type", "event_date", "location",
    "summary_he", "summary_en", "is_alert", "is_global",
]

KEYWORDS_HEADERS = ["keyword", "weight", "active"]
ORG_HEADERS      = ["name", "platform", "url", "keywords", "country", "notes", "active"]
SETTINGS_HEADERS = ["key", "value"]
SCAN_LOG_HEADERS = ["timestamp", "status", "fetched", "relevant", "alerts", "duration_sec", "notes"]
