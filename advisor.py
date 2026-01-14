"""
Advisor module for course eligibility and scheduling logic.
"""
import pandas as pd
from typing import Tuple, Dict, Set
from prereq import prereqs_met


def eligible_courses(courses_df: pd.DataFrame, completed_set: Set[str], term: str) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Filter courses that are eligible for the given term based on prerequisites and term availability.
    
    Args:
        courses_df: DataFrame with columns: course_id, title, credits, prerequisites_expr, 
                    corequisites_csv, offered_fall, offered_spring, blocks (optional)
        completed_set: Set of completed course IDs
        term: "Fall" or "Spring"
    
    Returns:
        Tuple of (eligible DataFrame, corequisite pairs dict)
    """
    eligible = []
    pairs = {}  # Maps course_id -> required_corequisite
    
    term_col = "offered_fall" if term == "Fall" else "offered_spring"
    
    for _, row in courses_df.iterrows():
        course_id = row["course_id"]
        prereq_expr = row.get("prerequisites_expr", "") or ""
        coreq_csv = row.get("corequisites_csv", "") or ""
        offered = row.get(term_col, True)
        
        # Check if offered in this term
        if not offered:
            continue
        
        # Check prerequisites
        if prereq_expr and not prereqs_met(prereq_expr, completed_set):
            continue
        
        # Track corequisites
        if coreq_csv:
            coreq_list = [c.strip() for c in coreq_csv.split(",") if c.strip()]
            for coreq in coreq_list:
                pairs[course_id] = coreq
        
        eligible.append(row)
    
    elig_df = pd.DataFrame(eligible) if eligible else pd.DataFrame()
    
    # Add blocks column if missing (for compatibility with app.py)
    if not elig_df.empty and "blocks" not in elig_df.columns:
        elig_df["blocks"] = ""
    
    return elig_df, pairs


def degree_progress(courses_df: pd.DataFrame, rules_df: pd.DataFrame, completed_set: Set[str]) -> pd.DataFrame:
    """
    Calculate degree progress based on rules and completed courses.
    
    Args:
        courses_df: All courses DataFrame
        rules_df: Degree rules DataFrame with columns: major, category, required_credits, etc.
        completed_set: Set of completed course IDs
    
    Returns:
        DataFrame with degree progress information
    """
    if rules_df.empty:
        return pd.DataFrame(columns=["category", "required", "completed", "remaining"])
    
    progress = []
    
    # Group by category if available, otherwise use a simple structure
    if "category" in rules_df.columns:
        for category in rules_df["category"].unique():
            cat_rules = rules_df[rules_df["category"] == category]
            required = cat_rules["required_credits"].sum() if "required_credits" in cat_rules.columns else 0
            completed_credits = sum(
                courses_df.loc[courses_df["course_id"] == cid, "credits"].values[0]
                for cid in completed_set
                if cid in courses_df["course_id"].values
            )
            remaining = max(0, required - completed_credits)
            progress.append({
                "category": category,
                "required": required,
                "completed": completed_credits,
                "remaining": remaining
            })
    else:
        # Fallback: simple summary
        total_required = rules_df["required_credits"].sum() if "required_credits" in rules_df.columns else 0
        completed_credits = sum(
            courses_df.loc[courses_df["course_id"] == cid, "credits"].values[0]
            for cid in completed_set
            if cid in courses_df["course_id"].values
        )
        progress.append({
            "category": "Total",
            "required": total_required,
            "completed": completed_credits,
            "remaining": max(0, total_required - completed_credits)
        })
    
    return pd.DataFrame(progress)


def greedy_fill(elig_df: pd.DataFrame, target_credits: int, pairs: Dict[str, str]) -> list:
    """
    Greedily select courses to reach target credits, respecting corequisite pairs.
    
    Args:
        elig_df: DataFrame of eligible courses
        target_credits: Target number of credits
        pairs: Dict mapping course_id -> required_corequisite
    
    Returns:
        List of selected course IDs
    """
    if elig_df.empty:
        return []
    
    selected = []
    selected_set = set()
    current_credits = 0
    
    # Sort by credits (descending) for greedy selection
    elig_sorted = elig_df.sort_values("credits", ascending=False)
    
    for _, row in elig_sorted.iterrows():
        course_id = row["course_id"]
        
        # Skip if already selected
        if course_id in selected_set:
            continue
        
        # Check if we need a corequisite
        if course_id in pairs:
            coreq = pairs[course_id]
            if coreq not in selected_set and coreq in elig_df["course_id"].values:
                # Add corequisite first
                coreq_row = elig_df[elig_df["course_id"] == coreq].iloc[0]
                coreq_credits = int(coreq_row["credits"])
                if current_credits + coreq_credits <= target_credits + 2:  # Allow slight overage
                    selected.append(coreq)
                    selected_set.add(coreq)
                    current_credits += coreq_credits
        
        # Add the course itself
        credits = int(row["credits"])
        if current_credits + credits <= target_credits + 2:  # Allow slight overage
            selected.append(course_id)
            selected_set.add(course_id)
            current_credits += credits
            
            # Stop if we've reached or exceeded target
            if current_credits >= target_credits:
                break
    
    return selected

