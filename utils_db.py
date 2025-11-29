import sqlite3
import pandas as pd

def connect(db_path: str):
    return sqlite3.connect(db_path)

def load_courses(conn) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM courses", conn)

def load_rules(conn) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM degree_rules", conn)

def load_students(conn) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM students", conn)

def list_majors(rules_df: pd.DataFrame) -> list[str]:
    return sorted(rules_df["major"].unique().tolist())

def rules_for_major(rules_df: pd.DataFrame, major: str) -> pd.DataFrame:
    return rules_df[rules_df["major"] == major].copy()
