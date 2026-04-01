"""
import_this_excel.py — Custom importer for BASE DE DATOS 2025.xlsx
Imports Instagram and Facebook GROUPS only (no private individuals).
Run: python import_this_excel.py
"""

import json
import os
import openpyxl
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

ORG_SHEET = "Organizations"
ORG_HEADERS = ["name", "platform", "url", "keywords", "country", "notes"]

EXCEL_PATH = os.path.expanduser("~/Downloads/BASE DE DATOS 2025.xlsx")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
GOOGLE_SHEETS_CREDENTIALS_JSON = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON", "")


def get_client():
    creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def clean(val):
    if val is None:
        return ""
    return str(val).strip()


def import_orgs():
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    organizations = []

    # --- Instagram Groups (column index 1 = B, rows 9-22 approx) ---
    print("Reading Instagram groups...")
    for row in rows[8:25]:  # rows 9-25
        url = clean(row[1] if len(row) > 1 else "")   # col B - URL
        name = clean(row[4] if len(row) > 4 else "")  # col E - Name
        activity = clean(row[10] if len(row) > 10 else "")  # col K - Activity

        if not url and not name:
            continue
        display_name = name if name else url.replace("https://www.instagram.com/", "@")
        organizations.append([
            display_name,
            "Instagram",
            url,
            "protesta,manifestación,boicot,BDS,Israel,Palestina",
            "Peru",
            activity,
        ])

    # --- Facebook Groups (column index 14 = O, rows 9-17 approx) ---
    print("Reading Facebook groups...")
    for row in rows[8:20]:  # rows 9-20
        url = clean(row[14] if len(row) > 14 else "")   # col O - URL
        name = clean(row[17] if len(row) > 17 else "")  # col R - Name
        activity = clean(row[20] if len(row) > 20 else "")  # col U - Activity

        if not url and not name:
            continue
        display_name = name if name else url
        organizations.append([
            display_name,
            "Facebook",
            url,
            "protesta,manifestación,boicot,BDS,Israel,Palestina",
            "Peru",
            activity,
        ])

    print(f"\nTotal organizations to import: {len(organizations)}")
    for o in organizations:
        print(f"  [{o[1]}] {o[0]}")

    # --- Upload to Google Sheets ---
    client = get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    try:
        org_sheet = spreadsheet.worksheet(ORG_SHEET)
        org_sheet.clear()
        print(f"\nCleared existing '{ORG_SHEET}' sheet")
    except gspread.WorksheetNotFound:
        org_sheet = spreadsheet.add_worksheet(title=ORG_SHEET, rows=200, cols=10)
        print(f"\nCreated '{ORG_SHEET}' sheet")

    org_sheet.append_row(ORG_HEADERS)
    org_sheet.append_rows(organizations)

    print(f"Imported {len(organizations)} organizations to Google Sheets!")
    print(f"View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")


if __name__ == "__main__":
    import_orgs()
