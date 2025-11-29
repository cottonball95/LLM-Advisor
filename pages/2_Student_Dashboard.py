import streamlit as st
import psycopg2
import openai
import json
from datetime import datetime

# ==========================
# CONFIG
# ==========================
openai.api_key = st.secrets["openai"]["api_key"]


#import psycopg2

#def get_conn():
#    return psycopg2.connect(
#        "postgresql://postgres:AIscheduler1!@db.lagyctcgaqulkpmflcjs.supabase.co:5432/postgres?sslmode=require"
#    )

import psycopg2
import socket

def get_conn():
    return psycopg2.connect(st.secrets["connections"]["postgres_url"])



# ==========================
# PAGE SETUP
# ==========================
st.set_page_config(page_title="Student Dashboard", page_icon="🎓", layout="wide")
st.title("🎓 Student Dashboard")

# Verify login
if "user" not in st.session_state or not st.session_state["user"]:
    st.warning("⚠️ You must be logged in to view this page.")
    st.switch_page("login.py")

elif st.session_state["user"]["role"] != "student":
    st.error("🚫 Access denied. Student role required.")
    st.stop()

st.sidebar.success(f"Logged in as {st.session_state['user']['full_name']} ({st.session_state['user']['role']})")
st.sidebar.page_link("login.py", label="🔒 Log out", help="Return to login page.")

# ==========================
# DATABASE HELPERS
# ==========================
def get_programs():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT program_id, name, catalog_year FROM programs ORDER BY program_id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_program_data(program_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.section_id, s.parent_section_id, s.title, s.rule_type, s.n_required, s.min_credits,
               c.course_id, c.title, c.credits, c.prerequisites_expr, c.corequisites_csv, c.special_constraints_text
        FROM sections s
        LEFT JOIN courses c ON s.section_id = c.section_id
        WHERE s.program_id = %s
        ORDER BY s.section_id;
    """, (program_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# ==========================
# STUDENT INTERFACE
# ==========================
programs = get_programs()
if not programs:
    st.warning("No programs found. Please ask your advisor to add one first.")
    st.stop()

program_dict = {f"{p[1]} ({p[2]})": p[0] for p in programs}
selected_program = st.selectbox("Select Your Program", list(program_dict.keys()))
program_id = program_dict[selected_program]

data = get_program_data(program_id)
if not data:
    st.info("This program has no courses yet.")
    st.stop()

# Build a tree-like viewer for sections/courses
st.subheader("📘 Program Viewer")

sections = {}
for row in data:
    section_id, parent, title, rule, n_req, min_cr, cid, cname, credits, prereq, coreq, special = row
    if section_id not in sections:
        sections[section_id] = {
            "title": title, "parent": parent, "courses": [], "rule": rule,
            "n_required": n_req, "min_credits": min_cr
        }
    if cid:
        sections[section_id]["courses"].append((cid, cname, credits))

# recursive render
def render_section(sid, level=0):
    section = sections[sid]
    indent = "&nbsp;" * (level * 8)
    st.markdown(f"{indent}**📂 {section['title']}** — Rule: {section['rule'] or 'All required'}")
    for cid, cname, cr in section["courses"]:
        st.markdown(f"{indent}&nbsp;&nbsp;&nbsp;&nbsp;📘 {cid} — {cname} ({cr} cr)")
    for child_id, child in sections.items():
        if child["parent"] == sid:
            render_section(child_id, level + 1)

root_sections = [sid for sid, s in sections.items() if s["parent"] is None]
for sid in root_sections:
    render_section(sid)

st.divider()

# ✅ === Mark Completed Courses Section ===
st.markdown("### ✅ Mark Completed Courses")

conn = get_conn()
cur = conn.cursor()
cur.execute("SELECT course_id, title FROM courses;")
course_list = cur.fetchall()
cur.close()
conn.close()

# Load saved completed courses
try:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT course_id 
        FROM student_courses_completed 
        WHERE student_username = %s;
    """, (st.session_state["user"]["username"],))
    completed_courses = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
except Exception as e:
    st.warning(f"Couldn't load completed courses: {e}")
    completed_courses = []

# Course checkboxes
updated_completed = []
for course_id, title in course_list:
    checked = st.checkbox(f"{course_id} — {title}", value=(course_id in completed_courses))
    if checked:
        updated_completed.append(course_id)

# Save logic
if st.button("💾 Save Completed Courses"):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM student_courses_completed WHERE student_username = %s;", 
                    (st.session_state["user"]["username"],))
        if updated_completed:
            insert_values = [(st.session_state["user"]["username"], cid) for cid in updated_completed]
            cur.executemany("""
                INSERT INTO student_courses_completed (student_username, course_id)
                VALUES (%s, %s);
            """, insert_values)
        conn.commit()
        cur.close()
        conn.close()
        st.success(f"✅ Saved! ({len(updated_completed)} courses marked complete)")
    except Exception as e:
        st.error(f"Error saving courses: {e}")

total_courses = len(course_list)
completed_count = len(updated_completed)
st.info(f"📊 Progress: {completed_count}/{total_courses} courses completed")

# ==========================
# CONSTRAINTS + PLANNING
# ==========================
st.markdown("---")
st.header("🧠 AI Planner")

if "constraints" not in st.session_state:
    st.session_state["constraints"] = []

user_text = st.text_area("Enter your scheduling preferences or constraints:",
                         placeholder="e.g., I don’t want more than 4 classes per semester. Avoid physics and chemistry together.")

# --- Database helpers
def save_constraint_to_db(student_username, label, ctype):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO student_constraints (student_username, label, type)
        VALUES (%s, %s, %s);
    """, (student_username, label, ctype))
    conn.commit()
    cur.close()
    conn.close()

def delete_constraint_from_db(student_username, label):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM student_constraints WHERE student_username = %s AND label = %s;",
                (student_username, label))
    conn.commit()
    cur.close()
    conn.close()

def load_constraints_from_db(student_username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT label, type FROM student_constraints
        WHERE student_username = %s
        ORDER BY created_at;
    """, (student_username,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"label": r[0], "type": r[1]} for r in rows]

# Load constraints if not cached
if not st.session_state["constraints"]:
    st.session_state["constraints"] = load_constraints_from_db(st.session_state["user"]["username"])

# --- Apply constraints (OpenAI)
if st.button("Apply Constraints"):
    prompt = f"""
    You are an academic scheduling assistant. A student entered these preferences:
    "{user_text}"

    Convert this text into a structured JSON list of constraint 'chips'.
    Each chip should have: 'label' (short text) and 'type' (category, like max_courses, avoid_pair, no_summer, balance_load, etc.).
    Reply ONLY with valid JSON.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        raw_text = response.choices[0].message.content.strip()
        import re
        json_match = re.search(r"\[.*\]", raw_text, re.DOTALL)
        json_text = json_match.group(0) if json_match else raw_text
        new_constraints = json.loads(json_text)

        for c in new_constraints:
            if not any(x["label"] == c["label"] for x in st.session_state["constraints"]):
                st.session_state["constraints"].append(c)
                save_constraint_to_db(st.session_state["user"]["username"], c["label"], c["type"])
        st.success("✅ Constraints parsed and saved!")
    except Exception as e:
        st.error(f"Failed to parse constraints: {e}")

# --- Show constraints
if st.session_state["constraints"]:
    st.write("**Active Constraints:**")
    for c in st.session_state["constraints"]:
        col1, col2 = st.columns([8, 1])
        with col1:
            st.markdown(f"<div style='padding:6px 10px;background:#eef;border-radius:10px;display:inline-block;margin:3px;'>🔹 {c['label']} ({c['type']})</div>", unsafe_allow_html=True)
        with col2:
            if st.button("❌", key=f"del_{c['label']}"):
                delete_constraint_from_db(st.session_state["user"]["username"], c["label"])
                st.session_state["constraints"] = [x for x in st.session_state["constraints"] if x["label"] != c["label"]]
                st.rerun()

# ==============================
#   START TERM SELECTION + AI PLANNER
# ==============================
st.markdown("### 🎓 Select Your Starting Term")

current_year = datetime.now().year
years = list(range(current_year - 1, current_year + 5))
terms = ["Spring", "Summer", "Fall"]
term_options = [f"{term} {year}" for year in years for term in terms]

start_semester = st.selectbox(
    "Start planning from:",
    sorted(term_options, key=lambda x: (int(x.split()[1]), x.split()[0])),
    index=len(term_options)//2
)

# --- Only run planner if start_semester chosen
if not start_semester or start_semester.strip() == "":
    st.warning("⚠️ Please select your starting semester before planning your schedule.")
else:
    if st.button("📅 Plan My Schedule"):
        st.info("💡 Generating AI-recommended schedule...")

        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT course_id, title, credits, offered_fall, offered_spring, special_constraints_text
                FROM courses;
            """)
            course_rows = cur.fetchall()
            cur.close()
            conn.close()

            # Build course dictionary for lookup later
            course_map = {
                r[0]: {
                    "title": r[1],
                    "credits": r[2],
                    "offered_fall": r[3],
                    "offered_spring": r[4],
                    "special": r[5] or ""
                }
                for r in course_rows
            }

            catalog_summary = "\n".join([
                f"{cid}: {c['title']} ({c['credits']} cr) "
                f"— Fall:{c['offered_fall']} Spring:{c['offered_spring']} Special:{c['special']}"
                for cid, c in course_map.items()
            ])

            # Build structured prompt
            prompt = f"""
            You are an AI academic advisor helping schedule remaining courses for a student.

            ### Context
            - Starting semester: {start_semester}
            - Completed courses: {updated_completed}
            - Program: {selected_program}
            - Constraints: {st.session_state['constraints']}

            ### Course Catalog
            {catalog_summary}

            ### Scheduling Guidelines
            1. Only use the course IDs from the catalog above — never invent new courses.
            2. A course can appear in Fall if `Fall:True` and in Spring if `Spring:True`.
            3. Follow all prerequisite and special constraints mentioned in the “Special” notes.
            4. A course that “must follow” another appears *after* that course in the next term.
            5. Student can take up to 5 courses (15 credits) per semester.
            6. Fill each semester efficiently (try to balance load and finish fast).
            7. Include at least one elective or lighter course if possible each term.
            8. Continue semesters until all remaining courses are completed.

            ### Output Format (strict JSON only)
            {{
              "plan": [
                {{"term": "Fall 2025", "courses": ["EET310","EET315L","EET320"]}},
                {{"term": "Spring 2026", "courses": ["EET322L","EET330"]}}
              ],
              "rationale": "Brief summary of how load, prerequisites, and constraints were balanced."
            }}
            Return **only JSON**, no explanation or markdown.
            """

            # Run OpenAI
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.25
            )

            raw_reply = response.choices[0].message.content.strip()
            import re, json
            match = re.search(r"\{.*\}", raw_reply, re.DOTALL)
            json_text = match.group(0) if match else raw_reply

            try:
                plan = json.loads(json_text)
            except json.JSONDecodeError:
                st.warning("⚠️ AI returned invalid JSON, attempting cleanup...")
                cleaned = json_text.replace("```json", "").replace("```", "").strip()
                plan = json.loads(cleaned)

            # Display Results
            st.subheader("📅 Recommended Multi-Term Plan")
            if "plan" in plan:
                for term in plan["plan"]:
                    st.markdown(f"### 🗓️ {term['term']}")
                    for cid in term["courses"]:
                        info = course_map.get(cid, {"title": "(Not found)", "credits": "?"})
                        st.markdown(f"- **{cid}** — {info['title']} ({info['credits']} cr)")
            else:
                st.error("⚠️ No plan found in AI response.")

            st.subheader("🧩 AI Rationale")
            st.write(plan.get("rationale", "No rationale provided."))

        except Exception as e:
            st.error(f"AI planning failed: {e}")
