import streamlit as st
import pandas as pd
from utils_db import connect, load_courses, load_rules, load_students, list_majors, rules_for_major
from advisor import eligible_courses, degree_progress, greedy_fill
from llm import plan_with_llm

st.set_page_config(page_title="AI Academic Advisor (Hybrid)", layout="wide")
st.title("AI Academic Advisor")

# Sidebar controls
db_path = st.text_input("SQLite DB path", value="advising.db", help="Path to your advising.db")
term = st.selectbox("Term", ["Fall", "Spring"])
target = st.slider("Target Credits", 12, 18, 15)
use_llm = st.checkbox(
    "Use OpenAI for planning & rationale",
    value=False,
    help="Requires OPENAI_API_KEY and 'openai' package"
)

# Load DB
try:
    conn = connect(db_path)
    courses_df = load_courses(conn)
    rules_df = load_rules(conn)
    students_df = load_students(conn)
    conn.close()
except Exception as e:
    st.error(f"Failed to load database: {e}")
    st.stop()

majors = list_majors(rules_df) or ["EET"]
major = st.selectbox("Major", majors)

mode = st.radio("Student mode", ["Pick sample student", "Enter completed courses manually"], horizontal=True)
if mode == "Pick sample student" and not students_df.empty:
    sid = st.selectbox("Student", students_df["student_id"].tolist())
    completed_raw = students_df.loc[students_df["student_id"] == sid, "completed_courses"].values[0] if sid else ""
    completed = [c.strip() for c in str(completed_raw).split(";") if c.strip()]
else:
    completed = st.multiselect("Completed Courses", sorted(courses_df["course_id"].tolist()))

interests = st.text_input("Interests (comma-separated, optional)", value="")

if st.button("Recommend Schedule"):
    completed_set = set(completed)
    rules_major = rules_for_major(rules_df, major)

    # Build eligibility and degree progress
    elig_df, pairs = eligible_courses(courses_df, completed_set, term)
    prog_df = degree_progress(courses_df, rules_major, completed_set)

    st.subheader("Degree Progress")
    st.dataframe(prog_df, use_container_width=True)

    # Friendly message if nothing eligible
    if elig_df.empty:
        st.warning(
            "No eligible courses for this term with the current completed courses. "
            "Try switching the term (Fall/Spring) or adding earlier prerequisites."
        )

    # Decide plan (LLM or deterministic)
    rationale = ""
    if use_llm:
        # Compact payload to keep token/cost low (only eligible subset)
        eligible_export = (
            [] if elig_df.empty
            else elig_df[["course_id", "title", "credits", "blocks"]].to_dict(orient="records")
        )
        payload = {
            "term": term,
            "target_credits": target,
            "student": {"major": major, "completed": list(completed_set), "interests": interests},
            "degree_progress": prog_df.to_dict(orient="records"),
            "eligible_courses": eligible_export,
            "pair_constraints": [{"course": a, "requires": b} for a, b in pairs.items()],
        }
        try:
            plan = plan_with_llm(payload)
            schedule_ids = [c for c in plan.get("schedule", []) if c in elig_df["course_id"].values]

            # Top up with greedy if under target
            credits = 0
            if schedule_ids:
                chosen_df = elig_df[elig_df["course_id"].isin(schedule_ids)]
                credits = int(chosen_df["credits"].astype(int).sum())
            if credits < max(12, target - 1) and not elig_df.empty:
                remaining_df = elig_df[~elig_df["course_id"].isin(schedule_ids)]
                # Limit pair constraints to remaining set
                rem_pairs = {k: v for k, v in pairs.items() if k in set(remaining_df["course_id"])}
                fill_ids = greedy_fill(remaining_df, target - credits, rem_pairs)
                schedule_ids = schedule_ids + fill_ids

            backups = [
                c for c in plan.get("backups", [])
                if (not elig_df.empty) and c in elig_df["course_id"].values and c not in schedule_ids
            ][:2]
            rationale = plan.get("rationale", "")
        except Exception as e:
            st.warning(f"OpenAI call failed or not configured: {e}. Falling back to deterministic planner.")
            if elig_df.empty:
                schedule_ids, backups = [], []
            else:
                schedule_ids = greedy_fill(elig_df, target, pairs)
                backups = [c for c in elig_df["course_id"].tolist() if c not in set(schedule_ids)][:2]
    else:
        if elig_df.empty:
            schedule_ids, backups = [], []
        else:
            schedule_ids = greedy_fill(elig_df, target, pairs)
            backups = [c for c in elig_df["course_id"].tolist() if c not in set(schedule_ids)][:2]

    # Pretty print section
    by_id = {r["course_id"]: r for _, r in courses_df.iterrows()}

    def pretty(cid: str):
        r = by_id.get(cid, {})
        return f"{cid} — {r.get('title', '')} ({r.get('credits', '?')} cr)"

    st.subheader("Recommended Plan")
    if schedule_ids:
        st.write("\n".join(f"- {pretty(c)}" for c in schedule_ids))
    else:
        st.info("No eligible courses found. Try a different term or update completed courses.")

    st.subheader("Backups")
    if backups:
        st.write("\n".join(f"- {pretty(c)}" for c in backups))
    else:
        st.write("- (none)")

    if rationale:
        st.subheader("Advisor Rationale")
        st.write(rationale)

    st.caption("Hybrid: deterministic eligibility (prereqs, coreqs, term) + optional OpenAI planner.")

else:
    st.info("Pick a student (or choose completed courses), set term & credits, then click **Recommend Schedule**.")
