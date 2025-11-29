import streamlit as st
import psycopg2

# ==========================
# DATABASE CONNECTION
# ==========================

import psycopg2
import socket

def get_conn():
    return psycopg2.connect(st.secrets["connections"]["postgres_url"])


# ==========================
# PAGE SETUP AND LOGIN CHECK
# ==========================
st.set_page_config(page_title="Advisor Dashboard", page_icon="🎓", layout="wide")
st.title("🎓 Advisor Dashboard")

# Verify login
if "user" not in st.session_state or not st.session_state["user"]:
    st.warning("⚠️ You must be logged in to view this page.")
    st.switch_page("login.py")

elif st.session_state["user"]["role"] != "advisor":
    st.error("🚫 Access denied. Advisor role required.")
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

def add_program(name, catalog_year, specialization):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO programs (name, catalog_year, specialization)
        VALUES (%s, %s, %s);
    """, (name, catalog_year, specialization))
    conn.commit()
    cur.close()
    conn.close()

def add_section(program_id, title, rule_type, n_required=None, min_credits=None, parent_section_id=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sections (program_id, title, rule_type, n_required, min_credits, parent_section_id)
        VALUES (%s, %s, %s, %s, %s, %s);
    """, (program_id, title, rule_type, n_required, min_credits, parent_section_id))
    conn.commit()
    cur.close()
    conn.close()

def add_course(section_id, course_id, title, credits, prerequisites, corequisites, offered_fall, offered_spring, special_constraints):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO courses (section_id, course_id, title, credits, prerequisites_expr, corequisites_csv, offered_fall, offered_spring, special_constraints_text)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """, (section_id, course_id, title, credits, prerequisites, corequisites, offered_fall, offered_spring, special_constraints))
    conn.commit()
    cur.close()
    conn.close()

# ==========================
# MAIN UI (TABS)
# ==========================
tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Program", "📂 Add Section", "📚 Add Course", "👀 View Program"])

# --------------------------------
# TAB 1 — ADD PROGRAM
# --------------------------------
with tab1:
    st.subheader("Add a New Program")
    name = st.text_input("Program Name")
    catalog_year = st.text_input("Catalog Year (e.g., 2025)")
    specialization = st.text_input("Specialization (optional)")

    if st.button("Save Program", key="save_program"):
        if name and catalog_year:
            add_program(name, catalog_year, specialization)
            st.success("✅ Program added successfully!")
        else:
            st.warning("Please fill in all required fields.")

# --------------------------------
# TAB 2 — ADD SECTION
# --------------------------------
with tab2:
    st.subheader("Add Section or Sub-Section")

    programs = get_programs()
    if programs:
        program_dict = {f"{p[1]} ({p[2]})": p[0] for p in programs}
        selected_program = st.selectbox("Select Program", list(program_dict.keys()))
        title = st.text_input("Section Title")
        rule_type = st.selectbox("Rule Type", ["ALL_REQUIRED", "CHOOSE_N_OF_M", "MIN_CREDITS"])
        n_required = st.number_input("N required (if applicable)", min_value=0, value=0)
        min_credits = st.number_input("Minimum credits (if applicable)", min_value=0, value=0)

        # Parent section (optional)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT section_id, title FROM sections WHERE program_id = %s ORDER BY section_id;", (program_dict[selected_program],))
        sections = cur.fetchall()
        cur.close()
        conn.close()

        parent_section_id = None
        if sections:
            parent_choice = st.selectbox("Parent Section (optional)", ["None"] + [f"{s[0]} - {s[1]}" for s in sections])
            if parent_choice != "None":
                parent_section_id = int(parent_choice.split(" - ")[0])

        if st.button("Save Section", key="save_section"):
            add_section(program_dict[selected_program], title, rule_type,
                        n_required if n_required > 0 else None,
                        min_credits if min_credits > 0 else None,
                        parent_section_id)
            st.success("✅ Section added successfully!")
    else:
        st.warning("No programs found. Please add a program first.")

# --------------------------------
# TAB 3 — ADD COURSE
# --------------------------------
with tab3:
    st.subheader("Add a Course")

    programs = get_programs()
    if programs:
        program_dict = {f"{p[1]} ({p[2]})": p[0] for p in programs}
        selected_program = st.selectbox("Select Program", list(program_dict.keys()), key="course_program")

        # Filter sections by selected program
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT section_id, title FROM sections WHERE program_id = %s ORDER BY section_id;
        """, (program_dict[selected_program],))
        sections = cur.fetchall()
        cur.close()
        conn.close()

        if sections:
            section_dict = {s[1]: s[0] for s in sections}
            selected_section = st.selectbox("Select Section", list(section_dict.keys()))
            course_id = st.text_input("Course ID (e.g., ENMA434)")
            title = st.text_input("Course Title")
            credits = st.number_input("Credits", min_value=1, max_value=5, value=3)
            prerequisites = st.text_input("Prerequisites (comma-separated IDs)")
            corequisites = st.text_input("Corequisites (comma-separated IDs)")
            special_constraints = st.text_area("Special Constraints (e.g., 'Must be Junior Standing')")
            offered_fall = st.checkbox("Offered in Fall", value=True)
            offered_spring = st.checkbox("Offered in Spring", value=True)

            if st.button("Save Course", key="save_course"):
                add_course(section_dict[selected_section], course_id, title, credits,
                           prerequisites, corequisites, offered_fall, offered_spring, special_constraints)
                st.success("✅ Course added successfully!")
        else:
            st.warning("No sections found for this program.")
    else:
        st.warning("No programs found. Please add a program first.")

# --------------------------------
# TAB 4 — VIEW PROGRAM STRUCTURE
# --------------------------------
with tab4:
    st.subheader("👀 View Program Structure")

    programs = get_programs()
    if programs:
        program_dict = {f"{p[1]} ({p[2]})": p[0] for p in programs}
        selected_program = st.selectbox("Select Program to View", list(program_dict.keys()), key="view_program")

        conn = get_conn()
        cur = conn.cursor()

        # Pull all sections for this program
        cur.execute("""
            SELECT section_id, parent_section_id, title, rule_type, n_required, min_credits
            FROM sections
            WHERE program_id = %s
            ORDER BY section_id;
        """, (program_dict[selected_program],))
        sections = cur.fetchall()

        # Pull all courses for this program
        cur.execute("""
            SELECT c.course_id, c.title, c.credits, c.section_id, c.prerequisites_expr, c.corequisites_csv, c.special_constraints_text
            FROM courses c
            JOIN sections s ON c.section_id = s.section_id
            WHERE s.program_id = %s
            ORDER BY c.section_id;
        """, (program_dict[selected_program],))
        courses = cur.fetchall()

        cur.close()
        conn.close()

        if not sections:
            st.info("This program has no sections yet.")
        else:
            # Build dictionaries
            section_dict = {int(s[0]): {"parent": s[1], "title": s[2], "rule": s[3],
                                        "n_req": s[4], "min_cr": s[5]} for s in sections}
            course_dict = {}
            for c in courses:
                sid = int(c[3])
                course_dict.setdefault(sid, []).append({
                    "id": c[0], "title": c[1], "credits": c[2],
                    "prereq": c[4], "coreq": c[5], "special": c[6]
                })

            # Recursive renderer
            def render_section(section_id, indent=0):
                sec = section_dict[section_id]
                indent_str = "&nbsp;&nbsp;&nbsp;&nbsp;" * indent
                rule_info = f" ({sec['rule']}"
                if sec['rule'] == "CHOOSE_N_OF_M" and sec['n_req']:
                    rule_info += f", choose {sec['n_req']}"
                elif sec['rule'] == "MIN_CREDITS" and sec['min_cr']:
                    rule_info += f", min {sec['min_cr']} credits"
                rule_info += ")"
                st.markdown(f"{indent_str}📂 **{sec['title']}**{rule_info}", unsafe_allow_html=True)

                # List courses
                if section_id in course_dict:
                    for c in course_dict[section_id]:
                        c_line = f"{indent_str}&nbsp;&nbsp;&nbsp;📘 {c['id']} — {c['title']} ({c['credits']} cr)"
                        if c["prereq"]:
                            c_line += f" | Prereq: {c['prereq']}"
                        if c["coreq"]:
                            c_line += f" | Coreq: {c['coreq']}"
                        if c["special"]:
                            c_line += f" | Note: {c['special']}"
                        st.markdown(c_line, unsafe_allow_html=True)

                # Recurse into children
                for sid, sdata in section_dict.items():
                    parent_id = sdata["parent"]
                    if parent_id is not None and int(parent_id) == int(section_id):
                        render_section(sid, indent + 1)

            # --- Render all top-level sections ---
            top_sections = [sid for sid, s in section_dict.items() if s["parent"] is None]
            if not top_sections:
                st.warning("No top-level sections found (all are nested).")
            else:
                for ts in top_sections:
                    render_section(ts)
    else:
        st.warning("No programs found. Please add one first.")
