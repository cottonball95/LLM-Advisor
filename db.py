import psycopg2
import streamlit as st

# Use connection info from .streamlit/secrets.toml
try:
    CONN_STR = st.secrets["connections"]["postgres"]["url"]
except (KeyError, AttributeError):
    import os
    CONN_STR = os.getenv("POSTGRES_URL", "")
    if not CONN_STR:
        raise ValueError(
            "Database connection not configured. "
            "Set POSTGRES_URL environment variable or configure Streamlit secrets."
        )

def get_conn():
    """Create a PostgreSQL connection."""
    return psycopg2.connect(CONN_STR)

def init_db():
    """Initialize all required tables."""
    conn = get_conn()
    cur = conn.cursor()

    # USERS table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        role TEXT CHECK (role IN ('student', 'advisor')) NOT NULL,
        full_name TEXT
    );
    """)

    # PROGRAMS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS programs (
        program_id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        catalog_year TEXT NOT NULL,
        specialization TEXT
    );
    """)

    # SECTIONS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sections (
        section_id SERIAL PRIMARY KEY,
        program_id INT REFERENCES programs(program_id) ON DELETE CASCADE,
        parent_section_id INT REFERENCES sections(section_id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        rule_type TEXT CHECK (rule_type IN ('ALL_REQUIRED', 'CHOOSE_N_OF_M', 'MIN_CREDITS')) NOT NULL,
        n_required INT,
        min_credits INT,
        sort_order INT DEFAULT 0,
        is_published BOOLEAN DEFAULT FALSE
    );
    """)

    # COURSES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id TEXT PRIMARY KEY,
        section_id INT REFERENCES sections(section_id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        credits INT DEFAULT 3,
        prerequisites_expr TEXT,
        corequisites_csv TEXT,
        offered_fall BOOLEAN DEFAULT TRUE,
        offered_spring BOOLEAN DEFAULT TRUE,
        special_constraints_text TEXT
    );
    """)

    # STUDENT COURSES COMPLETED (used by Student Dashboard)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_courses_completed (
        student_username TEXT REFERENCES users(username) ON DELETE CASCADE,
        course_id TEXT REFERENCES courses(course_id) ON DELETE CASCADE,
        PRIMARY KEY (student_username, course_id)
    );
    """)

    # STUDENT PROGRESS (alternative table, kept for compatibility)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_progress (
        username TEXT REFERENCES users(username) ON DELETE CASCADE,
        course_id TEXT REFERENCES courses(course_id) ON DELETE CASCADE,
        completed BOOLEAN DEFAULT TRUE,
        PRIMARY KEY (username, course_id)
    );
    """)

    # STUDENT CONSTRAINTS (used by Student Dashboard)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_constraints (
        constraint_id SERIAL PRIMARY KEY,
        student_username TEXT REFERENCES users(username) ON DELETE CASCADE,
        label TEXT NOT NULL,
        type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)

    # STUDENT PLANS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_plans (
        plan_id SERIAL PRIMARY KEY,
        username TEXT REFERENCES users(username) ON DELETE CASCADE,
        program_id INT REFERENCES programs(program_id) ON DELETE CASCADE,
        plan_json JSONB NOT NULL,
        rationale_text TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database initialized successfully.")

if __name__ == "__main__":
    init_db()
