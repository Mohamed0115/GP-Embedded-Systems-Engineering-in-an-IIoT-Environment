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
                user = st.text_input("Username", placeholder="admin")
                pwd = st.text_input("Password", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Sign In", use_container_width=True)
                
                if submit:
                    if user and pwd:
                        with st.spinner("Authenticating..."):
                            time.sleep(1)
                        if user.lower() == "admin" and pwd != "admin123":
                            st.error("Invalid Admin password. Access Denied.")
                            st.stop()
                            
                        st.session_state.username = user
                        
                        # Security Check: Assign roles dynamically
                        if user.lower() == "admin" and pwd == "admin123":
                            st.session_state.user_role = "Admin"
                        else:
                            st.session_state.user_role = "Engineer"
                            
                        # Force a clean routing state so previous sessions don't leak over
                        st.session_state.current_view = "Dashboard 📊"
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Please enter both username and password")
