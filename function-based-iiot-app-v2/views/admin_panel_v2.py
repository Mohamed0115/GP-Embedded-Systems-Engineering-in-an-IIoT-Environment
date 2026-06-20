"""
Admin Panel V2 — Custom Streamlit Component Version
====================================================
Replaces admin_panel.py with a Tailwind-styled custom component table.
The original admin_panel.py is NOT modified — this is a new file.

Features:
- Beautiful custom component table with role badges, search, edit/delete/logs buttons
- Per-user activity logs (Change 5b) with color-coded log dialog
- Add/Edit user dialogs remain as Streamlit @st.dialog
"""

import streamlit as st
import time
import uuid
import datetime
import os

# ===== Initialize users state =====
def init_users_state():
    """Create mock users if not already in session state."""
    if 'mock_users' not in st.session_state:
        st.session_state.mock_users = [
            {"id": "EMP-001", "name": "System Administrator", "username": "admin", "email": "admin@iiot.local", "contact": "+1-555-0101", "password": "••••••••", "role": "Admin System"},
            {"id": "EMP-002", "name": "Ahmed Engineer", "username": "vib", "email": "ahmed@iiot.local", "contact": "+20123456789", "password": "••••••••", "role": "Vibration Engineer"},
            {"id": "EMP-003", "name": "Guest Operator", "username": "maint", "email": "guest@iiot.local", "contact": "", "password": "••••••••", "role": "Maintenance Engineer"}
        ]

# ===== Initialize user activity logs =====
def init_activity_logs():
    """Create activity logs list if not already in session state."""
    if 'user_activity_logs' not in st.session_state:
        st.session_state.user_activity_logs = []

# ===== Log a user activity =====
def log_user_activity(user_id, action, detail, status="Success"):
    """Append an activity log entry for a specific user."""
    init_activity_logs()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.user_activity_logs.append({
        "user_id": user_id,
        "timestamp": timestamp,
        "action": action,
        "detail": detail,
        "status": status
    })

# ===== Delete user callback =====
def delete_user_callback(user_id):
    """Remove a user from session state by their ID."""
    st.session_state.mock_users = [u for u in st.session_state.mock_users if u['id'] != user_id]
    log_user_activity(user_id, "DELETE_USER", f"Deleted user {user_id}", "Success")


def admin_panel_v2_view():
    """Main view function for the Admin Panel V2 with custom component."""
    init_users_state()
    init_activity_logs()
    
    # ===== Security check =====
    if st.session_state.get("user_role") != "Admin System":
        st.error("Access Denied: You do not have permission to view this page.")
        return

    # ===== Declare the custom component =====
    import streamlit.components.v1 as components
    
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    admin_component_path = os.path.join(parent_dir, "admin_component")
    admin_component = components.declare_component("admin_component", path=admin_component_path)

    # ===== Render the custom component, passing users data =====
    res = admin_component(
        users=st.session_state.mock_users,
        key="admin_panel_component"
    )

    # ===== React to component events =====
    if res is not None:
        comparable = {k: v for k, v in res.items() if k != '_ts'}
        last_comparable = {k: v for k, v in (st.session_state.get('last_admin_event') or {}).items() if k != '_ts'}
        if comparable != last_comparable or res.get('_ts') != (st.session_state.get('last_admin_event') or {}).get('_ts'):
            st.session_state.last_admin_event = res
            action = res["action"]
            user_id = res.get("user_id", "")
            extra = res.get("extra", "")
            
            # Immediate actions
            if action == "delete_user":
                delete_user_callback(user_id)
                st.rerun()
            
            # Modal actions
            else:
                st.session_state.pending_admin_action = {
                    "action": action,
                    "user_id": user_id,
                    "extra": extra
                }
                st.rerun()

    # ===============================================
    # ===== DIALOGS =====
    # ===============================================

    # ===== Add New Account dialog =====
    @st.dialog("➕ Add New Account")
    def add_user_dialog():
        """Register a new employee and assign their system role."""
        st.markdown("Register a new employee and assign their system role.")
        name = st.text_input("Full Name", placeholder="e.g. Mohamed Ahmed")
        username = st.text_input("Username", placeholder="e.g. mohamed.a")
        email = st.text_input("Email Address", placeholder="e.g. email@firm.com")
        contact = st.text_input("Contact Info", placeholder="(Optional)")
        password = st.text_input("Temporary Password", type="password")
        role = st.selectbox("Assign Role", ["Maintenance Engineer", "Vibration Engineer", "Admin System"])
            
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
                log_user_activity(new_id, "CREATE_USER", f"Created user {name} ({username}) with role {role}", "Success")
                st.success("Account created successfully!")
                time.sleep(0.5)
                st.rerun()

    # ===== Edit Account dialog =====
    @st.dialog("✏️ Edit Account")
    def edit_user_dialog(user_id):
        """Update credentials for an existing user."""
        idx = next((i for i, u in enumerate(st.session_state.mock_users) if u['id'] == user_id), None)
        if idx is None:
            st.error("User not found!")
            return
        user = st.session_state.mock_users[idx]
        
        st.markdown(f"Update credentials for **{user['name']}** (`{user['id']}`)")
        name = st.text_input("Full Name", value=user['name'])
        username = st.text_input("Username", value=user['username'])
        email = st.text_input("Email Address", value=user.get('email', ''))
        contact = st.text_input("Contact Info", value=user.get('contact', ''))
        password = st.text_input("Password", value=user.get('password', '••••••••'), type="password")
        role_opts = ["Maintenance Engineer", "Vibration Engineer", "Admin System"]
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
            log_user_activity(user_id, "EDIT_USER", f"Updated user {name} ({username}), role={role}", "Success")
            st.success("Account updated successfully!")
            time.sleep(0.5)
            st.rerun()

    # ===== Change 5b: Per-User Activity Logs dialog =====
    @st.dialog("📋 User Activity Logs", width="large")
    def view_user_logs_dialog(user_id, user_name):
        """Show color-coded activity logs for a specific user, same style as gateway logs."""
        st.markdown(f"#### Activity Logs for **{user_name}** (`{user_id}`)")
        
        # Filter logs for this user
        user_logs = [l for l in st.session_state.user_activity_logs if l.get("user_id") == user_id]
        
        if not user_logs:
            st.info(f"No activity logs recorded for {user_name}.")
        else:
            # Build color-coded HTML table matching gateway logs style
            log_rows = ""
            for log in reversed(user_logs):
                status = log.get("status", "")
                # Color code: green for success, red for failed, yellow for pending
                if status == "Success":
                    response_bg = "background-color: #dcfce7; color: #166534;"
                elif status == "Failed":
                    response_bg = "background-color: #fee2e2; color: #991b1b;"
                elif status == "Pending":
                    response_bg = "background-color: #fef3c7; color: #92400e;"
                else:
                    response_bg = ""
                log_rows += f"""<tr>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; white-space: nowrap;">{log.get('timestamp', '')}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; font-weight: 600;">{log.get('action', '')}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; {response_bg} border-radius: 4px;">{log.get('detail', '')}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; font-weight: 600; {response_bg}">{status}</td>
                </tr>"""
            
            log_html = f"""<div style="max-height: 400px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 8px;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f3f4f6; position: sticky; top: 0;">
                        <th style="padding: 10px 12px; text-align: left; font-size: 13px; font-weight: 600; border-bottom: 2px solid #d1d5db;">Timestamp</th>
                        <th style="padding: 10px 12px; text-align: left; font-size: 13px; font-weight: 600; border-bottom: 2px solid #d1d5db;">Action</th>
                        <th style="padding: 10px 12px; text-align: left; font-size: 13px; font-weight: 600; border-bottom: 2px solid #d1d5db;">Detail</th>
                        <th style="padding: 10px 12px; text-align: left; font-size: 13px; font-weight: 600; border-bottom: 2px solid #d1d5db;">Status</th>
                    </tr>
                </thead>
                <tbody>{log_rows}</tbody>
            </table></div>"""
            st.markdown(log_html, unsafe_allow_html=True)

    # ===============================================
    # ===== Trigger Pending Actions =====
    # ===============================================
    if getattr(st.session_state, "pending_admin_action", None):
        pending = st.session_state.pending_admin_action
        st.session_state.pending_admin_action = None
        
        if pending["action"] == "add_user":
            add_user_dialog()
        elif pending["action"] == "edit_user":
            edit_user_dialog(pending["user_id"])
        elif pending["action"] == "view_user_logs":
            view_user_logs_dialog(pending["user_id"], pending.get("extra", "Unknown"))
