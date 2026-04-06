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

def render_sidebar():
    with st.sidebar:
        # Language
        lang_options = {"עברית": "he", "English": "en", "Español": "es"}
        cols = st.columns(3)
        for i, (label, code) in enumerate(lang_options.items()):
            if cols[i].button(label, key=f"lang_{code}",
                              type="primary" if get_ui_lang() == code else "secondary"):
                st.session_state["ui_lang"] = code
                st.rerun()

        st.markdown("---")
        st.title(t("title"))
        st.caption(t("subtitle"))
        st.info("🌍 Peru")

        st.markdown("---")

        pages = [
            t("page_findings"),
            t("page_orgs"),
            t("page_keywords"),
            t("page_settings"),
            t("page_reports"),
        ]
        page = st.radio("Navigation", pages, label_visibility="collapsed")

        st.markdown("---")

    return page


# ─── Page: Findings ───────────────────────────────────────────────────────────

def page_findings():
    st.header(t("page_findings"))
    df = load_sheet_data("Results")

    if df.empty:
        st.info(t("no_data"))
        return

    # ── Filters ──────────────────────────────────────────────────────────────
    with st.expander(f"🔍 {t('filters')}", expanded=True):
        col1, col2, col3, col4 = st.columns(4)

        # Score filter
        with col1:
            min_score = st.slider(t("score"), 0, 10, 0)

        # Event type filter
        with col2:
            etypes = [t("all")] + sorted(df["event_type"].dropna().unique().tolist()) if "event_type" in df else [t("all")]
            etype_sel = st.selectbox(t("event_type"), etypes)

        # Location filter
        with col3:
            locs = [t("all")] + sorted(df["location"].dropna().unique().tolist()) if "location" in df else [t("all")]
            loc_sel = st.selectbox(t("location"), locs)

        # Alerts only
        with col4:
            alerts_only = st.checkbox(f"🔔 {t('alerts_count')} only")

    # Apply filters
    filtered = df.copy()
    if "relevance_score" in filtered.columns:
        filtered["relevance_score"] = pd.to_numeric(filtered["relevance_score"], errors="coerce").fillna(0)
        filtered = filtered[filtered["relevance_score"] >= min_score]
    if etype_sel != t("all") and "event_type" in filtered.columns:
        filtered = filtered[filtered["event_type"] == etype_sel]
    if loc_sel != t("all") and "location" in filtered.columns:
        filtered = filtered[filtered["location"] == loc_sel]
    if alerts_only and "is_alert" in filtered.columns:
        filtered = filtered[filtered["is_alert"].astype(str).str.upper() == "YES"]

    # Sort newest first
    if "timestamp" in filtered.columns:
        filtered = filtered.sort_values("timestamp", ascending=False)

    st.caption(f"מציג {len(filtered)} מתוך {len(df)} ממצאים")

    # ── KPI row ──────────────────────────────────────────────────────────────
    if not filtered.empty and "relevance_score" in filtered.columns:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("total"), len(filtered))
        alert_count = len(filtered[filtered["is_alert"].astype(str).str.upper() == "YES"]) if "is_alert" in filtered.columns else 0
        c2.metric(t("alerts_count"), alert_count)
        avg = filtered["relevance_score"].mean()
        c3.metric(t("avg_score"), f"{avg:.1f}")
        high = len(filtered[filtered["relevance_score"] >= 8])
        c4.metric("🔴 Critical (8+)", high)

    st.markdown("---")

    # ── Table ─────────────────────────────────────────────────────────────────
    for idx, row in filtered.iterrows():
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

        with st.container():
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

            # ── Star rating ───────────────────────────────────────────────
            stars_label = {0: "לא דורג", 1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐", 4: "⭐⭐⭐⭐", 5: "⭐⭐⭐⭐⭐"}
            col_r1, col_r2, col_r3, col_r4, col_r5, col_cur = st.columns([1,1,1,1,1,4])
            for star, col in zip([1,2,3,4,5], [col_r1,col_r2,col_r3,col_r4,col_r5]):
                btn_label = "⭐" if star <= current_rating else "☆"
                if col.button(btn_label, key=f"rate_{idx}_{star}"):
                    # Save rating to Sheets
                    try:
                        client = get_gspread_client()
                        if client:
                            ws = client.open_by_key(SPREADSHEET_ID).worksheet("Results")
                            all_vals = ws.get_all_values()
                            headers = all_vals[0] if all_vals else []
                            # Add rating column if missing
                            if "rating" not in headers:
                                ws.update_cell(1, len(headers)+1, "rating")
                                rating_col = len(headers)+1
                            else:
                                rating_col = headers.index("rating") + 1
                            # Find the row by link
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
                col_cur.caption(f"דירוג: {stars_label[current_rating]}")
            st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)


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
            show_inactive = st.checkbox("הצג גם לא פעילים / Show inactive")
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
            st.subheader(f"➕ {t('add')} Organization")
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
                    st.error("Name is required")


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
            st.subheader(f"➕ {t('add')} Keyword")
            new_kw = st.text_input(t("keywords"), placeholder="e.g. protesta Israel Lima")
            new_weight = st.select_slider(t("weight"), options=[1, 2, 3], value=2,
                                          help="1=Low, 2=Medium, 3=High")
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
                    st.error("Keyword cannot be empty")


# ─── Page: Settings ───────────────────────────────────────────────────────────

def page_settings():
    st.header(t("page_settings"))
    settings = load_settings()

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

        st.subheader(f"📊 Auto-Reports")
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
    st.subheader(f"📋 {t('last_scan')} Log")
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
        label = f"שבוע אחרון / Last 7 days"
    elif period == t("monthly"):
        cutoff = now - pd.Timedelta(days=30)
        label = f"חודש אחרון / Last 30 days"
    else:
        cutoff = now - pd.Timedelta(days=365)
        label = f"שנה אחרונה / Last 365 days"

    if "ts_parsed" in df.columns:
        df_period = df[df["ts_parsed"] >= cutoff]
    else:
        df_period = df

    st.caption(f"📅 {label} — {len(df_period)} ממצאים")

    # ── KPIs ──────────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("total"), len(df_period))
    alerts = len(df_period[df_period.get("is_alert", pd.Series()).astype(str).str.upper() == "YES"]) if "is_alert" in df_period else 0
    col2.metric(t("alerts_count"), alerts)
    avg = df_period["relevance_score"].mean() if "relevance_score" in df_period else 0
    col3.metric(t("avg_score"), f"{avg:.1f}" if avg else "—")
    high = len(df_period[df_period["relevance_score"] >= 8]) if "relevance_score" in df_period else 0
    col4.metric("🔴 Critical (8+)", high)

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📅 Findings over time")
        if "ts_parsed" in df_period.columns and not df_period.empty:
            by_day = df_period.groupby(df_period["ts_parsed"].dt.date).size().reset_index()
            by_day.columns = ["date", "count"]
            st.bar_chart(by_day.set_index("date"))
        else:
            st.info(t("no_data"))

    with col_right:
        st.subheader("🏷️ Event Types")
        if "event_type" in df_period.columns and not df_period.empty:
            by_type = df_period["event_type"].value_counts().reset_index()
            by_type.columns = ["event_type", "count"]
            by_type["event_type"] = by_type["event_type"].map(lambda x: event_label(x))
            st.bar_chart(by_type.set_index("event_type"))
        else:
            st.info(t("no_data"))

    # Score distribution
    if "relevance_score" in df_period.columns and not df_period.empty:
        st.subheader("📊 Score Distribution")
        buckets = pd.cut(df_period["relevance_score"],
                         bins=[0, 2, 4, 6, 8, 10],
                         labels=["1-2", "3-4", "5-6", "7-8", "9-10"])
        dist = buckets.value_counts().sort_index().reset_index()
        dist.columns = ["Score Range", "Count"]
        st.bar_chart(dist.set_index("Score Range"))

    # Top findings table
    st.subheader(f"🔝 Top 10 Findings")
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
            with st.spinner("Sending..."):
                try:
                    from summary_runner import run as run_summary
                    period_map = {
                        t("weekly"): "weekly",
                        t("monthly"): "monthly",
                        t("annual"): "annual",
                    }
                    run_summary(period_map.get(period, "weekly"))
                    st.success("✅ Report sent!")
                except Exception as e:
                    st.error(f"Failed: {e}")
    with col_info:
        st.caption("השלח דוח מסכם למייל / Send summary email with charts and top findings")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # Init session state
    if "ui_lang" not in st.session_state:
        st.session_state["ui_lang"] = "he"

    # RTL CSS for Hebrew
    if get_ui_lang() == "he":
        st.markdown("""
        <style>
            .stMarkdown, .stText, p, li { direction: rtl; text-align: right; }
            .stMetric { direction: rtl; }
        </style>
        """, unsafe_allow_html=True)

    page = render_sidebar()

    if page == t("page_findings"):
        page_findings()
    elif page == t("page_orgs"):
        page_organizations()
    elif page == t("page_keywords"):
        page_keywords()
    elif page == t("page_settings"):
        page_settings()
    elif page == t("page_reports"):
        page_reports()


if __name__ == "__main__":
    main()
