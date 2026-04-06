import streamlit as st

st.set_page_config(page_title="OSINTAgent", page_icon="🔍", layout="wide")

if "loaded" not in st.session_state:
    st.session_state["loaded"] = True

st.title("🔍 OSINTAgent")
st.write("המערכת עובדת!")
st.write(f"Session: {id(st.session_state)}")
