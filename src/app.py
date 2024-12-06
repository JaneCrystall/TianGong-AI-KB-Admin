import streamlit as st

from module.password import check_password

st.set_page_config(
    page_title="TianGong Knowledge Base Admin",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="static/favicon.ico",
)

if check_password():
    st.success('Password correct!', icon="✅")
