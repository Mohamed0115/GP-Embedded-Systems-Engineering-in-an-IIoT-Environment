import streamlit as st
import time
import uuid

def init_users_state():
    if 'mock_users' not in st.session_state:
        st.session_state.mock_users = [
            {"id": "EMP-001", "name": "System Administrator", "username": "admin", "email": "admin@iiot.local", "contact": "+1-555-0101", "password": "••••••••", "role": "Admin"},
            {"id": "EMP-002", "name": "Ahmed Engineer", "username": "engineer1", "email": "ahmed@iiot.local", "contact": "+20123456789", "password": "••••••••", "role": "Engineer"},
            {"id": "EMP-003", "name": "Guest Operator", "username": "guest", "email": "guest@iiot.local", "contact": "", "password": "••••••••", "role": "Viewer"}
        ]

def delete_user_callback(user_id):
    st.session_state.mock_users = [u for u in st.session_state.mock_users if u['id'] != user_id]

@st.dialog("➕ Add New Account")
def add_user_dialog():
    st.markdown("Register a new employee and assign their system role.")
    name = st.text_input("Full Name", placeholder="e.g. Mohamed Ahmed")
    username = st.text_input("Username", placeholder="e.g. mohamed.a")
    email = st.text_input("Email Address", placeholder="e.g. email@firm.com")
    contact = st.text_input("Contact Info", placeholder="(Optional)")
    password = st.text_input("Temporary Password", type="password")
    role = st.selectbox("Assign Role", ["Viewer", "Engineer", "Admin"])
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Save Account", type="primary", use_container_width=True):
        if not name or not username or not password:
            st.error("Name, Username, and Password are required fields.")
        else:
            new_id = f"EMP-{str(uuid.uuid4())[:3].upper()}"
            st.session_state.mock_users.append({
                "id": new_id, "name": name, "username": username,
                "email": email, "contact": contact, "password": "••••••••", "role": role
            })
            st.success("Account created successfully!")
            time.sleep(0.5)
            st.rerun()

@st.dialog("✏️ Edit Account")
def edit_user_dialog(user_id):
    idx = next((i for i, u in enumerate(st.session_state.mock_users) if u['id'] == user_id), None)
    if idx is None: return
    user = st.session_state.mock_users[idx]
    
    st.markdown(f"Update credentials for **{user['name']}** (`{user['id']}`)")
    name = st.text_input("Full Name", value=user['name'])
    username = st.text_input("Username", value=user['username'])
    email = st.text_input("Email Address", value=user.get('email', ''))
    contact = st.text_input("Contact Info", value=user.get('contact', ''))
    password = st.text_input("Password", value=user.get('password', '••••••••'), type="password")
    role_opts = ["Viewer", "Engineer", "Admin"]
    role_idx = role_opts.index(user['role']) if user['role'] in role_opts else 0
    role = st.selectbox("Assign Role", role_opts, index=role_idx)
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Update Account", type="primary", use_container_width=True):
        st.session_state.mock_users[idx]['name'] = name
        st.session_state.mock_users[idx]['username'] = username
        st.session_state.mock_users[idx]['contact'] = contact
        st.session_state.mock_users[idx]['email'] = email
        st.session_state.mock_users[idx]['password'] = password
        st.session_state.mock_users[idx]['role'] = role
        st.success("Account updated successfully!")
        time.sleep(0.5)
        st.rerun()

def admin_panel_view():
    init_users_state()
    
    # Extra security check just to be safe
    if st.session_state.get("user_role") != "Admin":
        st.error("Access Denied: You do not have permission to view this page.")
        return

    # Top Header
    c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
    with c1:
        st.title("🛡️ User Management")
        st.markdown("Manage system access, assign roles, and configure employee credentials.")
    with c2:
        if st.button("➕ Add Account", type="primary", use_container_width=True):
            add_user_dialog()

    st.markdown("---")
    
    # Search Bar - Wrapped in a column to make it smaller like Figma
    col_search, _ = st.columns([1, 2])
    with col_search:
        search_term = st.text_input("🔍 Search", placeholder="Filter by Name, Username, or Email...", label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Header Row (Removed the raw HTML div that caused the empty box artifact)
    h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns([1.2, 2, 1.2, 1.5, 2, 1.5, 1, 0.8, 0.8], gap="small", vertical_alignment="center")
    h1.markdown("<div style='height: 28px; display: flex; align-items: center; font-weight: bold;'>ID</div>", unsafe_allow_html=True)
    h2.markdown("**Name**")
    h3.markdown("**Role**")
    h4.markdown("**Username**")
    h5.markdown("**Email**")
    h6.markdown("**Contact Info**")
    h7.markdown("**Password**")
    h8.markdown("**Edit**")
    h9.markdown("**Delete**")
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px; border-color: rgba(128,128,128,0.2);'>", unsafe_allow_html=True)
    
    # Filter Users
    filtered = [
        u for u in st.session_state.mock_users 
        if search_term.lower() in u['name'].lower() 
        or search_term.lower() in u['username'].lower() 
        or search_term.lower() in u.get('email', '').lower()
    ]
    
    # Render Rows
    if len(filtered) == 0:
        st.info("No accounts match your search query.")
    else:
        # Inject custom CSS specifically scoped to the Edit and Delete buttons so it doesn't break Streamlit globals!
        st.markdown("""
        <style>
        /* Squash all text margins to prevent markdown wrappers from bloating the row */
        .stMarkdown p {
            margin-bottom: 0px !important;
            padding-bottom: 0px !important;
        }
        div[data-testid="stVerticalBlock"] > div {
            padding-bottom: 0px !important;
            margin-bottom: 0px !important;
        }
        
        /* Forcefully override theme_engine.py button styles by using maximum CSS specificity */
        html body .stApp [data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-last-child(2) div[data-testid="stButton"] button {
            background-color: #0E7954 !important; 
            color: white !important; 
            font-weight: bold !important; 
            border: none !important; 
            min-height: 24px !important; 
            height: 24px !important; 
            border-radius: 4px !important; 
            padding: 0px 4px !important; 
            font-size: 11px !important;
            line-height: 1 !important;
        }
        html body .stApp [data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-last-child(2) div[data-testid="stButton"] button:hover { 
            opacity: 0.8 !important; 
        }
        
        html body .stApp [data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-last-child(1) div[data-testid="stButton"] button {
            background-color: #9C2E2A !important; 
            color: white !important; 
            font-weight: bold !important; 
            border: none !important; 
            min-height: 24px !important; 
            height: 24px !important; 
            border-radius: 4px !important; 
            padding: 0px 4px !important; 
            font-size: 11px !important;
            line-height: 1 !important;
        }
        html body .stApp [data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-last-child(1) div[data-testid="stButton"] button:hover { 
            opacity: 0.8 !important; 
        }
        
        /* Force the inner markdown container to remove padding so our 40px pole works perfectly */
        html body .stApp div[data-testid="stMarkdownContainer"] {
            line-height: 1 !important;
        }
        
        /* OVERRIDE theme_engine.py massive hr margins that were blowing out the row height */
        html body .stApp hr, html body .stApp div[data-testid="stMarkdownContainer"] hr {
            margin: 0px 0px !important;
            padding: 0px 0px !important;
        }
        
        /* Reduce gap between rows and squash all potential margins */
        html body .stApp [data-testid="stVerticalBlock"] > div {
            gap: 0rem !important;
            padding-bottom: 0px !important;
            margin-bottom: 0px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        for user in filtered:
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.2, 2, 1.2, 1.5, 2, 1.5, 1, 0.8, 0.8], vertical_alignment="center", gap="small")
            
            # Determine Badge Color
            if user['role'] == "Admin": color = "#FF4B4B"
            elif user['role'] == "Engineer": color = "#4A90E2"
            else: color = "#00D26A"
            badge = f"<span style='background-color:{color}; color:white; padding:2px 6px; border-radius:8px; font-size:0.7em; display:inline-block;'>{user['role']}</span>"
            
            # Use the 28px invisible pole inside col1 to force the row height perfectly, and style the ID like code
            id_html = f"<div style='height: 28px; display: flex; align-items: center;'><span style='background-color: rgba(128,128,128,0.2); padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px;'>{user['id']}</span></div>"
            col1.markdown(id_html, unsafe_allow_html=True)
            
            col2.markdown(f"<div style='line-height: 1.2; font-size: 14px;'><strong>{user['name']}</strong></div>", unsafe_allow_html=True)
            col3.markdown(badge, unsafe_allow_html=True)
            col4.markdown(f"<span style='font-size: 14px;'>{user['username']}</span>", unsafe_allow_html=True)
            col5.markdown(f"<span style='font-size: 14px;'>{user.get('email') if user.get('email') else '-'}</span>", unsafe_allow_html=True)
            col6.markdown(f"<span style='font-size: 14px; color: gray;'>{user.get('phone', '+1 (555) 000-0000')}</span>", unsafe_allow_html=True)
            col7.markdown("<span style='color: gray; font-size: 14px;'>••••••••</span>", unsafe_allow_html=True)
            
            with col8:
                if st.button("EDIT", key=f"edit_{user['id']}", use_container_width=True):
                    edit_user_dialog(user['id'])
            with col9:
                st.button("DELETE", key=f"del_{user['id']}", use_container_width=True, on_click=delete_user_callback, args=(user['id'],))
                
            st.markdown("<hr style='margin:0; border-color: rgba(128,128,128,0.2);'>", unsafe_allow_html=True) # Row underline separator
