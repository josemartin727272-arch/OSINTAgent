# OSINTAgent — תיאור המערכת

## מה זה?
סוכן OSINT אוטומטי שסורק חדשות ציבוריות על **ארגונים וקבוצות** הפועלים נגד ישראל / פרו-פלסטיניים בפרו.
המערכת מיועדת להתראה מוקדמת על הפגנות, חרמות, קמפיינים וכד'.

**חשוב:** המערכת עוקבת אחר **ארגונים וקבוצות בלבד** — לא אחר אנשים פרטיים.

---

## ארכיטקטורה

```
main.py → scanner.py → Google News RSS
       → analyzer.py → ניקוד מילות מפתח (0-10)
       → sheets.py   → Google Sheets (קריאה + שמירה)
       → notifier.py → מייל HTML בעברית
```

### קבצים עיקריים
| קובץ | תפקיד |
|------|--------|
| `config.py` | הגדרות מרכזיות, טעינת סודות מ-env |
| `scanner.py` | שליפת כתבות מ-Google News RSS |
| `analyzer.py` | ניקוד כתבות לפי מילות מפתח |
| `sheets.py` | קריאת ארגונים/מילות מפתח, שמירת תוצאות |
| `notifier.py` | שליחת מייל התראה בעברית |
| `main.py` | נקודת כניסה — מריץ את הכל |
| `import_this_excel.py` | ייבא 23 ארגונים מקובץ BASE DE DATOS 2025.xlsx |

---

## Google Sheets (Spreadsheet ID: 1LP4rVIihIe0tpusUU8uEW-pVb2wLqiF7lG84ihMkTck)

### גיליונות:
- **Organizations** — רשימת ארגונים לניטור (עמודות: name, keywords, country, notes)
- **Keywords** — מילות חיפוש ומשקלות (עמודות: keyword, weight, active)
  - weight=3 → high (×3 נקודות)
  - weight=2 → medium (×2 נקודות)
  - weight=1 → low (×1 נקודה)
  - active=TRUE/FALSE — להפעיל/לכבות מילה בלי למחוק
- **Results** — תוצאות הסריקה (14 עמודות, שעון לימה UTC-5)

### הוספת מילת חיפוש חדשה:
פשוט להוסיף שורה בגיליון Keywords — **לא צריך לשנות קוד**.

---

## הגדרות עיקריות (config.py)
- `LOOKBACK_HOURS = 48` — כמה שעות אחורה לחפש
- `ALERT_THRESHOLD = 6` — ציון מינימלי לשליחת התראה (0-10)
- `LANGUAGES = ["he", "en", "es"]` — עברית, אנגלית, ספרדית
- `COUNTRY = "Peru"`, `COUNTRY_CODE = "PE"`

---

## GitHub Actions (.github/workflows/scan.yml)
רץ אוטומטית **5 פעמים ביום**: 06:00, 10:00, 14:00, 18:00, 22:00 UTC
(= 01:00, 05:00, 09:00, 13:00, 17:00 שעון לימה)

### Secrets שמוגדרים ב-GitHub:
- `GEMINI_API_KEY`
- `GOOGLE_SHEETS_CREDENTIALS_JSON` — JSON של service account (פרויקט os111-492000)
- `SPREADSHEET_ID`
- `ALERT_EMAIL_FROM` / `ALERT_EMAIL_TO` / `ALERT_EMAIL_PASSWORD`

---

## ניקוד כתבות (analyzer.py)
- high keywords × 3
- medium keywords × 2
- low keywords × 1
- בונוס פרו: +2 אם מוזכרת פרו בכתבה
- ציון מקסימלי: 10
- סף התראה: 6

### זיהוי אוטומטי:
- **סוג אירוע**: הפגנה / חרם / אלים / קמפיין ברשת / הצהרה
- **מיקום**: לימה / קוסקו / ארקיפה / טרוחיו ועוד

---

## מייל התראה (notifier.py)
- HTML בעברית
- כרטיסיה לכל כתבה: ציון, סוג אירוע, מיקום, כותרת עם קישור, מקור, תאריך, סיכום
- צבע: אדום ≥8, כתום ≥6
- נשלח ל: Josemartin727272@gmail.com

---

## הרצה ידנית (לוקאלית)
```bash
cd /Users/adilevy/OSINTAgent
python3 main.py
```

### ניקוי וריצה מחדש:
```python
# מחיקת גיליון Results והרצה מחדש
python3 -c "
from sheets import _get_client, SPREADSHEET_ID, RESULTS_SHEET, RESULTS_HEADERS
client = _get_client()
ws = client.open_by_key(SPREADSHEET_ID).worksheet(RESULTS_SHEET)
ws.clear()
ws.append_row(RESULTS_HEADERS)
"
python3 main.py
```

---

## GitHub
- Repo: `https://github.com/josemartin727272-arch/OSINTAgent`
- Branch: `main`

---

## בעיות שנפתרו בעבר
1. **Gemini API quota=0** → עברנו לניקוד מילות מפתח בלבד (ללא AI)
2. **Scanner 0 articles** → עברנו לחיפוש לפי נושאים (לא usernames)
3. **Python 3.9 str|None** → הסרנו type hints לא תואמים
4. **load_dotenv חסר** → הוספנו ל-config.py
5. **Results עמודות לא נכונות** → תוקן עם `table_range='A1'` ב-append_rows
6. **שעון UTC במקום לימה** → תוקן ל-UTC-5 עם תווית "(Lima)"
