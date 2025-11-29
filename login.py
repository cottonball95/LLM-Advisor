import streamlit as st
import psycopg2

# ==========================
# DB CONNECTION (same as dashboards)
# ==========================
def get_conn():
    return psycopg2.connect(
        "postgresql://postgres:AIscheduler1!@db.lagyctcgaqulkpmflcjs.supabase.co:5432/postgres?sslmode=require"
    )

# ==========================
# LOGIN HELPER
# ==========================
def check_login(username: str, password: str):
    """
    Look up the user in the 'users' table using plain-text password
    (per your professor's requirement for the class project).
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT username, full_name, role
        FROM users
        WHERE username = %s AND password = %s;
        """,
        (username, password),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return {
            "username": row[0],
            "full_name": row[1],
            "role": row[2],
        }
    return None

# ==========================
# STREAMLIT PAGE
# ==========================
st.set_page_config(page_title="LLM Advisor - Login", page_icon="🎓", layout="centered")
st.title("🎓 Large Language Model-Based Academic Advising Assistant")
st.subheader("Login")

# Initialize session
if "user" not in st.session_state:
    st.session_state["user"] = None

# If already logged in, show who & offer links
if st.session_state["user"]:
    u = st.session_state["user"]
    st.info(f"Already logged in as **{u['full_name']}** ({u['role']}).")
    if u["role"] == "student":
        st.page_link("pages/2_Student_Dashboard.py", label="➡ Go to Student Dashboard")
    elif u["role"] == "advisor":
        st.page_link("pages/1_Advisor_Dashboard.py", label="➡ Go to Advisor Dashboard")
    st.divider()

# Login form
with st.form("login_form"):
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Log in")

if submitted:
    if not username_input or not password_input:
        st.error("Please enter both username and password.")
    else:
        user = check_login(username_input.strip(), password_input.strip())
        if user:
            st.session_state["user"] = user
            st.success(f"Welcome, {user['full_name']}! Logged in as {user['role']}.")

            # Redirect based on role
            if user["role"] == "student":
                st.switch_page("pages/2_Student_Dashboard.py")
            elif user["role"] == "advisor":
                st.switch_page("pages/1_Advisor_Dashboard.py")
            else:
                st.info("Logged in, but role is not mapped to a specific page.")
        else:
            st.error("Invalid username or password. Please try again.")

st.markdown("---")
st.caption("Use your assigned demo credentials for this ENGT 434/435 project.")
