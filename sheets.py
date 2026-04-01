"""
sheets.py — Read organizations + keywords from Google Sheets and write results back.
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

ORG_SHEET      = "Organizations"
RESULTS_SHEET  = "Results"
KEYWORDS_SHEET = "Keywords"

RESULTS_HEADERS = [
    "timestamp", "org_name", "title", "link", "source", "published",
    "lang", "relevance_score", "event_type", "event_date", "location",
    "summary_he", "summary_en", "is_alert",
]

KEYWORDS_HEADERS = ["keyword", "weight", "active"]


def _get_client() -> gspread.Client:
    creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def load_organizations() -> list[dict]:
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


def load_keywords() -> dict:
    """
    Load keywords from the 'Keywords' sheet.
    Returns: {"high": [...], "medium": [...], "low": [...], "search_queries": [...]}
    """
    client = _get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    # Create sheet with defaults if it doesn't exist
    try:
        ws = spreadsheet.worksheet(KEYWORDS_SHEET)
    except gspread.WorksheetNotFound:
        ws = _create_default_keywords_sheet(spreadsheet)

    records = ws.get_all_records()

    high, medium, low, search_queries = [], [], [], []

    for row in records:
        keyword = str(row.get("keyword", "")).strip()
        weight  = str(row.get("weight", "2")).strip()
        active  = str(row.get("active", "TRUE")).strip().upper()

        if not keyword or active not in ("TRUE", "1", "YES"):
            continue

        w = int(weight) if weight.isdigit() else 2
        if w >= 3:
            high.append(keyword)
        elif w == 2:
            medium.append(keyword)
        else:
            low.append(keyword)

        # Also use as RSS search query
        search_queries.append(keyword)

    print(f"[sheets] Loaded {len(high)+len(medium)+len(low)} keywords "
          f"(high:{len(high)} medium:{len(medium)} low:{len(low)})")
    return {
        "high": high,
        "medium": medium,
        "low": low,
        "search_queries": search_queries,
    }


def _create_default_keywords_sheet(spreadsheet) -> gspread.Worksheet:
    """Create Keywords sheet with sensible defaults."""
    ws = spreadsheet.add_worksheet(title=KEYWORDS_SHEET, rows=200, cols=5)
    ws.append_row(KEYWORDS_HEADERS)

    defaults = [
        # weight 3 — high
        ["manifestación Israel", 3, "TRUE"],
        ["manifestación contra Israel", 3, "TRUE"],
        ["marcha contra Israel", 3, "TRUE"],
        ["marcha Palestina Perú", 3, "TRUE"],
        ["protesta Israel Lima", 3, "TRUE"],
        ["boicot Israel Perú", 3, "TRUE"],
        ["BDS Perú", 3, "TRUE"],
        ["antisemitismo Perú", 3, "TRUE"],
        ["against Israel Peru", 3, "TRUE"],
        ["protest Israel Peru", 3, "TRUE"],
        # weight 2 — medium
        ["solidaridad Palestina Perú", 2, "TRUE"],
        ["contra Israel Lima", 2, "TRUE"],
        ["Palestina Libre Lima", 2, "TRUE"],
        ["Free Palestine Peru", 2, "TRUE"],
        ["boicot Lima", 2, "TRUE"],
        ["huelga Israel", 2, "TRUE"],
        ["הפגנה פרו", 2, "TRUE"],
        ["boycott Lima", 2, "TRUE"],
        # weight 1 — low / informational
        ["Palestina Perú", 1, "TRUE"],
        ["Gaza Lima", 1, "TRUE"],
        ["Israel Lima noticias", 1, "TRUE"],
    ]
    ws.append_rows(defaults)
    print(f"[sheets] Created '{KEYWORDS_SHEET}' sheet with {len(defaults)} default keywords")
    return ws


def save_results(results: list[dict]) -> None:
    if not results:
        print("[sheets] No results to save")
        return

    client = _get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    try:
        ws = spreadsheet.worksheet(RESULTS_SHEET)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=RESULTS_SHEET, rows=1000, cols=len(RESULTS_HEADERS))

    existing = ws.get_all_values()
    if not existing:
        ws.append_row(RESULTS_HEADERS)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    rows = []
    for r in results:
        rows.append([
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
        ])

    ws.append_rows(rows, value_input_option='RAW', table_range='A1')
    print(f"[sheets] Saved {len(rows)} rows to '{RESULTS_SHEET}'")


def get_existing_links() -> set[str]:
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
