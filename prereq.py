import re

COURSE_ID_RE = re.compile(r"[A-Z]{2,}\d{3}[A-Z]?")

def prereqs_met(prereq_expr: str, completed_set: set[str]) -> bool:
    """
    Evaluate AND/OR prerequisite expressions against completed courses.
    Supports &, |, and parentheses. Empty/None => True.
    Example: "EE201 & (CS101 | MATH202)"
    """
    expr = (prereq_expr or "").strip()
    if not expr:
        return True

    def repl(m):
        cid = m.group(0)
        return "True" if cid in completed_set else "False"

    safe = COURSE_ID_RE.sub(repl, expr)
    safe = safe.replace("&", " and ").replace("|", " or ")
    return bool(eval(safe, {"__builtins__": {}}, {}))
