"""
database.py
Handles all SQLite storage for the AI Student Planner:
timetable, marks (academic performance), assignments, and exams.
"""

import os
import sqlite3
from datetime import date

DB_PATH = "data/student_planner.db"


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            faculty TEXT,
            classroom TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL UNIQUE,
            internal_mark REAL NOT NULL,
            max_mark REAL NOT NULL,
            difficulty TEXT NOT NULL DEFAULT 'Medium'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            deadline TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            exam_date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------- Timetable ----------

def add_class(subject, day, start_time, end_time, faculty, classroom):
    conn = get_connection()
    conn.execute(
        "INSERT INTO timetable (subject, day, start_time, end_time, faculty, classroom) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (subject, day, start_time, end_time, faculty, classroom),
    )
    conn.commit()
    conn.close()


def get_timetable():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM timetable ORDER BY "
        "CASE day "
        "WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 "
        "WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 "
        "WHEN 'Sunday' THEN 7 ELSE 8 END, start_time"
    ).fetchall()
    conn.close()
    return rows


def get_classes_for_day(day_name):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM timetable WHERE day = ? ORDER BY start_time", (day_name,)
    ).fetchall()
    conn.close()
    return rows


def delete_class(class_id):
    conn = get_connection()
    conn.execute("DELETE FROM timetable WHERE id = ?", (class_id,))
    conn.commit()
    conn.close()


# ---------- Marks / Academic Performance ----------

def upsert_marks(subject, internal_mark, max_mark, difficulty):
    conn = get_connection()
    conn.execute(
        "INSERT INTO marks (subject, internal_mark, max_mark, difficulty) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(subject) DO UPDATE SET "
        "internal_mark=excluded.internal_mark, max_mark=excluded.max_mark, difficulty=excluded.difficulty",
        (subject, internal_mark, max_mark, difficulty),
    )
    conn.commit()
    conn.close()


def get_marks():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM marks ORDER BY subject").fetchall()
    conn.close()
    return rows


def delete_marks(mark_id):
    conn = get_connection()
    conn.execute("DELETE FROM marks WHERE id = ?", (mark_id,))
    conn.commit()
    conn.close()


# ---------- Assignments ----------

def add_assignment(title, subject, deadline, status="Pending"):
    conn = get_connection()
    conn.execute(
        "INSERT INTO assignments (title, subject, deadline, status) VALUES (?, ?, ?, ?)",
        (title, subject, deadline, status),
    )
    conn.commit()
    conn.close()


def get_assignments():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM assignments ORDER BY deadline").fetchall()
    conn.close()
    return rows


def update_assignment_status(assignment_id, status):
    conn = get_connection()
    conn.execute("UPDATE assignments SET status = ? WHERE id = ?", (status, assignment_id))
    conn.commit()
    conn.close()


def delete_assignment(assignment_id):
    conn = get_connection()
    conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
    conn.commit()
    conn.close()


# ---------- Exams ----------

def add_exam(subject, exam_date):
    conn = get_connection()
    conn.execute("INSERT INTO exams (subject, exam_date) VALUES (?, ?)", (subject, exam_date))
    conn.commit()
    conn.close()


def get_exams():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM exams ORDER BY exam_date").fetchall()
    conn.close()
    return rows


def delete_exam(exam_id):
    conn = get_connection()
    conn.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
    conn.commit()
    conn.close()


def days_remaining(target_date_str):
    """Return integer days between today and target_date_str (YYYY-MM-DD). Can be negative if past."""
    y, m, d = map(int, target_date_str.split("-"))
    target = date(y, m, d)
    return (target - date.today()).days
