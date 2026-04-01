"""
import_excel.py — One-time script to import organizations from Excel into Google Sheets.
Run locally: python import_excel.py organizations.xlsx
"""

import sys
import json
import openpyxl
import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_SHEETS_CREDENTIALS_JSON, SPREADSHEET_ID

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

ORG_SHEET = "Organizations"
ORG_HEADERS = ["name", "keywords", "country", "notes"]


def import_excel(filepath: str):
    print(f"Reading Excel: {filepath}")
    wb = openpyxl.load_workbook(filepath)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        print("Excel file is empty.")
        return

    # Auto-detect header row
    headers = [str(h).strip().lower() if h else "" for h in rows[0]]
    print(f"Excel headers: {headers}")
    data_rows = rows[1:]

    # Connect to Google Sheets
    creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    try:
        org_sheet = spreadsheet.worksheet(ORG_SHEET)
        print(f"Sheet '{ORG_SHEET}' already exists — clearing and re-importing")
        org_sheet.clear()
    except gspread.WorksheetNotFound:
        org_sheet = spreadsheet.add_worksheet(title=ORG_SHEET, rows=500, cols=10)
        print(f"Created sheet '{ORG_SHEET}'")

    # Write headers
    org_sheet.append_row(ORG_HEADERS)

    # Map Excel columns to our schema
    # Expected Excel columns (flexible mapping):
    # name/organization/ארגון, keywords/מילות מפתח, country/מדינה, notes/הערות
    name_col = next((i for i, h in enumerate(headers) if h in ["name", "organization", "ארגון", "שם"]), 0)
    kw_col = next((i for i, h in enumerate(headers) if h in ["keywords", "מילות מפתח", "tags"]), None)
    country_col = next((i for i, h in enumerate(headers) if h in ["country", "מדינה", "страна"]), None)
    notes_col = next((i for i, h in enumerate(headers) if h in ["notes", "הערות", "comments"]), None)

    batch = []
    skipped = 0
    for row in data_rows:
        name = str(row[name_col]).strip() if row[name_col] else ""
        if not name or name.lower() == "none":
            skipped += 1
            continue

        keywords = str(row[kw_col]).strip() if kw_col is not None and row[kw_col] else ""
        country = str(row[country_col]).strip() if country_col is not None and row[country_col] else "Peru"
        notes = str(row[notes_col]).strip() if notes_col is not None and row[notes_col] else ""

        batch.append([name, keywords, country, notes])

    org_sheet.append_rows(batch)
    print(f"\nImported {len(batch)} organizations (skipped {skipped} empty rows)")
    print(f"View your sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_excel.py <path_to_excel.xlsx>")
        sys.exit(1)
    import_excel(sys.argv[1])
