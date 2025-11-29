import streamlit as st
from supabase import create_client, Client

# -------------------------
# Streamlit page setup
# -------------------------
st.set_page_config(
    page_title="AI Academic Advisor Login",
    page_icon="🎓",
    layout="centered"
)
st.title("🎓 AI Academic Advisor Login")

# -------------------------
# Supabase Client (Auth + Users table)
# -------------------------
# Expect these in Streamlit secrets (both local .streamlit/secrets.toml and Streamlit Cloud):
# [supabase]
# url = "https://YOUR-PROJECT.supabase.co"
# anon_key = "YOUR_ANON_KEY"
sb: Client = create_client(
    st.secrets["supabase"]["url"],
    st.secrets["supabase"]["anon_key"]
)

# -------------------------
# Login helper
# -------------------------
def check_login(username: str, password: str):
    """
    Checks the Supabase `users` table for a matching username + password.
    Returns a dict with username, full_name, and role if found, else None.
    """
    res = (
        sb.table("users")
        .select("username, full_name, role")
        .eq("username", username)
        .eq("password", password)  # plain text by prof requirement
        .single()
        .execute()
    )

    if res.data:
        return {
            "username": res.data["username"],
            "full_name": res.data["full_name"],
            "role": res.data["role"],
        }
    return None

# -------------------------
# Session + UI
# -------------------------
if "user" not in st.session_state:
    st.session_state["user"] = None

# If already logged in, show shortcuts
if st.session_state["user"]:
    st.success(
        f"Already logged in as {st.session_state['user']['full_name']} "
        f"({st.session_state['user']['role']})"
    )
    st.sidebar.page_link("pages/1_Advisor_Dashboard.py", label="Go to Advisor Dashboard")
    st.sidebar.page_link("pages/2_Student_Dashboard.py", label="Go to Student Dashboard")
    st.stop()

# Login form
username_input = st.text_input("Username")
password_input = st.text_input("Password", type="password")

if st.button("Login"):
    if not username_input or not password_input:
        st.error("Please enter both username and password.")
    else:
        user = check_login(username_input.strip(), password_input.strip())
        if user:
            st.session_state["user"] = user
            st.success(f"Welcome, {user['full_name']}!")

            if user["role"] == "advisor":
                st.switch_page("pages/1_Advisor_Dashboard.py")
            else:
                st.switch_page("pages/2_Student_Dashboard.py")
        else:
            st.error("Invalid username or password.")
