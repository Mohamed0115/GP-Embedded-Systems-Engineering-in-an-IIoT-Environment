import streamlit as st
from datetime import datetime

def init_app_state():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if "username" not in st.session_state: st.session_state.username = None
    if "users_data" not in st.session_state: st.session_state.users_data = {}
    if "current_view" not in st.session_state: st.session_state.current_view = "Dashboard 📊"
    if "theme" not in st.session_state: st.session_state.theme = "Dark"

def get_user_data():
    user = st.session_state.username
    if user not in st.session_state.users_data:
        st.session_state.users_data[user] = {
            "history": [],
            "machines": ["Motor A", "Pump B"],
            "ita_connected_list": [],
            "last_ita_reading": None,
            "last_ctc_data": None,
            "show_fft": False,
            "show_rms": False
        }
    return st.session_state.users_data[user]

def add_to_history(gateway, operation, status):
    usr_data = get_user_data()
    usr_data["history"].insert(0, {
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Gateway": gateway,
        "Operation": operation,
        "Status": status
    })
    usr_data["history"] = usr_data["history"][:5]
