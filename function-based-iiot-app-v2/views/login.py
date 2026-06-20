import streamlit as st
import time

def login_view():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #4A90E2; margin-top: 0;'>IIoT Platform Login</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #888; margin-bottom: 2rem;'>Enter credentials to access firm environment</p>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                user = st.text_input("Username", placeholder="")
                pwd = st.text_input("Password", type="password", placeholder="")
                submit = st.form_submit_button("Sign In", use_container_width=True)
                
                if submit:
                    if user and pwd:
                        with st.spinner("Authenticating..."):
                            time.sleep(1)
                        user_lower = user.lower()
                        users_db = {
                            "admin": {"pwd": "admin123", "role": "Admin System"},
                            "vib": {"pwd": "vib123", "role": "Vibration Engineer"},
                            "maint": {"pwd": "maint123", "role": "Maintenance Engineer"}
                        }
                        
                        if user_lower not in users_db or users_db[user_lower]["pwd"] != pwd:
                            st.error("Invalid username or password. Access Denied.")
                            st.stop()
                            
                        st.session_state.username = user
                        st.session_state.user_role = users_db[user_lower]["role"]
                            
                        # Force a clean routing state so previous sessions don't leak over
                        st.session_state.current_view = "Dashboard 📊"
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Please enter both username and password")
