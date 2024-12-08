import streamlit as st
from synology_api import filestation

fl = filestation.FileStation(
    ip_address=st.secrets["synology"]["host"],
    port=st.secrets["synology"]["port"],
    username=st.secrets["synology"]["username"],
    password=st.secrets["synology"]["password"],
    secure=True,
    cert_verify=True,
    dsm_version=7,
    debug=True,
    otp_code=None,
)


def upload_file(dest_path: str, file_path: str):
    result = fl.upload_file(
        dest_path=dest_path,
        file_path=file_path,
    )
    return result["success"]
