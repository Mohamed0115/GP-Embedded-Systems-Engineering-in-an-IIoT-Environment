import streamlit as st
from datetime import datetime
import uuid as _uuid

# ===== Server-side session cache (survives page refreshes) =====
# This dict lives in the server process memory. Keys are session tokens
# stored in st.query_params. Lost only when the Streamlit server restarts.
@st.cache_resource
def _get_session_store():
    """Return a mutable dict shared across all reruns (but NOT across server restarts)."""
    return {}

def save_session_to_cache():
    """Persist current login state to the server-side cache."""
    store = _get_session_store()
    token = st.session_state.get("_session_token")
    if not token:
        token = _uuid.uuid4().hex
        st.session_state._session_token = token
    store[token] = {
        "logged_in": st.session_state.get("logged_in", False),
        "username": st.session_state.get("username"),
        "user_role": st.session_state.get("user_role"),
    }
    # Put token in query params so it survives refresh
    st.query_params["t"] = token

def restore_session_from_cache():
    """Re-hydrate session_state from cached data if a token is in query_params."""
    token = st.query_params.get("t")
    if not token:
        return False
    store = _get_session_store()
    data = store.get(token)
    if data and data.get("logged_in"):
        st.session_state.logged_in = True
        st.session_state.username = data["username"]
        st.session_state.user_role = data["user_role"]
        st.session_state._session_token = token
        return True
    return False

def clear_session_cache():
    """Remove cached session data and clear query_params on logout."""
    token = st.session_state.get("_session_token")
    if token:
        store = _get_session_store()
        store.pop(token, None)
    st.query_params.clear()

def init_app_state():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if "username" not in st.session_state: st.session_state.username = None
    if "users_data" not in st.session_state: st.session_state.users_data = {}
    if "current_view" not in st.session_state: st.session_state.current_view = "Dashboard 📊"
    if "theme" not in st.session_state: st.session_state.theme = "Dark"
    if "unified_activity_logs" not in st.session_state: st.session_state.unified_activity_logs = []

    # Try to restore session from cache if not already logged in
    if not st.session_state.logged_in:
        restore_session_from_cache()

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

# ===== Unified Activity Logging (cross-page) =====
# Used by admin panel to show all actions a user did across the entire website.
def log_user_activity(username, category, action, detail, status="Success"):
    """Append an activity log entry to the unified log.
    
    Args:
        username: The username who performed the action (e.g. 'admin', 'vib')
        category: Section of the app (e.g. 'GATEWAYS', 'DIAGNOSIS', 'ADMIN')
        action: Short action name (e.g. 'TAKE_READING', 'ADD_PLANT')
        detail: Human-readable detail string
        status: 'Success' or 'Failed'
    """
    if "unified_activity_logs" not in st.session_state:
        st.session_state.unified_activity_logs = []
    st.session_state.unified_activity_logs.append({
        "username": username,
        "category": category,
        "action": action,
        "detail": detail,
        "status": status,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

