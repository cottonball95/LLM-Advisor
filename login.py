import streamlit as st
import psycopg2
import hashlib

import time

def get_conn():
    for attempt in range(3):  # retry up to 3 times
        try:
            return psycopg2.connect(
                "postgresql://postgres:AIscheduler1!@db.lagyctcgaqulkpmflcjs.supabase.co:5432/postgres?sslmode=require"
            )
        except psycopg2.OperationalError as e:
            if attempt < 2:
                time.sleep(2)
            else:
                raise e

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# top of login.py
import streamlit as st
from supabase import create_client, Client

sb: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["anon_key"])

def check_login(username, password):
    # Plain text by prof requirement; OK for class demo
    res = sb.table("users")\
            .select("username, full_name, role")\
            .eq("username", username)\
            .eq("password", password)\
            .single()\
            .execute()

    if res.data:
        return {
            "username": res.data["username"],
            "full_name": res.data["full_name"],
            "role": res.data["role"],
        }
    return None




st.set_page_config(page_title="AI Academic Advisor Login", page_icon="🎓", layout="centered")
st.title("🎓 AI Academic Advisor Login")

if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"]:
    st.success(f"Already logged in as {st.session_state['user']['full_name']} ({st.session_state['user']['role']})")
    st.sidebar.page_link("pages/1_Advisor_Dashboard.py", label="Go to Advisor Dashboard")
    st.sidebar.page_link("pages/2_Student_Dashboard.py", label="Go to Student Dashboard")
    st.stop()

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user = check_login(username, password)
    if user:
        st.session_state["user"] = user
        st.success(f"Welcome, {user['full_name']}!")
        if user["role"] == "advisor":
            st.switch_page("pages/1_Advisor_Dashboard.py")
        else:
            st.switch_page("pages/2_Student_Dashboard.py")
    else:
        st.error("Invalid username or password.")
