
import streamlit as st

# Setup Page Config first before any other Streamlit commands!
st.set_page_config(
    page_title="IIoT Gateway Monitor",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Core imports
from core.state_manager import init_app_state
from core.theme_engine import apply_theme
from hardware.gateway_bridge import ita, ctc

# View imports
from views.login import login_view
from views.dashboard import dashboard_view
from views.ita_gateway import ita_gateway_view
from views.ctc_gateway import ctc_gateway_view
from views.machines import machines_view

# Initialize states
ita.init_ita_state()
ctc.init_ctc_state()
init_app_state()

# Theme apply
apply_theme()

# Main Router
if not st.session_state.logged_in:
    login_view()
else:
    with st.sidebar:
        st.image("https://openautomationsoftware.com/wp-content/uploads/2021/11/blog_iiot.png", width=60)
        st.markdown(f"<h3 style='margin-top: 5px;'>Welcome, <span class='gold-user'>{st.session_state.username}</span></h3>", unsafe_allow_html=True)
        st.markdown("<hr style='border: 1px solid rgba(100,100,100,0.2);'>", unsafe_allow_html=True)
        
        menu_items = ["Dashboard 📊", "ITA-110 Gateway ⚙️", "CTC Connect 📡", "Machines & Diagnosis 🏭"]
        for item in menu_items:
            if st.button(item, key=f"nav_{item}", use_container_width=True):
                st.session_state.current_view = item
                st.rerun()
                
        st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
        
        thm_toggle = st.toggle("Enable Light Mode", value=(st.session_state.get('theme', 'Dark') == 'Light'))
        new_theme = "Light" if thm_toggle else "Dark"
        if new_theme != st.session_state.get('theme', 'Dark'):
            st.session_state.theme = new_theme
            st.rerun()
            
        st.markdown("<hr style='border: 1px solid rgba(100,100,100,0.2);'>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()

    # Content Router
    if st.session_state.current_view == "Dashboard 📊":
        dashboard_view()
    elif st.session_state.current_view == "ITA-110 Gateway ⚙️":
        ita_gateway_view()
    elif st.session_state.current_view == "CTC Connect 📡":
        ctc_gateway_view()
    elif st.session_state.current_view == "Machines & Diagnosis 🏭":
        machines_view()
