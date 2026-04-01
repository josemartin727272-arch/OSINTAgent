"""
sheets.py — Read organizations from Google Sheets and write results back.
"""

import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

from config import GOOGLE_SHEETS_CREDENTIALS_JSON, SPREADSHEET_ID

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Sheet tab names
ORG_SHEET = "Organizations"
RESULTS_SHEET = "Results"

RESULTS_HEADERS = [
    "timestamp", "org_name", "title", "link", "source", "published",
    "lang", "relevance_score", "event_type", "event_date", "location",
    "summary_he", "summary_en", "is_alert",
]


def _get_client() -> gspread.Client:
    creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def load_organizations() -> list[dict]:
    """
    Load organizations from the 'Organizations' sheet.
    Expected columns: name, keywords, country, notes
    """
    client = _get_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(ORG_SHEET)
    records = sheet.get_all_records()

    orgs = []
    for row in records:
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        keywords_raw = str(row.get("keywords", ""))
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        orgs.append({
            "name": name,
            "keywords": keywords,
            "country": str(row.get("country", "")).strip(),
            "notes": str(row.get("notes", "")).strip(),
        })

    print(f"[sheets] Loaded {len(orgs)} organizations")
    return orgs


def save_results(results: list[dict]) -> None:
    """
    Append analyzed articles to the 'Results' sheet.
    Creates headers if the sheet is empty.
    """
    if not results:
        print("[sheets] No results to save")
        return

    client = _get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    try:
        ws = spreadsheet.worksheet(RESULTS_SHEET)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=RESULTS_SHEET, rows=1000, cols=len(RESULTS_HEADERS))

    # Add headers if sheet is empty
    existing = ws.get_all_values()
    if not existing:
        ws.append_row(RESULTS_HEADERS)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    rows = []
    for r in results:
        row = [
            timestamp,
            r.get("org_name", ""),
            r.get("title", ""),
            r.get("link", ""),
            r.get("source", ""),
            r.get("published", ""),
            r.get("lang", ""),
            r.get("relevance_score", 0),
            r.get("event_type", ""),
            r.get("event_date") or "",
            r.get("location") or "",
            r.get("summary_he", ""),
            r.get("summary_en", ""),
            "YES" if r.get("is_alert") else "no",
        ]
        rows.append(row)

    ws.append_rows(rows)
    print(f"[sheets] Saved {len(rows)} rows to '{RESULTS_SHEET}'")


def get_existing_links() -> set[str]:
    """Return set of article links already saved, to avoid duplicates."""
    client = _get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    try:
        ws = spreadsheet.worksheet(RESULTS_SHEET)
        all_values = ws.get_all_values()
        if len(all_values) <= 1:
            return set()
        link_col = RESULTS_HEADERS.index("link")
        return {row[link_col] for row in all_values[1:] if len(row) > link_col}
    except gspread.WorksheetNotFound:
        return set()
