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

import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="iiot",
        user="postgres",
        password="hassan",
        port="5432"
    )


def load_users():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            id,
            full_name,
            username,
            email,
            phone_number,
            role,
            created_at,
            last_login
        FROM users
        ORDER BY id
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    users = []

    for row in rows:
        users.append({
            "id": row["id"],
            "name": row["full_name"],
            "username": row["username"],
            "email": row["email"],
            "contact": row["phone_number"] or "",
            "password": "********",
            "role": row["role"]
        })

    return users

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

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM users WHERE id = %s",
        (user_id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    log_user_activity(
        user_id,
        "DELETE_USER",
        f"Deleted user {user_id}",
        "Success"
    )

def admin_panel_v2_view():
    """Main view function for the Admin Panel V2 with custom component."""
    st.session_state.mock_users = load_users()
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
        password = st.text_input(" Password", type="password")
        role = st.selectbox("Assign Role", ["Maintenance Engineer", "Vibration Engineer", "Admin System"])
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Save Account", type="primary", use_container_width=True):
            if not name or not username or not password:
                st.error("Name, Username, and Password are required fields.")
            else:
                new_id = f"EMP-{str(uuid.uuid4())[:3].upper()}"
                #-------------------TO Add new user
                conn = get_db_connection()
                cur = conn.cursor()

                cur.execute("""
                    INSERT INTO users (
                        full_name,
                        role,
                        username,
                        email,
                        phone_number,
                        password
                    )
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (
                    name,
                    role,
                    username,
                    email,
                    contact,
                    password
                ))

                conn.commit()
                cur.close()
                conn.close()
                #------------------------
                log_user_activity(new_id, "CREATE_USER", f"Created user {name} ({username}) with role {role}", "Success")
                st.success("Account created successfully!")
                time.sleep(0.5)
                st.rerun()

    # ===== Edit Account dialog =====
    @st.dialog("✏️ Edit Account")
    def edit_user_dialog(user_id):
        """Update credentials for an existing user."""
        idx = next(
            (
                i for i, u in enumerate(st.session_state.mock_users)
                if str(u["id"]) == str(user_id)
            ),
            None
        )
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
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE users
                SET
                    full_name = %s,
                    username = %s,
                    email = %s,
                    phone_number = %s,
                    role = %s,
                    password = %s
                WHERE id = %s
            """, (
                name,
                username,
                email,
                contact,
                role,
                password,
                user_id
            ))

            conn.commit()
            cur.close()
            conn.close()
            st.success("Account updated successfully!")
            time.sleep(0.5)
            st.rerun()

    def get_user_details(user_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                id,
                full_name,
                username,
                email,
                role,
                created_at,
                last_login
            FROM users
            WHERE id = %s
        """, (user_id,))

        user = cur.fetchone()

        cur.close()
        conn.close()

        return user
    # ===== Change 5b: Per-User Activity Logs dialog =====
    #
    @st.dialog("📋 User Information", width="large")
    def view_user_logs_dialog(user_id, user_name):

        user = get_user_details(user_id)

        if not user:
            st.error("User not found.")
            return

        st.markdown(f"### {user['full_name']}")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("User ID", user["id"])
            st.metric("Username", user["username"])
            st.metric("Role", user["role"])

        with col2:
            st.metric(
                "Created At",
                user["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                if user["created_at"] else "N/A"
            )

            st.metric(
                "Last Login",
                user["last_login"].strftime("%Y-%m-%d %H:%M:%S")
                if user["last_login"] else "Never"
            )

        st.divider()

        st.markdown("#### Account Information")

        st.write(f"**Email:** {user['email']}")

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
