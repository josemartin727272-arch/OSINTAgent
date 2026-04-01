"""
Central configuration for OSINTAgent.
All secrets are loaded from environment variables (GitHub Actions Secrets).
"""

import os

# --- API Keys ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# --- Google Sheets ---
GOOGLE_SHEETS_CREDENTIALS_JSON = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON", "")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")

# --- Email Alerts ---
ALERT_EMAIL_FROM = os.environ.get("ALERT_EMAIL_FROM", "")
ALERT_EMAIL_TO = os.environ.get("ALERT_EMAIL_TO", "")
ALERT_EMAIL_PASSWORD = os.environ.get("ALERT_EMAIL_PASSWORD", "")  # Gmail App Password

# --- Scan Settings ---
LANGUAGES = ["he", "en", "es"]  # Hebrew, English, Spanish
COUNTRY = "Peru"
COUNTRY_CODE = "PE"

# Keywords that increase relevance score when found in articles
ALERT_KEYWORDS = [
    # Spanish
    "manifestación", "protesta", "marcha", "concentración", "huelga",
    "boicot", "antisemitismo", "contra Israel", "pro palestina",
    # English
    "protest", "demonstration", "rally", "march", "boycott",
    "antisemitism", "against Israel", "pro Palestine", "BDS",
    # Hebrew
    "הפגנה", "מחאה", "אנטישמיות", "חרם", "נגד ישראל",
]

# Google News RSS base URL
GOOGLE_NEWS_RSS_TEMPLATE = (
    "https://news.google.com/rss/search?q={query}&hl={lang}&gl={country}&ceid={country}:{lang}"
)

# How many past hours to look back for new articles
LOOKBACK_HOURS = 6

# Minimum Gemini relevance score (0-10) to trigger an alert
ALERT_THRESHOLD = 6
