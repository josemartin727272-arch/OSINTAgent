"""
dashboard.py — OSINTAgent Streamlit Dashboard
Pages: Findings | Organizations | Keywords | Settings | Reports
"""

import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
import os

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OSINTAgent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constants ────────────────────────────────────────────────────────────────
SPREADSHEET_ID = "1LP4rVIihIe0tpusUU8uEW-pVb2wLqiF7lG84ihMkTck"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

# UI text in 3 languages
UI_TEXT = {
    "he": {
        "title":         "🔍 OSINTAgent",
        "subtitle":      "ניטור פעילות אנטי-ישראלית",
        "page_findings": "🚨 ממצאים",
        "page_orgs":     "🏢 ארגונים ומקורות",
        "page_keywords": "🔑 מילות מפתח",
        "page_settings": "⚙️ הגדרות",
        "page_reports":  "📊 דוחות",
        "loading":       "טוען נתונים...",
        "no_data":       "אין נתונים",
        "score":         "ציון",
        "date":          "תאריך",
        "title_col":     "כותרת",
        "source":        "מקור",
        "event_type":    "סוג אירוע",
        "location":      "מיקום",
        "org":           "ארגון",
        "alert":         "התרעה",
        "filters":       "סינון",
        "all":           "הכל",
        "add":           "הוסף",
        "delete":        "מחק",
        "save":          "שמור",
        "cancel":        "ביטול",
        "edit":          "עריכה",
        "name":          "שם",
        "platform":      "פלטפורמה",
        "url":           "כתובת URL",
        "keywords":      "מילות מפתח",
        "country":       "מדינה",
        "notes":         "הערות",
        "active":        "פעיל",
        "weight":        "משקל",
        "send_report":   "שלח דוח",
        "weekly":        "שבועי",
        "monthly":       "חודשי",
        "annual":        "שנתי",
        "total":         "סה״כ",
        "alerts_count":  "התרעות",
        "avg_score":     "ציון ממוצע",
        "last_scan":     "סריקה אחרונה",
        "scan_status":   "סטטוס",
        "settings_saved":"הגדרות נשמרו ✅",
        "country_setting":"מדינה לניטור",
        "lang_setting":  "שפות סריקה",
        "threshold_setting": "סף התרעה",
        "email_alerts":  "שליחת התרעות למייל",
        "ui_language":   "שפת ממשק",
        "summary_weekly":"דוח שבועי אוטומטי",
        "summary_monthly":"דוח חודשי אוטומטי",
        "page_home":           "🏠 דף בית",
        "page_review":         "✍️ תור דירוג",
        "page_feed":           "📰 חדשות מסוננות",
        "page_global":         "🌍 אירועים גלובליים",
        "page_admin":          "⚙️ ניהול",
        "tab_orgs":            "🏢 ארגונים",
        "tab_keywords":        "🔑 מילות מפתח",
        "tab_settings":        "⚙️ הגדרות",
        "tab_reports":         "📊 דוחות",
        "critical_alerts":     "🔴 התרעות קריטיות",
        "regular_alerts":      "🟠 התרעות רגילות",
        "total_week":          "📰 כתבות השבוע",
        "top10_title":         "🔝 10 הידיעות הרלוונטיות ביותר",
        "geo_map_title":       "🗺️ פריסה גיאוגרפית — פרו",
        "lima_map_title":      "📍 לימה — רמת שכונה",
        "review_queue_title":  "✍️ תור דירוג",
        "pending_count":       "נותרו {n} כתבות לדירוג",
        "rated_today":         "דורגו היום: {done}/{total}",
        "skip":                "דלג ⏭",
        "no_pending":          "✅ אין כתבות לדירוג כרגע",
        "feed_title":          "📰 חדשות מסוננות",
        "search_placeholder":  "חיפוש חופשי...",
        "period_today":        "היום",
        "period_week":         "שבוע",
        "period_month":        "חודש",
        "period_all":          "הכל",
        "send_filtered":       "📤 שלח דוח",
        "send_to_email":       "כתובת מייל",
        "send_period":         "תקופה",
        "send_btn":            "שלח",
        "send_success":        "✅ נשלח!",
        "global_title":        "🌍 אירועים גלובליים",
        "global_empty":        "אין אירועים גלובליים כרגע",
        "findings_over_time":  "📅 ממצאים לפי זמן",
        "event_types_chart":   "🏷️ סוגי אירועים",
        "score_dist":          "📊 התפלגות ציונים",
        "top10_findings":      "🔝 10 הממצאים המובילים",
        "period_last_week":    "7 ימים אחרונים",
        "period_last_month":   "30 ימים אחרונים",
        "period_last_year":    "365 ימים אחרונים",
        "auto_reports":        "דוחות אוטומטיים",
        "report_sent":         "✅ הדוח נשלח!",
        "report_failed":       "שליחה נכשלה",
        "show_inactive":       "הצג גם לא פעילים",
        "add_org_title":       "➕ הוסף ארגון",
        "add_kw_title":        "➕ הוסף מילת מפתח",
        "weight_help":         "1=נמוך, 2=בינוני, 3=גבוה",
        "kw_placeholder":      "לדוגמה: protesta Israel Lima",
        "org_platform":        "פלטפורמה",
        "scan_log_title":      "📋 יומן סריקות",
        "pending_badge":       "ממתינות לדירוג",
        "app_subtitle":        "ניטור פעילות אנטי-ישראלית",
        "articles":            "כתבות",
        "results_count":       "תוצאות",
        "top_cities":          "10 הערים המובילות",
        "no_location":         "📍 לא זוהה מיקום",
        "active_badge":        "פעיל",
        "not_rated":           "לא דורג",
        "rating_failed":       "שמירה נכשלה",
        "skipped":             "דולג",
        "saved":               "נשמר",
        "need_review_first":   "אין כתבות מדורגות. עבור לתור דירוג כדי להתחיל.",
        "need_rating_3":       "אין עדיין כתבות בדירוג 3★ או יותר",
        "global_not_yet":      "עדיין לא נאספו אירועים גלובליים",
        "no_recent_location":  "אין כתבות ב-7 הימים האחרונים עם מיקום מזוהה",
        "nav_label":           "ניווט",
    },
    "en": {
        "title":         "🔍 OSINTAgent",
        "subtitle":      "Anti-Israel Activity Monitor",
        "page_findings": "🚨 Findings",
        "page_orgs":     "🏢 Organizations",
        "page_keywords": "🔑 Keywords",
        "page_settings": "⚙️ Settings",
        "page_reports":  "📊 Reports",
        "loading":       "Loading data...",
        "no_data":       "No data",
        "score":         "Score",
        "date":          "Date",
        "title_col":     "Title",
        "source":        "Source",
        "event_type":    "Event Type",
        "location":      "Location",
        "org":           "Organization",
        "alert":         "Alert",
        "filters":       "Filters",
        "all":           "All",
        "add":           "Add",
        "delete":        "Delete",
        "save":          "Save",
        "cancel":        "Cancel",
        "edit":          "Edit",
        "name":          "Name",
        "platform":      "Platform",
        "url":           "URL",
        "keywords":      "Keywords",
        "country":       "Country",
        "notes":         "Notes",
        "active":        "Active",
        "weight":        "Weight",
        "send_report":   "Send Report",
        "weekly":        "Weekly",
        "monthly":       "Monthly",
        "annual":        "Annual",
        "total":         "Total",
        "alerts_count":  "Alerts",
        "avg_score":     "Avg Score",
        "last_scan":     "Last Scan",
        "scan_status":   "Status",
        "settings_saved":"Settings saved ✅",
        "country_setting":"Monitor Country",
        "lang_setting":  "Scan Languages",
        "threshold_setting": "Alert Threshold",
        "email_alerts":  "Email Alerts",
        "ui_language":   "UI Language",
        "summary_weekly":"Weekly Auto-Report",
        "summary_monthly":"Monthly Auto-Report",
        "page_home":           "🏠 Home",
        "page_review":         "✍️ Review Queue",
        "page_feed":           "📰 Intelligence Feed",
        "page_global":         "🌍 Global Events",
        "page_admin":          "⚙️ Admin",
        "tab_orgs":            "🏢 Organizations",
        "tab_keywords":        "🔑 Keywords",
        "tab_settings":        "⚙️ Settings",
        "tab_reports":         "📊 Reports",
        "critical_alerts":     "🔴 Critical Alerts",
        "regular_alerts":      "🟠 Regular Alerts",
        "total_week":          "📰 Articles This Week",
        "top10_title":         "🔝 Top 10 Most Relevant",
        "geo_map_title":       "🗺️ Geographic Distribution — Peru",
        "lima_map_title":      "📍 Lima — Neighborhood Level",
        "review_queue_title":  "✍️ Review Queue",
        "pending_count":       "{n} articles pending review",
        "rated_today":         "Rated today: {done}/{total}",
        "skip":                "Skip ⏭",
        "no_pending":          "✅ No articles pending review",
        "feed_title":          "📰 Intelligence Feed",
        "search_placeholder":  "Free search...",
        "period_today":        "Today",
        "period_week":         "Week",
        "period_month":        "Month",
        "period_all":          "All",
        "send_filtered":       "📤 Send Report",
        "send_to_email":       "Email address",
        "send_period":         "Period",
        "send_btn":            "Send",
        "send_success":        "✅ Sent!",
        "global_title":        "🌍 Global Events",
        "global_empty":        "No global events at the moment",
        "findings_over_time":  "📅 Findings Over Time",
        "event_types_chart":   "🏷️ Event Types",
        "score_dist":          "📊 Score Distribution",
        "top10_findings":      "🔝 Top 10 Findings",
        "period_last_week":    "Last 7 days",
        "period_last_month":   "Last 30 days",
        "period_last_year":    "Last 365 days",
        "auto_reports":        "Auto Reports",
        "report_sent":         "✅ Report sent!",
        "report_failed":       "Send failed",
        "show_inactive":       "Show inactive too",
        "add_org_title":       "➕ Add Organization",
        "add_kw_title":        "➕ Add Keyword",
        "weight_help":         "1=Low, 2=Medium, 3=High",
        "kw_placeholder":      "e.g. protesta Israel Lima",
        "org_platform":        "Platform",
        "scan_log_title":      "📋 Scan Log",
        "pending_badge":       "pending review",
        "app_subtitle":        "Anti-Israel Activity Monitor",
        "articles":            "articles",
        "results_count":       "results",
        "top_cities":          "Top 10 Cities",
        "no_location":         "📍 No location identified",
        "active_badge":        "active",
        "not_rated":           "Not rated",
        "rating_failed":       "Save failed",
        "skipped":             "Skipped",
        "saved":               "Saved",
        "need_review_first":   "No rated articles yet. Go to Review Queue to start.",
        "need_rating_3":       "No articles rated 3★ or higher yet",
        "global_not_yet":      "No global events collected yet",
        "no_recent_location":  "No located articles in the last 7 days",
        "nav_label":           "Navigation",
    },
    "es": {
        "title":         "🔍 OSINTAgent",
        "subtitle":      "Monitor de Actividad Anti-Israel",
        "page_findings": "🚨 Hallazgos",
        "page_orgs":     "🏢 Organizaciones",
        "page_keywords": "🔑 Palabras Clave",
        "page_settings": "⚙️ Configuración",
        "page_reports":  "📊 Informes",
        "loading":       "Cargando datos...",
        "no_data":       "Sin datos",
        "score":         "Puntuación",
        "date":          "Fecha",
        "title_col":     "Título",
        "source":        "Fuente",
        "event_type":    "Tipo de Evento",
        "location":      "Ubicación",
        "org":           "Organización",
        "alert":         "Alerta",
        "filters":       "Filtros",
        "all":           "Todo",
        "add":           "Agregar",
        "delete":        "Eliminar",
        "save":          "Guardar",
        "cancel":        "Cancelar",
        "edit":          "Editar",
        "name":          "Nombre",
        "platform":      "Plataforma",
        "url":           "URL",
        "keywords":      "Palabras clave",
        "country":       "País",
        "notes":         "Notas",
        "active":        "Activo",
        "weight":        "Peso",
        "send_report":   "Enviar Informe",
        "weekly":        "Semanal",
        "monthly":       "Mensual",
        "annual":        "Anual",
        "total":         "Total",
        "alerts_count":  "Alertas",
        "avg_score":     "Puntuación media",
        "last_scan":     "Último escaneo",
        "scan_status":   "Estado",
        "settings_saved":"Configuración guardada ✅",
        "country_setting":"País a monitorear",
        "lang_setting":  "Idiomas de escaneo",
        "threshold_setting": "Umbral de alerta",
        "email_alerts":  "Alertas por email",
        "ui_language":   "Idioma de interfaz",
        "summary_weekly":"Informe semanal automático",
        "summary_monthly":"Informe mensual automático",
        "page_home":           "🏠 Inicio",
        "page_review":         "✍️ Cola de Revisión",
        "page_feed":           "📰 Noticias Filtradas",
        "page_global":         "🌍 Eventos Globales",
        "page_admin":          "⚙️ Administración",
        "tab_orgs":            "🏢 Organizaciones",
        "tab_keywords":        "🔑 Palabras Clave",
        "tab_settings":        "⚙️ Configuración",
        "tab_reports":         "📊 Informes",
        "critical_alerts":     "🔴 Alertas Críticas",
        "regular_alerts":      "🟠 Alertas Regulares",
        "total_week":          "📰 Artículos Esta Semana",
        "top10_title":         "🔝 Top 10 Más Relevantes",
        "geo_map_title":       "🗺️ Distribución Geográfica — Perú",
        "lima_map_title":      "📍 Lima — Nivel Barrio",
        "review_queue_title":  "✍️ Cola de Revisión",
        "pending_count":       "Quedan {n} artículos por revisar",
        "rated_today":         "Revisados hoy: {done}/{total}",
        "skip":                "Saltar ⏭",
        "no_pending":          "✅ No hay artículos pendientes",
        "feed_title":          "📰 Noticias Filtradas",
        "search_placeholder":  "Búsqueda libre...",
        "period_today":        "Hoy",
        "period_week":         "Semana",
        "period_month":        "Mes",
        "period_all":          "Todo",
        "send_filtered":       "📤 Enviar Informe",
        "send_to_email":       "Correo electrónico",
        "send_period":         "Período",
        "send_btn":            "Enviar",
        "send_success":        "✅ ¡Enviado!",
        "global_title":        "🌍 Eventos Globales",
        "global_empty":        "No hay eventos globales en este momento",
        "findings_over_time":  "📅 Hallazgos por Tiempo",
        "event_types_chart":   "🏷️ Tipos de Eventos",
        "score_dist":          "📊 Distribución de Puntuaciones",
        "top10_findings":      "🔝 Top 10 Hallazgos",
        "period_last_week":    "Últimos 7 días",
        "period_last_month":   "Últimos 30 días",
        "period_last_year":    "Últimos 365 días",
        "auto_reports":        "Informes Automáticos",
        "report_sent":         "✅ ¡Informe enviado!",
        "report_failed":       "Error al enviar",
        "show_inactive":       "Mostrar también inactivos",
        "add_org_title":       "➕ Agregar Organización",
        "add_kw_title":        "➕ Agregar Palabra Clave",
        "weight_help":         "1=Bajo, 2=Medio, 3=Alto",
        "kw_placeholder":      "p.ej. protesta Israel Lima",
        "org_platform":        "Plataforma",
        "scan_log_title":      "📋 Registro de Escaneos",
        "pending_badge":       "pendientes de revisión",
        "app_subtitle":        "Monitor de Actividad Anti-Israel",
        "articles":            "artículos",
        "results_count":       "resultados",
        "top_cities":          "Top 10 Ciudades",
        "no_location":         "📍 Sin ubicación identificada",
        "active_badge":        "activo",
        "not_rated":           "Sin puntuar",
        "rating_failed":       "Error al guardar",
        "skipped":             "Saltado",
        "saved":               "Guardado",
        "need_review_first":   "No hay artículos puntuados. Ve a la Cola de Revisión para empezar.",
        "need_rating_3":       "Aún no hay artículos con 3★ o más",
        "global_not_yet":      "Aún no se han recolectado eventos globales",
        "no_recent_location":  "No hay artículos con ubicación en los últimos 7 días",
        "nav_label":           "Navegación",
    },
}

EVENT_TYPE_LABELS = {
    "demonstration":   {"he": "🪧 הפגנה / עצרת",  "en": "🪧 Demonstration", "es": "🪧 Manifestación"},
    "boycott":         {"he": "🚫 קריאה לחרם",     "en": "🚫 Boycott / BDS", "es": "🚫 Boicot"},
    "violence":        {"he": "⚠️ אירוע אלים",      "en": "⚠️ Violence",      "es": "⚠️ Violencia"},
    "online_campaign": {"he": "📱 קמפיין ברשת",    "en": "📱 Online Campaign","es": "📱 Campaña online"},
    "statement":       {"he": "📢 הצהרה / גינוי",  "en": "📢 Statement",     "es": "📢 Declaración"},
    "other":           {"he": "📌 אירוע כללי",     "en": "📌 General",       "es": "📌 General"},
    "none":            {"he": "—",                  "en": "—",                "es": "—"},
}

PERU_CITY_COORDS = {
    "Lima":     (-12.0464, -77.0428),
    "Cusco":    (-13.5319, -71.9675),
    "Arequipa": (-16.4090, -71.5375),
    "Trujillo": (-8.1116,  -79.0287),
    "Piura":    (-5.1945,  -80.6328),
    "Iquitos":  (-3.7489,  -73.2538),
    "Huancayo": (-12.0651, -75.2049),
    "Puno":     (-15.8402, -70.0219),
    "Chiclayo": (-6.7714,  -79.8409),
}

LIMA_NEIGHBORHOODS = {
    "Miraflores":  (-12.1191, -77.0336),
    "San Isidro":  (-12.0978, -77.0360),
    "Centro Lima": (-12.0553, -77.0353),
    "Barranco":    (-12.1500, -77.0200),
    "San Borja":   (-12.1058, -77.0014),
    "La Victoria": (-12.0658, -77.0200),
}


PERU_CITIES = {
    "Lima":      "🏙️ Lima",
    "Cusco":     "🏔️ Cusco",
    "Arequipa":  "🌋 Arequipa",
    "Trujillo":  "🎭 Trujillo",
    "Chiclayo":  "🌿 Chiclayo",
    "Piura":     "☀️ Piura",
    "Ayacucho":  "⛪ Ayacucho",
    "Puno":      "🎵 Puno",
    "Huancayo":  "🏞️ Huancayo",
}


COUNTRY_PRESETS = {
    "Peru": "PE", "Argentina": "AR", "Chile": "CL", "Colombia": "CO",
    "Mexico": "MX", "Brazil": "BR", "Spain": "ES", "United States": "US",
    "United Kingdom": "GB", "Germany": "DE", "France": "FR", "Custom": "",
}

SCAN_LANGUAGES = {
    "עברית (he)": "he", "English (en)": "en", "Español (es)": "es",
    "Arabic (ar)": "ar", "Français (fr)": "fr", "Português (pt)": "pt",
}


# ─── Google Sheets helpers ────────────────────────────────────────────────────

@st.cache_resource(ttl=300)
def get_gspread_client():
    """Get authenticated gspread client. Cached 5 min."""
    try:
        # Try Streamlit secrets first (cloud)
        creds_raw = st.secrets.get("GOOGLE_SHEETS_CREDENTIALS_JSON", "")
        if not creds_raw:
            creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON", "")
        if not creds_raw:
            return None
        creds_dict = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Sheets connection failed: {e}")
        return None


@st.cache_data(ttl=120)
def load_sheet_data(sheet_name: str) -> pd.DataFrame:
    client = get_gspread_client()
    if not client:
        return pd.DataFrame()
    try:
        ws = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
        records = ws.get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame()
    except Exception as e:
        st.warning(f"Could not load {sheet_name}: {e}")
        return pd.DataFrame()


def get_worksheet(sheet_name: str):
    client = get_gspread_client()
    if not client:
        return None
    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        try:
            return spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            return spreadsheet.add_worksheet(title=sheet_name, rows=500, cols=20)
    except Exception:
        return None


def save_setting(key: str, value: str):
    ws = get_worksheet("Settings")
    if not ws:
        return
    try:
        records = ws.get_all_records()
        for i, row in enumerate(records, start=2):
            if str(row.get("key")) == key:
                ws.update_cell(i, 2, value)
                st.cache_data.clear()
                return
        ws.append_row([key, value])
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Save failed: {e}")


def load_settings_dict() -> dict:
    df = load_sheet("Settings")
    if df.empty:
        return {}
    return {str(r["key"]): str(r["value"]) for _, r in df.iterrows() if r.get("key")}


# ─── UI Language ──────────────────────────────────────────────────────────────

def get_ui_lang() -> str:
    return st.session_state.get("ui_lang", "he")


def t(key: str) -> str:
    lang = get_ui_lang()
    return UI_TEXT.get(lang, UI_TEXT["he"]).get(key, key)


def event_label(etype: str) -> str:
    lang = get_ui_lang()
    return EVENT_TYPE_LABELS.get(etype, {}).get(lang, etype)


# ─── Score badge ──────────────────────────────────────────────────────────────

def score_badge(score) -> str:
    try:
        s = float(score)
    except Exception:
        return str(score)
    if s >= 8:
        color = "#cc0000"
    elif s >= 6:
        color = "#e67e00"
    elif s >= 4:
        color = "#2980b9"
    else:
        color = "#888"
    return f'<span style="background:{color};color:white;padding:2px 9px;border-radius:12px;font-size:13px;font-weight:bold;">{s:.0f}</span>'


# ─── Sidebar ──────────────────────────────────────────────────────────────────

PAGE_ORDER = [
    ("page_home",   "home"),
    ("page_review", "review"),
    ("page_feed",   "feed"),
    ("page_global", "global"),
    ("page_admin",  "admin"),
]


def _count_pending_ratings() -> int:
    try:
        df = load_sheet_data("Results")
    except Exception:
        return 0
    if df.empty:
        return 0
    if "rating" not in df.columns:
        return len(df)
    rated = df["rating"].apply(lambda x: str(x).strip().isdigit() and int(x) > 0)
    return int((~rated).sum())


def render_sidebar():
    with st.sidebar:
        lang_options = [("עברית", "he"), ("English", "en"), ("Español", "es")]
        cols = st.columns(3)
        for i, (label, code) in enumerate(lang_options):
            if cols[i].button(label, key=f"lang_{code}",
                              type="primary" if get_ui_lang() == code else "secondary"):
                st.session_state["ui_lang"] = code
                st.rerun()

        st.markdown("---")
        st.title("🔍 OSINTAgent")
        st.caption(t("app_subtitle"))
        st.info("🌍 Peru")

        st.markdown("---")

        pending = _count_pending_ratings()
        page_labels = []
        for t_key, _ in PAGE_ORDER:
            label = t(t_key)
            if t_key == "page_review" and pending > 0:
                page_labels.append(f"{label} 🔴 {pending}")
            else:
                page_labels.append(label)

        selected = st.radio(t("nav_label"), page_labels, label_visibility="collapsed")
        st.markdown("---")

    idx = page_labels.index(selected)
    return PAGE_ORDER[idx][1]


# ─── Page: Findings ───────────────────────────────────────────────────────────

def _render_finding_card(row, idx, with_rating=True):
    score = row.get("relevance_score", 0)
    try:
        score_val = float(score)
    except Exception:
        score_val = 0

    bg = "#fff5f5" if score_val >= 8 else "#fff9f0" if score_val >= 6 else "#ffffff"
    border = "#cc0000" if score_val >= 8 else "#e67e00" if score_val >= 6 else "#dddddd"

    title = str(row.get("title", ""))
    link  = str(row.get("link", ""))
    source = str(row.get("source", ""))
    ts = str(row.get("timestamp", ""))[:16]
    org = str(row.get("org_name", ""))
    etype = str(row.get("event_type", ""))
    loc = str(row.get("location", ""))
    summary_he = str(row.get("summary_he", ""))
    is_alert = str(row.get("is_alert", "")).upper() == "YES"
    current_rating = int(row.get("rating", 0)) if str(row.get("rating", "")).isdigit() else 0

    st.markdown(
        f'<div style="border-left:4px solid {border};background:{bg};'
        f'padding:12px 16px;margin-bottom:4px;border-radius:4px;">'
        f'{score_badge(score_val)} &nbsp; '
        f'<strong><a href="{link}" target="_blank" style="color:#333;text-decoration:none;">{title[:120]}</a></strong>'
        f'{"&nbsp; 🔔" if is_alert else ""}'
        f'<br><span style="color:#888;font-size:12px;">📰 {source} &nbsp;|&nbsp; 📅 {ts} &nbsp;|&nbsp; '
        f'🏢 {org} &nbsp;|&nbsp; {event_label(etype)} &nbsp;|&nbsp; 📍 {loc}</span>'
        f'<br><span style="font-size:12px;color:#555;">{summary_he}</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    if not with_rating:
        return

    stars_label = {0: t("not_rated"), 1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐", 4: "⭐⭐⭐⭐", 5: "⭐⭐⭐⭐⭐"}
    col_r1, col_r2, col_r3, col_r4, col_r5, col_cur = st.columns([1,1,1,1,1,4])
    for star, col in zip([1,2,3,4,5], [col_r1,col_r2,col_r3,col_r4,col_r5]):
        btn_label = "⭐" if star <= current_rating else "☆"
        if col.button(btn_label, key=f"rate_{idx}_{star}"):
            try:
                client = get_gspread_client()
                if client:
                    ws = client.open_by_key(SPREADSHEET_ID).worksheet("Results")
                    all_vals = ws.get_all_values()
                    headers = all_vals[0] if all_vals else []
                    if "rating" not in headers:
                        ws.update_cell(1, len(headers)+1, "rating")
                        rating_col = len(headers)+1
                    else:
                        rating_col = headers.index("rating") + 1
                    for r_idx, r_row in enumerate(all_vals[1:], start=2):
                        link_col = headers.index("link") if "link" in headers else 3
                        if len(r_row) > link_col and r_row[link_col] == link:
                            ws.update_cell(r_idx, rating_col, star)
                            break
                    st.cache_data.clear()
                    st.rerun()
            except Exception as e:
                st.error(f"Rating save failed: {e}")
    if current_rating > 0:
        col_cur.caption(stars_label[current_rating])
    st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)


def _render_global_card(row):
    title = str(row.get("title", ""))[:140]
    link  = str(row.get("link", ""))
    source = str(row.get("source", ""))
    ts = str(row.get("timestamp", ""))[:16]
    loc = str(row.get("location", "") or "—")
    summary_he = str(row.get("summary_he", ""))[:160]
    try:
        score = float(row.get("relevance_score", 0) or 0)
    except Exception:
        score = 0
    st.markdown(
        f'<div style="border-left:4px solid #2980b9;background:#1a2a3a;'
        f'color:white;padding:12px 16px;margin-bottom:8px;border-radius:4px;">'
        f'🌍 <strong><a href="{link}" target="_blank" style="color:#9ecbff;text-decoration:none;">{title}</a></strong>'
        f'&nbsp;<span style="background:#2980b9;padding:1px 8px;border-radius:10px;font-size:11px;">{score:.0f}/10</span><br>'
        f'<span style="font-size:12px;opacity:.8;">📍 {loc} | {source} | {ts}</span><br>'
        f'<span style="font-size:12px;">{summary_he}</span>'
        f'</div>',
        unsafe_allow_html=True
    )


def _rating_of(row) -> int:
    raw = row.get("rating", "") if hasattr(row, "get") else ""
    try:
        return int(raw) if str(raw).strip() else 0
    except (ValueError, TypeError):
        return 0


def _parse_ts_col(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_ts"] = pd.to_datetime(df.get("timestamp", "").astype(str).str[:16],
                               format="%Y-%m-%d %H:%M", errors="coerce")
    if "relevance_score" in df.columns:
        df["relevance_score"] = pd.to_numeric(df["relevance_score"], errors="coerce").fillna(0)
    return df


def _save_rating(link: str, stars: int):
    client = get_gspread_client()
    if not client:
        return
    ws = client.open_by_key(SPREADSHEET_ID).worksheet("Results")
    all_vals = ws.get_all_values()
    headers = all_vals[0] if all_vals else []
    if "rating" not in headers:
        ws.update_cell(1, len(headers)+1, "rating")
        rating_col = len(headers)+1
    else:
        rating_col = headers.index("rating") + 1
    link_col = headers.index("link") if "link" in headers else 3
    for r_idx, r_row in enumerate(all_vals[1:], start=2):
        if len(r_row) > link_col and r_row[link_col] == link:
            ws.update_cell(r_idx, rating_col, stars)
            break
    st.cache_data.clear()


def _peru_city_bucket(loc_val) -> str:
    loc_str = str(loc_val).strip()
    if not loc_str or loc_str.lower() in ("nan", "none"):
        return None
    for city in PERU_CITY_COORDS.keys():
        if city.lower() in loc_str.lower():
            return city
    return None


def _render_peru_map(df: pd.DataFrame):
    """National map of Peru with article-count circles."""
    df = _parse_ts_col(df)
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=7)
    recent = df[df["_ts"] >= cutoff].copy() if "_ts" in df.columns else df
    if "location" not in recent.columns:
        return
    recent["_city"] = recent["location"].apply(_peru_city_bucket)
    counts = recent.groupby("_city").size().to_dict()
    if not counts:
        st.info(t("no_recent_location"))
        return

    if FOLIUM_AVAILABLE:
        fmap = folium.Map(location=[-9.19, -75.0152], zoom_start=5, tiles="cartodbpositron")
        for city, (lat, lon) in PERU_CITY_COORDS.items():
            n = counts.get(city, 0)
            if n == 0:
                continue
            folium.CircleMarker(
                location=[lat, lon],
                radius=6 + min(20, n * 2),
                popup=f"{city}: {n} {t('articles')}",
                tooltip=f"{city} — {n}",
                color="#cc0000", fill=True, fill_opacity=0.6,
            ).add_to(fmap)
        st_folium(fmap, width=None, height=400, returned_objects=[])
    else:
        rows = []
        for city, (lat, lon) in PERU_CITY_COORDS.items():
            n = counts.get(city, 0)
            if n > 0:
                rows.append({"lat": lat, "lon": lon, "city": city, "count": n})
        if rows:
            st.map(pd.DataFrame(rows), zoom=4)


def _render_lima_map(df: pd.DataFrame):
    if "location" not in df.columns:
        return
    lima = df[df["location"].astype(str).str.contains("Lima", case=False, na=False)]
    if lima.empty:
        return
    st.markdown(f"**🏙️ Lima — {len(lima)} {t('articles')}**")
    if FOLIUM_AVAILABLE:
        fmap = folium.Map(location=[-12.0764, -77.0300], zoom_start=11, tiles="cartodbpositron")
        for name, (lat, lon) in LIMA_NEIGHBORHOODS.items():
            folium.Marker(
                location=[lat, lon],
                popup=name,
                tooltip=name,
                icon=folium.Icon(color="blue", icon="info-sign"),
            ).add_to(fmap)
        st_folium(fmap, width=None, height=380, returned_objects=[])
    else:
        rows = [{"lat": lat, "lon": lon} for lat, lon in LIMA_NEIGHBORHOODS.values()]
        st.map(pd.DataFrame(rows), zoom=11)


# ─── Page 1: Home ─────────────────────────────────────────────────────────────

def page_home():
    st.header(t("page_home"))

    with st.spinner(t("loading")):
        df = load_sheet_data("Results")

    if df.empty:
        st.info(t("no_data"))
        return

    df = _parse_ts_col(df)
    now = pd.Timestamp.now()
    last_24h = df[df["_ts"] >= now - pd.Timedelta(hours=24)]
    last_7d  = df[df["_ts"] >= now - pd.Timedelta(days=7)]

    # KPI tiles
    c1, c2, c3, c4 = st.columns(4)
    crit = len(last_24h[last_24h["relevance_score"] >= 8]) if "relevance_score" in last_24h.columns else 0
    reg  = len(last_24h[(last_24h["relevance_score"] >= 6) & (last_24h["relevance_score"] < 8)]) if "relevance_score" in last_24h.columns else 0
    c1.metric(t("critical_alerts"), crit)
    c2.metric(t("regular_alerts"), reg)
    c3.metric(t("total_week"), len(last_7d))

    scan_df = load_sheet_data("ScanLog")
    if not scan_df.empty:
        last_row = scan_df.iloc[-1]
        c4.metric(t("last_scan"),
                  str(last_row.get("timestamp", ""))[5:16],
                  delta=str(last_row.get("status", "")),
                  delta_color="off")
    else:
        c4.metric(t("last_scan"), "—")

    st.markdown("---")

    # Top 10 most-relevant (last 7 days)
    st.markdown(f"### {t('top10_title')}")
    if "relevance_score" in last_7d.columns and not last_7d.empty:
        top = last_7d.sort_values("relevance_score", ascending=False).head(10)
        for _, row in top.iterrows():
            try:
                s = float(row.get("relevance_score", 0) or 0)
            except Exception:
                s = 0
            color = "#cc0000" if s >= 8 else "#e67e00" if s >= 6 else "#888"
            title = str(row.get("title", ""))[:110]
            link = str(row.get("link", ""))
            source = str(row.get("source", ""))
            ts = str(row.get("timestamp", ""))[:16]
            etype = str(row.get("event_type", ""))
            summary_he = str(row.get("summary_he", ""))[:100]
            st.markdown(
                f'<div style="padding:8px 12px;margin-bottom:4px;border-radius:4px;background:#fafafa;'
                f'border-left:3px solid {color};">'
                f'<span style="background:{color};color:white;padding:1px 8px;border-radius:10px;'
                f'font-size:12px;font-weight:bold;">{s:.0f}</span> '
                f'<span style="font-size:12px;color:#555;">{event_label(etype)}</span> '
                f'<a href="{link}" target="_blank" style="color:#222;text-decoration:none;font-weight:600;">{title}</a>'
                f'<br><span style="font-size:11px;color:#888;">{source} | {ts}</span>'
                f'<br><span style="font-size:12px;color:#555;">{summary_he}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.info(t("no_data"))

    st.markdown("---")

    # Peru national map
    st.markdown(f"### {t('geo_map_title')}")
    _render_peru_map(df)

    st.markdown("---")

    st.markdown(f"### {t('lima_map_title')}")
    _render_lima_map(df)


# ─── Page 2: Review queue ─────────────────────────────────────────────────────

_MOBILE_CSS = """
<style>
@media (max-width: 768px) {
    .stButton > button {
        font-size: 18px !important;
        padding: 10px 2px !important;
        min-height: 48px !important;
    }
    div[data-testid="column"] { padding: 0 1px !important; }
}
.stMarkdown, p, li { direction: rtl; text-align: right; }
</style>
"""


def page_review():
    st.markdown(_MOBILE_CSS, unsafe_allow_html=True)
    st.header(t("review_queue_title"))

    df = load_sheet_data("Results")
    if df.empty:
        st.info(t("no_data"))
        return

    if "rating" not in df.columns:
        df = df.copy()
        df["rating"] = ""
    df["_rating_int"] = df["rating"].apply(lambda x: int(x) if str(x).strip().isdigit() else 0)
    df["relevance_score"] = pd.to_numeric(df.get("relevance_score", 0), errors="coerce").fillna(0)

    unrated = df[df["_rating_int"] == 0].sort_values("relevance_score", ascending=False)
    rated_today = df[df["_rating_int"] > 0]
    total = len(df)
    done  = len(rated_today)

    st.caption(t("pending_count").format(n=len(unrated)))
    if total:
        st.progress(min(1.0, done / total),
                    text=t("rated_today").format(done=done, total=total))

    # Filter skipped in session
    skipped = st.session_state.setdefault("review_skipped", set())
    queue = unrated[~unrated["link"].astype(str).isin(skipped)]

    if queue.empty:
        st.success(t("no_pending"))
        return

    row = queue.iloc[0]
    idx = row.name
    score = float(row.get("relevance_score", 0) or 0)
    color = "#cc0000" if score >= 8 else "#e67e00" if score >= 6 else "#2980b9"
    title = str(row.get("title", ""))
    link = str(row.get("link", ""))
    source = str(row.get("source", ""))
    ts = str(row.get("timestamp", ""))[:16]
    org = str(row.get("org_name", ""))
    loc = str(row.get("location", "") or "—")
    summary_he = str(row.get("summary_he", ""))

    st.markdown(
        f'<div style="border:2px solid {color};border-radius:8px;padding:14px 16px;margin-bottom:14px;background:#fff;">'
        f'<span style="background:{color};color:white;padding:3px 12px;border-radius:12px;font-weight:bold;">{score:.0f}/10</span>'
        f'&nbsp;&nbsp;<strong style="font-size:16px;"><a href="{link}" target="_blank" style="color:#222;text-decoration:none;">{title}</a></strong>'
        f'<div style="color:#777;font-size:12px;margin-top:6px;">📰 {source} | 📅 {ts} | 🏢 {org} | 📍 {loc}</div>'
        f'<div style="font-size:13px;color:#444;margin-top:8px;">{summary_he}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    cols = st.columns(6)
    star_labels = ["⭐1", "⭐⭐2", "⭐⭐⭐3", "⭐⭐⭐⭐4", "⭐⭐⭐⭐⭐5", t("skip")]
    for i, label in enumerate(star_labels):
        key = f"review_{idx}_{i}"
        if cols[i].button(label, key=key, use_container_width=True):
            if i < 5:
                try:
                    _save_rating(link, i + 1)
                    st.toast(f"{t('saved')}: {i+1}★")
                except Exception as e:
                    st.error(f"{t('rating_failed')}: {e}")
            else:
                skipped.add(link)
                st.toast(t("skipped"))
            st.rerun()


# ─── Page 3: Filtered feed ────────────────────────────────────────────────────

def page_feed():
    st.header(t("feed_title"))
    df = load_sheet_data("Results")
    if df.empty or "rating" not in df.columns:
        st.info(t("need_review_first"))
        return

    df = _parse_ts_col(df)
    df["_rating"] = df["rating"].apply(lambda x: int(x) if str(x).strip().isdigit() else 0)
    df = df[df["_rating"] >= 3]
    if df.empty:
        st.info(t("need_rating_3"))
        return

    period_labels = [t("period_today"), t("period_week"), t("period_month"), t("period_all")]

    with st.expander(f"🔍 {t('filters')}", expanded=True):
        search_q = st.text_input(t("search_placeholder"), "")
        period = st.radio(t("send_period"), period_labels,
                          horizontal=True, index=3)
        etypes_avail = sorted([e for e in df["event_type"].dropna().unique() if e])
        etype_sel = st.multiselect(t("event_type"), etypes_avail, default=etypes_avail)

    filtered = df.copy()
    if search_q:
        q = search_q.lower()
        filtered = filtered[
            filtered["title"].astype(str).str.lower().str.contains(q, na=False) |
            filtered["summary_he"].astype(str).str.lower().str.contains(q, na=False)
        ]

    now = pd.Timestamp.now()
    if period == t("period_today"):
        filtered = filtered[filtered["_ts"] >= now - pd.Timedelta(days=1)]
    elif period == t("period_week"):
        filtered = filtered[filtered["_ts"] >= now - pd.Timedelta(days=7)]
    elif period == t("period_month"):
        filtered = filtered[filtered["_ts"] >= now - pd.Timedelta(days=30)]

    if etype_sel:
        filtered = filtered[filtered["event_type"].isin(etype_sel)]

    filtered = filtered.sort_values("relevance_score", ascending=False)
    st.caption(f"{len(filtered)} {t('articles')}")

    with st.expander(t("send_filtered")):
        default_email = os.environ.get("ALERT_EMAIL_TO", "")
        try:
            default_email = st.secrets.get("ALERT_EMAIL_TO", default_email)
        except Exception:
            pass
        recipient = st.text_input(t("send_to_email"), value=default_email)
        email_period_labels = [t("period_today"), t("period_week"), t("period_month")]
        period_label = st.selectbox(t("send_period"), email_period_labels, key="feed_email_period")
        if st.button(t("send_btn"), type="primary"):
            try:
                from notifier import send_filtered_report
                send_filtered_report(filtered.to_dict("records"), recipient, period_label)
                st.success(t("send_success"))
            except Exception as e:
                st.error(f"{t('report_failed')}: {e}")

    st.markdown("---")

    # Cards
    for idx, row in filtered.iterrows():
        rating = int(row.get("_rating", 0))
        score = float(row.get("relevance_score", 0) or 0)
        color = "#cc0000" if score >= 8 else "#e67e00" if score >= 6 else "#2980b9"
        title = str(row.get("title", ""))[:140]
        link = str(row.get("link", ""))
        source = str(row.get("source", ""))
        ts = str(row.get("timestamp", ""))[:16]
        etype = str(row.get("event_type", ""))
        loc = str(row.get("location", "") or "—")
        summary_he = str(row.get("summary_he", ""))[:200]
        st.markdown(
            f'<div style="border-left:4px solid {color};background:#fafafa;'
            f'padding:10px 14px;margin-bottom:6px;border-radius:4px;">'
            f'<span style="background:{color};color:white;padding:1px 8px;border-radius:10px;font-size:12px;font-weight:bold;">{score:.0f}</span>'
            f'&nbsp;<span style="color:#daa520;">{"⭐" * rating}</span> '
            f'<span style="font-size:12px;color:#555;">{event_label(etype)}</span>&nbsp;'
            f'<span style="font-size:12px;color:#777;">📍 {loc}</span><br>'
            f'<strong><a href="{link}" target="_blank" style="color:#222;text-decoration:none;">{title}</a></strong>'
            f'<div style="font-size:12px;color:#555;margin-top:4px;">{summary_he}</div>'
            f'<div style="font-size:11px;color:#888;margin-top:4px;">{source} | {ts}</div>'
            f'</div>',
            unsafe_allow_html=True
        )


# ─── Page 4: Global events ────────────────────────────────────────────────────

def page_global():
    st.header(t("global_title"))
    df = load_sheet_data("Results")
    if df.empty:
        st.info(t("no_data"))
        return
    if "is_global" not in df.columns:
        st.info(t("global_not_yet"))
        return

    df = _parse_ts_col(df)
    gdf = df[df["is_global"].astype(str).str.upper().isin(["YES", "TRUE", "1"])]
    if gdf.empty:
        st.info(t("global_empty"))
        return

    gdf = gdf.sort_values("relevance_score", ascending=False)
    st.caption(f"{len(gdf)} {t('results_count')}")

    # Global map
    if "location" in gdf.columns:
        try:
            from analyzer import GLOBAL_CITIES
        except ImportError:
            GLOBAL_CITIES = []
        GLOBAL_CITY_COORDS = {
            "London": (51.5074, -0.1278),
            "Paris": (48.8566, 2.3522),
            "Berlin": (52.5200, 13.4050),
            "Madrid": (40.4168, -3.7038),
            "Rome": (41.9028, 12.4964),
            "New York": (40.7128, -74.0060),
            "Washington": (38.9072, -77.0369),
            "Sydney": (-33.8688, 151.2093),
            "Toronto": (43.6532, -79.3832),
            "Amsterdam": (52.3676, 4.9041),
            "Brussels": (50.8503, 4.3517),
            "Stockholm": (59.3293, 18.0686),
            "Oslo": (59.9139, 10.7522),
        }
        loc_counts = gdf["location"].value_counts().to_dict()
        if FOLIUM_AVAILABLE and loc_counts:
            fmap = folium.Map(location=[30, 0], zoom_start=2, tiles="cartodbpositron")
            for city, (lat, lon) in GLOBAL_CITY_COORDS.items():
                n = loc_counts.get(city, 0)
                if n == 0:
                    continue
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=6 + min(20, n * 2),
                    popup=f"{city}: {n}",
                    tooltip=f"{city} — {n}",
                    color="#2980b9", fill=True, fill_opacity=0.6,
                ).add_to(fmap)
            st_folium(fmap, width=None, height=380, returned_objects=[])
        elif loc_counts:
            rows = []
            for city, (lat, lon) in GLOBAL_CITY_COORDS.items():
                if loc_counts.get(city, 0) > 0:
                    rows.append({"lat": lat, "lon": lon})
            if rows:
                st.map(pd.DataFrame(rows), zoom=1)

    st.markdown("---")

    for _, row in gdf.iterrows():
        _render_global_card(row)


# ─── Page: Organizations ──────────────────────────────────────────────────────

def page_organizations():
    st.header(t("page_orgs"))
    df = load_sheet_data("Organizations")

    tab1, tab2 = st.tabs([f"📋 {t('all')}", f"➕ {t('add')}"])

    with tab1:
        if df.empty:
            st.info(t("no_data"))
        else:
            # Filter by active
            show_inactive = st.checkbox(t("show_inactive"))
            if not show_inactive and "active" in df.columns:
                df_show = df[df["active"].astype(str).str.upper().isin(["TRUE", "1", "YES", ""])]
            else:
                df_show = df

            for _, row in df_show.iterrows():
                name     = str(row.get("name", ""))
                platform = str(row.get("platform", ""))
                url      = str(row.get("url", ""))
                country  = str(row.get("country", ""))
                notes    = str(row.get("notes", ""))
                active   = str(row.get("active", "TRUE")).upper() in ("TRUE", "1", "YES", "")
                kws      = str(row.get("keywords", ""))

                with st.expander(f"{'🟢' if active else '🔴'} {name} — {platform} ({country})"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if url:
                            st.markdown(f"🔗 [{url}]({url})")
                        if kws:
                            st.caption(f"🔑 {kws}")
                        if notes:
                            st.caption(f"📝 {notes}")
                    with col2:
                        if st.button(f"🗑️ {t('delete')}", key=f"del_org_{name}"):
                            ws = get_worksheet("Organizations")
                            if ws:
                                records = ws.get_all_records()
                                for i, r in enumerate(records, start=2):
                                    if str(r.get("name")) == name:
                                        ws.delete_rows(i)
                                        st.cache_data.clear()
                                        st.success(f"Deleted: {name}")
                                        st.rerun()

    with tab2:
        with st.form("add_org_form"):
            st.subheader(t("add_org_title"))
            c1, c2 = st.columns(2)
            new_name     = c1.text_input(t("name"))
            new_platform = c2.selectbox(t("platform"), ["Instagram", "Facebook", "Twitter/X", "YouTube", "Website", "Other"])
            new_url      = st.text_input(t("url"))
            new_keywords = st.text_input(t("keywords"), help="Comma-separated: BDS,protesta,boycott")
            c3, c4 = st.columns(2)

            country_options = list(COUNTRY_PRESETS.keys())
            new_country  = c3.selectbox(t("country"), country_options)
            new_notes    = c4.text_input(t("notes"))

            if st.form_submit_button(t("save")):
                if new_name:
                    ws = get_worksheet("Organizations")
                    if ws:
                        existing = ws.get_all_values()
                        if not existing:
                            ws.append_row(["name","platform","url","keywords","country","notes","active"])
                        ws.append_row([new_name, new_platform, new_url, new_keywords,
                                       new_country, new_notes, "TRUE"])
                        st.cache_data.clear()
                        st.success(f"✅ Added: {new_name}")
                        st.rerun()
                else:
                    st.error(t("name"))


# ─── Page: Keywords ───────────────────────────────────────────────────────────

def page_keywords():
    st.header(t("page_keywords"))
    df = load_sheet_data("Keywords")

    tab1, tab2 = st.tabs([f"📋 {t('all')}", f"➕ {t('add')}"])

    with tab1:
        if df.empty:
            st.info(t("no_data"))
        else:
            # Weight filter
            weight_filter = st.multiselect(t("weight"), [1, 2, 3], default=[1, 2, 3])
            if "weight" in df.columns:
                df["weight"] = pd.to_numeric(df["weight"], errors="coerce").fillna(2)
                df_show = df[df["weight"].isin(weight_filter)]
            else:
                df_show = df

            weight_colors = {3: "🔴", 2: "🟡", 1: "🟢"}

            for _, row in df_show.iterrows():
                kw     = str(row.get("keyword", ""))
                weight = int(row.get("weight", 2))
                active = str(row.get("active", "TRUE")).upper() in ("TRUE", "1", "YES")

                col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
                col1.markdown(f"{weight_colors.get(weight,'⚪')} `{kw}`")
                col2.caption(f"w={weight}")

                # Toggle active
                new_active = col3.checkbox("✓", value=active, key=f"kw_active_{kw}",
                                           label_visibility="collapsed")
                if new_active != active:
                    ws = get_worksheet("Keywords")
                    if ws:
                        records = ws.get_all_records()
                        for i, r in enumerate(records, start=2):
                            if str(r.get("keyword")) == kw:
                                ws.update_cell(i, 3, "TRUE" if new_active else "FALSE")
                                st.cache_data.clear()
                                st.rerun()

                # Delete
                if col4.button("🗑️", key=f"del_kw_{kw}"):
                    ws = get_worksheet("Keywords")
                    if ws:
                        records = ws.get_all_records()
                        for i, r in enumerate(records, start=2):
                            if str(r.get("keyword")) == kw:
                                ws.delete_rows(i)
                                st.cache_data.clear()
                                st.rerun()

    with tab2:
        with st.form("add_kw_form"):
            st.subheader(t("add_kw_title"))
            new_kw = st.text_input(t("keywords"), placeholder=t("kw_placeholder"))
            new_weight = st.select_slider(t("weight"), options=[1, 2, 3], value=2,
                                          help=t("weight_help"))
            if st.form_submit_button(t("save")):
                if new_kw.strip():
                    ws = get_worksheet("Keywords")
                    if ws:
                        existing = ws.get_all_values()
                        if not existing:
                            ws.append_row(["keyword", "weight", "active"])
                        ws.append_row([new_kw.strip(), new_weight, "TRUE"])
                        st.cache_data.clear()
                        st.success(f"✅ Added: {new_kw}")
                        st.rerun()
                else:
                    st.error(f"{t('keywords')} — {t('filters')}")


# ─── Page: Settings ───────────────────────────────────────────────────────────

def page_settings():
    st.header(t("page_settings"))
    df_s = load_sheet_data("Settings")
    settings = dict(zip(df_s["key"], df_s["value"])) if not df_s.empty and "key" in df_s.columns else {}

    with st.form("settings_form"):
        st.subheader(f"🌍 {t('country_setting')}")
        col1, col2 = st.columns(2)

        country_options = list(COUNTRY_PRESETS.keys())
        current_country = settings.get("country", "Peru")
        if current_country not in country_options:
            country_options.append(current_country)

        sel_country = col1.selectbox(t("country"), country_options,
                                     index=country_options.index(current_country) if current_country in country_options else 0)
        # Custom country code if "Custom"
        auto_code = COUNTRY_PRESETS.get(sel_country, "")
        sel_code = col2.text_input("Country Code (2 letters)", value=settings.get("country_code", auto_code or "PE"),
                                   max_chars=2)

        st.subheader(f"🗣️ {t('lang_setting')}")
        lang_options = list(SCAN_LANGUAGES.keys())
        current_langs_raw = settings.get("languages", "es,en,he").split(",")
        # Map codes back to display names
        code_to_display = {v: k for k, v in SCAN_LANGUAGES.items()}
        current_lang_display = [code_to_display.get(l.strip(), l.strip()) for l in current_langs_raw]
        current_lang_display = [x for x in current_lang_display if x in lang_options]

        sel_langs = st.multiselect(t("lang_setting"), lang_options,
                                   default=current_lang_display or ["Español (es)", "English (en)"])

        st.subheader(f"🔔 {t('threshold_setting')}")
        sel_threshold = st.slider(t("threshold_setting"), 1, 10,
                                  int(settings.get("alert_threshold", "6")))

        st.subheader(f"📧 {t('email_alerts')}")
        sel_email = st.checkbox(t("email_alerts"),
                                value=settings.get("email_alerts", "true").lower() == "true")

        st.subheader(f"📊 {t('auto_reports')}")
        col3, col4 = st.columns(2)
        sel_weekly = col3.checkbox(t("summary_weekly"),
                                   value=settings.get("weekly_summary", "true").lower() == "true")
        sel_monthly = col4.checkbox(t("summary_monthly"),
                                    value=settings.get("monthly_summary", "true").lower() == "true")

        submitted = st.form_submit_button(f"💾 {t('save')}")

    if submitted:
        lang_codes = ",".join([SCAN_LANGUAGES[l] for l in sel_langs if l in SCAN_LANGUAGES])
        save_setting("country", sel_country)
        save_setting("country_code", sel_code.upper())
        save_setting("languages", lang_codes)
        save_setting("alert_threshold", str(sel_threshold))
        save_setting("email_alerts", "true" if sel_email else "false")
        save_setting("weekly_summary", "true" if sel_weekly else "false")
        save_setting("monthly_summary", "true" if sel_monthly else "false")
        st.success(t("settings_saved"))
        st.rerun()

    # ── Scan Log ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader(t("scan_log_title"))
    df_log = load_sheet_data("ScanLog")
    if not df_log.empty:
        st.dataframe(df_log.tail(20).iloc[::-1], use_container_width=True)
    else:
        st.info(t("no_data"))


# ─── Page: Reports ────────────────────────────────────────────────────────────

def page_reports():
    st.header(t("page_reports"))
    df = load_sheet_data("Results")

    if df.empty:
        st.info(t("no_data"))
        return

    if "timestamp" in df.columns:
        df["ts_parsed"] = pd.to_datetime(df["timestamp"].str[:16], format="%Y-%m-%d %H:%M", errors="coerce")
    if "relevance_score" in df.columns:
        df["relevance_score"] = pd.to_numeric(df["relevance_score"], errors="coerce").fillna(0)

    now = pd.Timestamp.now()

    # Period selector
    period = st.radio("", [t("weekly"), t("monthly"), t("annual")], horizontal=True)

    if period == t("weekly"):
        cutoff = now - pd.Timedelta(days=7)
        label = t("period_last_week")
    elif period == t("monthly"):
        cutoff = now - pd.Timedelta(days=30)
        label = t("period_last_month")
    else:
        cutoff = now - pd.Timedelta(days=365)
        label = t("period_last_year")

    if "ts_parsed" in df.columns:
        df_period = df[df["ts_parsed"] >= cutoff]
    else:
        df_period = df

    st.caption(f"📅 {label} — {len(df_period)} {t('results_count')}")

    # ── KPIs ──────────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("total"), len(df_period))
    alerts = len(df_period[df_period.get("is_alert", pd.Series()).astype(str).str.upper() == "YES"]) if "is_alert" in df_period else 0
    col2.metric(t("alerts_count"), alerts)
    avg = df_period["relevance_score"].mean() if "relevance_score" in df_period else 0
    col3.metric(t("avg_score"), f"{avg:.1f}" if avg else "—")
    high = len(df_period[df_period["relevance_score"] >= 8]) if "relevance_score" in df_period else 0
    col4.metric(t("critical_alerts") + " (8+)", high)

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader(t("findings_over_time"))
        if "ts_parsed" in df_period.columns and not df_period.empty:
            by_day = df_period.groupby(df_period["ts_parsed"].dt.date).size().reset_index()
            by_day.columns = ["date", "count"]
            st.bar_chart(by_day.set_index("date"))
        else:
            st.info(t("no_data"))

    with col_right:
        st.subheader(t("event_types_chart"))
        if "event_type" in df_period.columns and not df_period.empty:
            by_type = df_period["event_type"].value_counts().reset_index()
            by_type.columns = ["event_type", "count"]
            by_type["event_type"] = by_type["event_type"].map(lambda x: event_label(x))
            st.bar_chart(by_type.set_index("event_type"))
        else:
            st.info(t("no_data"))

    # Score distribution
    if "relevance_score" in df_period.columns and not df_period.empty:
        st.subheader(t("score_dist"))
        buckets = pd.cut(df_period["relevance_score"],
                         bins=[0, 2, 4, 6, 8, 10],
                         labels=["1-2", "3-4", "5-6", "7-8", "9-10"])
        dist = buckets.value_counts().sort_index().reset_index()
        dist.columns = ["Score Range", "Count"]
        st.bar_chart(dist.set_index("Score Range"))

    # Top findings table
    st.subheader(t("top10_findings"))
    if not df_period.empty and "relevance_score" in df_period.columns:
        top10 = df_period.nlargest(10, "relevance_score")[
            ["timestamp", "relevance_score", "title", "event_type", "location", "org_name", "link"]
        ].copy()
        top10["timestamp"] = top10["timestamp"].astype(str).str[:16]
        top10["title_short"] = top10["title"].astype(str).str[:80]
        st.dataframe(top10[["timestamp","relevance_score","title_short","event_type","location","org_name"]],
                     use_container_width=True)

    # ── Send Summary Email ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader(f"📧 {t('send_report')}")
    col_send, col_info = st.columns([2, 3])
    with col_send:
        if st.button(f"📤 {t('send_report')} ({period})", type="primary"):
            with st.spinner(t("loading")):
                try:
                    from summary_runner import run as run_summary
                    period_map = {
                        t("weekly"): "weekly",
                        t("monthly"): "monthly",
                        t("annual"): "annual",
                    }
                    run_summary(period_map.get(period, "weekly"))
                    st.success(t("report_sent"))
                except Exception as e:
                    st.error(f"{t('report_failed')}: {e}")
    with col_info:
        st.caption(t("send_report"))


# ─── Main ─────────────────────────────────────────────────────────────────────

def page_admin():
    st.header(t("page_admin"))
    tab1, tab2, tab3, tab4 = st.tabs([t("tab_orgs"), t("tab_keywords"),
                                      t("tab_settings"), t("tab_reports")])
    with tab1:
        page_organizations()
    with tab2:
        page_keywords()
    with tab3:
        page_settings()
    with tab4:
        page_reports()


def main():
    if "ui_lang" not in st.session_state:
        st.session_state["ui_lang"] = "he"

    lang = get_ui_lang()
    direction  = "rtl"   if lang == "he" else "ltr"
    text_align = "right" if lang == "he" else "left"

    st.markdown(f"""
    <style>
    .stMarkdown, .stText, p, li, h1, h2, h3, label {{
        direction: {direction} !important;
        text-align: {text_align} !important;
    }}
    .stMetric {{ direction: {direction}; }}
    @media (max-width: 768px) {{
        .stButton > button {{
            font-size: 18px !important;
            padding: 10px 2px !important;
            min-height: 48px !important;
        }}
        div[data-testid="column"] {{ padding: 0 1px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

    page = render_sidebar()

    if page == "home":
        page_home()
    elif page == "review":
        page_review()
    elif page == "feed":
        page_feed()
    elif page == "global":
        page_global()
    elif page == "admin":
        page_admin()


if __name__ == "__main__":
    main()
# test Mon Apr  6 14:28:00 -05 2026
