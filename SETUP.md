# OSINTAgent — מדריך הקמה

## שלב 1 — Gemini API Key (חינמי)

1. כנס ל-https://aistudio.google.com
2. לחץ **"Get API Key"** → **"Create API key"**
3. שמור את ה-key — תצטרך אותו בשלב 4

---

## שלב 2 — Google Sheets Service Account

1. כנס ל-https://console.cloud.google.com
2. צור פרויקט חדש (שם לדוגמה: `osint-agent`)
3. הפעל את ה-APIs הבאים:
   - **Google Sheets API**
   - **Google Drive API**
4. לך ל-**IAM & Admin → Service Accounts**
5. צור Service Account חדש (שם: `osint-sheets`)
6. לך ל-**Keys → Add Key → JSON** — הורד את קובץ ה-JSON
7. שמור את כל התוכן של ה-JSON — תצטרך אותו בשלב 4

---

## שלב 3 — Google Sheets

1. צור Google Spreadsheet חדש
2. שנה את שם ה-tab הראשון ל: `Organizations`
3. **שתף את ה-Spreadsheet** עם כתובת האימייל של ה-Service Account
   (נמצאת בקובץ ה-JSON בשדה `client_email`) — תן הרשאת **Editor**
4. העתק את ה-**Spreadsheet ID** מה-URL:
   `https://docs.google.com/spreadsheets/d/**SPREADSHEET_ID**/edit`

---

## שלב 4 — Gmail App Password

1. כנס לחשבון Gmail של הפרויקט
2. לך ל: Google Account → Security → **2-Step Verification** (הפעל אם כבול)
3. חפש **"App Passwords"** → צור סיסמה לאפליקציה "Mail"
4. שמור את ה-16 ספרות

---

## שלב 5 — GitHub Repository

1. צור repo חדש ב-GitHub (שם: `OSINTAgent`, Private)
2. לך ל-**Settings → Secrets and variables → Actions**
3. הוסף את ה-Secrets הבאים:

| Secret Name | ערך |
|-------------|-----|
| `GEMINI_API_KEY` | ה-key משלב 1 |
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | כל תוכן קובץ ה-JSON משלב 2 |
| `SPREADSHEET_ID` | ה-ID משלב 3 |
| `ALERT_EMAIL_FROM` | כתובת Gmail של הפרויקט |
| `ALERT_EMAIL_TO` | כתובת המייל לקבלת התרעות |
| `ALERT_EMAIL_PASSWORD` | App Password משלב 4 |

---

## שלב 6 — ייבוא קובץ ה-Excel

```bash
cd ~/OSINTAgent
pip install -r requirements.txt

# הכנס את ה-credentials זמנית לסביבה המקומית
export GOOGLE_SHEETS_CREDENTIALS_JSON='<תוכן ה-JSON>'
export SPREADSHEET_ID='<ה-ID שלך>'

# ייבא את ה-Excel
python import_excel.py /path/to/your/organizations.xlsx
```

---

## שלב 7 — Push ל-GitHub

```bash
cd ~/OSINTAgent
git init
git add .
git commit -m "Initial OSINTAgent setup"
git remote add origin https://github.com/<username>/OSINTAgent.git
git push -u origin main
```

GitHub Actions יתחיל לרוץ אוטומטית 5 פעמים ביום.
ניתן להריץ ידנית: **Actions → OSINTAgent Scan → Run workflow**

---

## מבנה הקבצים

```
OSINTAgent/
├── main.py              # נקודת כניסה ראשית
├── scanner.py           # סריקת Google News RSS
├── analyzer.py          # ניתוח Gemini API
├── sheets.py            # קריאה/כתיבה Google Sheets
├── notifier.py          # שליחת מייל
├── config.py            # הגדרות מרכזיות
├── import_excel.py      # ייבוא חד-פעמי מ-Excel
├── requirements.txt
└── .github/
    └── workflows/
        └── scan.yml     # GitHub Actions (5x/day)
```
