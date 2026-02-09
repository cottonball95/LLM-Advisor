import streamlit as st
from supabase import create_client, Client
import httpx

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

# Initialize Supabase client with error handling
try:
    supabase_url = st.secrets["supabase"]["url"]
    supabase_key = st.secrets["supabase"]["anon_key"]
    
    # Validate that secrets are not empty
    if not supabase_url or not supabase_key:
        st.error("❌ Supabase configuration is missing or empty. Please check your `.streamlit/secrets.toml` file.")
        st.stop()
    
    # Debug: Show URL being used (can be removed later)
    with st.sidebar:
        st.caption(f"Connecting to: {supabase_url[:30]}...")
    
    sb: Client = create_client(supabase_url, supabase_key)
except KeyError as e:
    st.error(f"❌ Missing Supabase configuration in secrets: {e}")
    st.info("Please ensure your `.streamlit/secrets.toml` file contains:\n```toml\n[supabase]\nurl = \"https://YOUR-PROJECT.supabase.co\"\nanon_key = \"YOUR_ANON_KEY\"\n```")
    st.stop()
except Exception as e:
    st.error(f"❌ Failed to initialize Supabase client: {e}")
    st.stop()

# -------------------------
# Login helper
# -------------------------
def check_login(username: str, password: str):
    """
    Checks the Supabase `users` table for a matching username + password.
    Returns a dict with username, full_name, and role if found, else None.
    """
    try:
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
    except httpx.ConnectError as e:
        supabase_url = st.secrets["supabase"]["url"]
        error_msg = f"❌ **Connection Error**: Cannot connect to Supabase.\n\n"
        error_msg += f"**URL being used**: `{supabase_url}`\n\n"
        error_msg += "**Possible causes:**\n"
        error_msg += "1. **Supabase project is paused** (free tier projects pause after inactivity)\n"
        error_msg += "   → Go to https://supabase.com/dashboard and resume your project\n"
        error_msg += "2. **Network/DNS issues** - Check your internet connection\n"
        error_msg += "3. **Incorrect URL** - Verify the URL in your Supabase dashboard\n"
        error_msg += f"\n**Error details**: {str(e)}"
        st.error(error_msg)
        return None
    except Exception as e:
        st.error(f"❌ **Login Error**: {str(e)}")
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
