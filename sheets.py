"""
sheets.py — Google Sheets layer for OSINTAgent.
Handles all read/write operations across all tabs.
"""

import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

from config import (
    GOOGLE_SHEETS_CREDENTIALS_JSON, SPREADSHEET_ID,
    SHEET_ORGANIZATIONS, SHEET_RESULTS, SHEET_KEYWORDS,
    SHEET_SETTINGS, SHEET_SCAN_LOG,
    RESULTS_HEADERS, KEYWORDS_HEADERS, ORG_HEADERS,
    SETTINGS_HEADERS, SCAN_LOG_HEADERS,
    DEFAULT_COUNTRY, DEFAULT_COUNTRY_CODE, DEFAULT_LANGUAGES, ALERT_THRESHOLD,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

LIMA_TZ = timezone(timedelta(hours=-5))


# ── Client ────────────────────────────────────────────────────────────────────

def _get_client() -> gspread.Client:
    creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_or_create_sheet(spreadsheet, name: str, rows=1000, cols=20) -> gspread.Worksheet:
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=name, rows=rows, cols=cols)
        return ws


# ── Settings ──────────────────────────────────────────────────────────────────

def load_settings() -> dict:
    """Load runtime settings from Settings sheet. Falls back to defaults."""
    defaults = {
        "country":       DEFAULT_COUNTRY,
        "country_code":  DEFAULT_COUNTRY_CODE,
        "languages":     ",".join(DEFAULT_LANGUAGES),
        "alert_threshold": str(ALERT_THRESHOLD),
        "ui_language":   "he",
        "email_alerts":  "true",
        "weekly_summary": "true",
        "monthly_summary":"true",
    }
    try:
        client = _get_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        ws = _get_or_create_sheet(spreadsheet, SHEET_SETTINGS, rows=50, cols=3)
        records = ws.get_all_records()
        if not records:
            # Write defaults
            ws.append_row(SETTINGS_HEADERS)
            for k, v in defaults.items():
                ws.append_row([k, v])
            return defaults
        return {str(r["key"]): str(r["value"]) for r in records if r.get("key")}
    except Exception as e:
        print(f"[sheets] Settings load failed, using defaults: {e}")
        return defaults


def save_setting(key: str, value: str) -> None:
    client = _get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    ws = _get_or_create_sheet(spreadsheet, SHEET_SETTINGS, rows=50, cols=3)
    records = ws.get_all_records()
    for i, row in enumerate(records, start=2):
        if str(row.get("key")) == key:
            ws.update_cell(i, 2, value)
            return
    ws.append_row([key, value])


# ── Organizations ─────────────────────────────────────────────────────────────

def load_organizations(active_only=True) -> list[dict]:
    client = _get_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_ORGANIZATIONS)
    records = sheet.get_all_records()
    orgs = []
    for row in records:
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        active = str(row.get("active", "TRUE")).strip().upper()
        if active_only and active not in ("TRUE", "1", "YES", ""):
            continue
        keywords_raw = str(row.get("keywords", ""))
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        orgs.append({
            "name":     name,
            "platform": str(row.get("platform", "")),
            "url":      str(row.get("url", "")),
            "keywords": keywords,
            "country":  str(row.get("country", "")),
            "notes":    str(row.get("notes", "")),
            "active":   active,
        })
    print(f"[sheets] Loaded {len(orgs)} organizations")
    return orgs


def save_organization(org: dict) -> None:
    client = _get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    ws = spreadsheet.worksheet(SHEET_ORGANIZATIONS)
    existing = ws.get_all_records()
    # Check if exists by name
    for i, row in enumerate(existing, start=2):
        if str(row.get("name")) == org["name"]:
            ws.update(f"A{i}:G{i}", [[
                org.get("name",""), org.get("platform",""), org.get("url",""),
                org.get("keywords",""), org.get("country",""),
                org.get("notes",""), org.get("active","TRUE"),
            ]])
            return
    ws.append_row([
        org.get("name",""), org.get("platform",""), org.get("url",""),
        org.get("keywords",""), org.get("country",""),
        org.get("notes",""), org.get("active","TRUE"),
    ])


def delete_organization(name: str) -> None:
    client = _get_client()
    ws = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_ORGANIZATIONS)
    records = ws.get_all_records()
    for i, row in enumerate(records, start=2):
        if str(row.get("name")) == name:
            ws.delete_rows(i)
            return


# ── Keywords ──────────────────────────────────────────────────────────────────

def load_keywords() -> dict:
    client = _get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    try:
        ws = spreadsheet.worksheet(SHEET_KEYWORDS)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=SHEET_KEYWORDS, rows=200, cols=5)
        ws.append_row(KEYWORDS_HEADERS)

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
        search_queries.append(keyword)

    print(f"[sheets] Keywords: high={len(high)} medium={len(medium)} low={len(low)}")
    return {"high": high, "medium": medium, "low": low, "search_queries": search_queries}


def save_keyword(keyword: str, weight: int, active: bool) -> None:
    client = _get_client()
    ws = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_KEYWORDS)
    records = ws.get_all_records()
    for i, row in enumerate(records, start=2):
        if str(row.get("keyword")) == keyword:
            ws.update(f"A{i}:C{i}", [[keyword, weight, "TRUE" if active else "FALSE"]])
            return
    ws.append_row([keyword, weight, "TRUE" if active else "FALSE"])


def delete_keyword(keyword: str) -> None:
    client = _get_client()
    ws = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_KEYWORDS)
    records = ws.get_all_records()
    for i, row in enumerate(records, start=2):
        if str(row.get("keyword")) == keyword:
            ws.delete_rows(i)
            return


# ── Results ───────────────────────────────────────────────────────────────────

def load_results(days_back=90) -> list[dict]:
    client = _get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    try:
        ws = spreadsheet.worksheet(SHEET_RESULTS)
    except gspread.WorksheetNotFound:
        return []
    records = ws.get_all_records()
    return records


def save_results(results: list[dict]) -> None:
    if not results:
        return
    client = _get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    ws = _get_or_create_sheet(spreadsheet, SHEET_RESULTS)
    existing = ws.get_all_values()
    if not existing:
        ws.append_row(RESULTS_HEADERS)

    timestamp = datetime.now(LIMA_TZ).strftime("%Y-%m-%d %H:%M (Lima)")
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
    print(f"[sheets] Saved {len(rows)} results")


def load_rated_results(min_stars: int = 4) -> list:
    """Return Results rows where rating >= min_stars."""
    try:
        client = _get_client()
        ws = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_RESULTS)
        records = ws.get_all_records()
    except Exception as e:
        print(f"[sheets] load_rated_results failed: {e}")
        return []
    out = []
    for r in records:
        raw = r.get("rating", "")
        try:
            rating = int(raw) if str(raw).strip() else 0
        except (ValueError, TypeError):
            rating = 0
        if rating >= min_stars:
            out.append(r)
    print(f"[sheets] load_rated_results(min={min_stars}) → {len(out)}")
    return out


def load_low_rated_results(max_stars: int = 2) -> list:
    """Return Results rows where 0 < rating <= max_stars (ignores unrated)."""
    try:
        client = _get_client()
        ws = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_RESULTS)
        records = ws.get_all_records()
    except Exception as e:
        print(f"[sheets] load_low_rated_results failed: {e}")
        return []
    out = []
    for r in records:
        raw = r.get("rating", "")
        try:
            rating = int(raw) if str(raw).strip() else 0
        except (ValueError, TypeError):
            rating = 0
        if 0 < rating <= max_stars:
            out.append(r)
    print(f"[sheets] load_low_rated_results(max={max_stars}) → {len(out)}")
    return out


def get_existing_links() -> set:
    client = _get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    try:
        ws = spreadsheet.worksheet(SHEET_RESULTS)
        all_values = ws.get_all_values()
        if len(all_values) <= 1:
            return set()
        link_col = RESULTS_HEADERS.index("link")
        return {row[link_col] for row in all_values[1:] if len(row) > link_col}
    except gspread.WorksheetNotFound:
        return set()


# ── Scan Log ──────────────────────────────────────────────────────────────────

def log_scan(status: str, fetched: int, relevant: int, alerts: int,
             duration_sec: float, notes: str = "") -> None:
    client = _get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    ws = _get_or_create_sheet(spreadsheet, SHEET_SCAN_LOG, rows=500, cols=8)
    existing = ws.get_all_values()
    if not existing:
        ws.append_row(SCAN_LOG_HEADERS)
    timestamp = datetime.now(LIMA_TZ).strftime("%Y-%m-%d %H:%M (Lima)")
    ws.append_row([timestamp, status, fetched, relevant, alerts,
                   round(duration_sec, 1), notes])
