import streamlit as st
import time
import psycopg2


# ==========================================
# DATABASE CONNECTION
# ==========================================
def get_connection():

    postgres_password = "hassan"

    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="iiot",
        user="postgres",
        password=postgres_password
    )


    return conn


# ==========================================
# USER AUTHENTICATION
# ==========================================
def authenticate_user(username, entered_password):

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT username, role
        FROM users
        WHERE username = %s
        AND password = %s
    """

    cur.execute(query, (username, entered_password))

    result = cur.fetchone()


    cur.close()
    conn.close()

    return result


# ==========================================
# LOGIN PAGE
# ==========================================
def login_view():

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:

        st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)

        with st.container(border=True):

            st.markdown(
                "<h2 style='text-align: center; color: #4A90E2;'>IIoT Platform Login</h2>",
                unsafe_allow_html=True
            )

            st.markdown(
                "<p style='text-align: center; color: #888;'>Enter credentials to access firm environment</p>",
                unsafe_allow_html=True
            )

            with st.form("login_form"):

                username = st.text_input("Username")
                entered_password = st.text_input(
                    "Password",
                    type="password"
                )

                submit = st.form_submit_button(
                    "Sign In",
                    use_container_width=True
                )

                if submit:

                    if not username or not entered_password:
                        st.error(
                            "Please enter both username and password"
                        )
                        return

                    with st.spinner("Authenticating..."):
                        time.sleep(1)

                    result = authenticate_user(
                        username,
                        entered_password
                    )

                    if result is None:
                        st.error(
                            "Invalid username or password. Access Denied."
                        )
                        return

                    db_username, role = result

                    st.session_state.username = db_username
                    st.session_state.user_role = role
                    st.session_state.logged_in = True
                    st.session_state.current_view = "Dashboard 📊"

                    st.rerun()