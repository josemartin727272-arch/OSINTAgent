import streamlit as st
import json
import os

st.set_page_config(page_title="OSINTAgent", page_icon="🔍", layout="wide")
st.title("🔍 OSINTAgent")

try:
    import gspread
    from google.oauth2.service_account import Credentials
    creds_raw = st.secrets.get("GOOGLE_SHEETS_CREDENTIALS_JSON", "")
    if creds_raw:
        st.success("✅ Sheets connected")
    else:
        st.warning("No credentials")
except Exception as e:
    st.error(f"Error: {e}")
