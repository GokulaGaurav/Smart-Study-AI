"""
app.py
Main Flask application for the AI-Based Smart Student Planner.
Connects timetable, marks, assignments, exams, and the AI recommendation
engine into a single dashboard.

Run with: python app.py
Then open http://127.0.0.1:5000
"""

from datetime import date, datetime

from flask import Flask, redirect, render_template, request, url_for

import database as db
from recommendation import recommend_study_plan

app = Flask(__name__)
db.init_db()

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def build_subjects_info():
    """Merge marks + exams + assignments into the structure recommend_study_plan() needs."""
    marks = db.get_marks()
    exams = db.get_exams()
    assignments = db.get_assignments()

    # nearest upcoming exam per subject
    nearest_exam_days = {}
    for e in exams:
        d = db.days_remaining(e["exam_date"])
        if e["subject"] not in nearest_exam_days or d < nearest_exam_days[e["subject"]]:
            nearest_exam_days[e["subject"]] = d

    # nearest pending assignment deadline per subject
    nearest_assignment_days = {}
    for a in assignments:
        if a["status"] != "Pending":
            continue
        d = db.days_remaining(a["deadline"])
        if a["subject"] not in nearest_assignment_days or d < nearest_assignment_days[a["subject"]]:
            nearest_assignment_days[a["subject"]] = d

    subjects_info = []
    for m in marks:
        pct = (m["internal_mark"] / m["max_mark"]) * 100 if m["max_mark"] else 0
        subjects_info.append({
            "subject": m["subject"],
            "marks_percent": round(pct, 2),
            "difficulty": m["difficulty"],
            "days_left_exam": nearest_exam_days.get(m["subject"], 999),
            "days_left_assignment": nearest_assignment_days.get(m["subject"]),
        })
    return subjects_info


@app.route("/")
def dashboard():
    today_name = DAY_NAMES[date.today().weekday()]
    today_classes = db.get_classes_for_day(today_name)

    subjects_info = build_subjects_info()
    study_plan = recommend_study_plan(subjects_info, available_hours=3)[:5] if subjects_info else []

    exams = db.get_exams()
    upcoming_alerts = []
    for e in exams:
        d = db.days_remaining(e["exam_date"])
        if 0 <= d <= 3:
            upcoming_alerts.append(f"{e['subject']} exam is in {d} day(s).")

    return render_template(
        "dashboard.html",
        today_name=today_name,
        today_classes=today_classes,
        study_plan=study_plan,
        alerts=upcoming_alerts,
    )


# ---------- Timetable ----------

@app.route("/timetable", methods=["GET", "POST"])
def timetable():
    if request.method == "POST":
        db.add_class(
            request.form["subject"],
            request.form["day"],
            request.form["start_time"],
            request.form["end_time"],
            request.form.get("faculty", ""),
            request.form.get("classroom", ""),
        )
        return redirect(url_for("timetable"))

    rows = db.get_timetable()
    grouped = {day: [] for day in DAY_NAMES}
    for r in rows:
        if r["day"] in grouped:
            grouped[r["day"]].append(r)

    return render_template("timetable.html", grouped=grouped, day_names=DAY_NAMES)


@app.route("/timetable/delete/<int:class_id>", methods=["POST"])
def delete_class(class_id):
    db.delete_class(class_id)
    return redirect(url_for("timetable"))


# ---------- Marks / Academic Performance ----------

def performance_level(pct):
    if pct >= 85:
        return "Excellent"
    elif pct >= 70:
        return "Good"
    elif pct >= 50:
        return "Average"
    return "Poor"


@app.route("/marks", methods=["GET", "POST"])
def marks():
    if request.method == "POST":
        db.upsert_marks(
            request.form["subject"],
            float(request.form["internal_mark"]),
            float(request.form["max_mark"]),
            request.form["difficulty"],
        )
        return redirect(url_for("marks"))

    rows = db.get_marks()
    enriched = []
    for r in rows:
        pct = (r["internal_mark"] / r["max_mark"]) * 100 if r["max_mark"] else 0
        enriched.append({
            "id": r["id"],
            "subject": r["subject"],
            "internal_mark": r["internal_mark"],
            "max_mark": r["max_mark"],
            "difficulty": r["difficulty"],
            "percent": round(pct, 1),
            "level": performance_level(pct),
        })

    return render_template("marks.html", marks=enriched)


@app.route("/marks/delete/<int:mark_id>", methods=["POST"])
def delete_marks(mark_id):
    db.delete_marks(mark_id)
    return redirect(url_for("marks"))


# ---------- Assignments ----------

@app.route("/assignments", methods=["GET", "POST"])
def assignments():
    if request.method == "POST":
        db.add_assignment(
            request.form["title"],
            request.form["subject"],
            request.form["deadline"],
        )
        return redirect(url_for("assignments"))

    rows = db.get_assignments()
    enriched = []
    for r in rows:
        d = db.days_remaining(r["deadline"])
        enriched.append({
            "id": r["id"],
            "title": r["title"],
            "subject": r["subject"],
            "deadline": r["deadline"],
            "status": r["status"],
            "days_left": d,
        })

    return render_template("assignments.html", assignments=enriched)


@app.route("/assignments/complete/<int:assignment_id>", methods=["POST"])
def complete_assignment(assignment_id):
    db.update_assignment_status(assignment_id, "Completed")
    return redirect(url_for("assignments"))


@app.route("/assignments/delete/<int:assignment_id>", methods=["POST"])
def delete_assignment(assignment_id):
    db.delete_assignment(assignment_id)
    return redirect(url_for("assignments"))


# ---------- Exams ----------

@app.route("/exams", methods=["GET", "POST"])
def exams():
    if request.method == "POST":
        db.add_exam(request.form["subject"], request.form["exam_date"])
        return redirect(url_for("exams"))

    rows = db.get_exams()
    enriched = []
    for r in rows:
        enriched.append({
            "id": r["id"],
            "subject": r["subject"],
            "exam_date": r["exam_date"],
            "days_left": db.days_remaining(r["exam_date"]),
        })

    return render_template("exams.html", exams=enriched)


@app.route("/exams/delete/<int:exam_id>", methods=["POST"])
def delete_exam(exam_id):
    db.delete_exam(exam_id)
    return redirect(url_for("exams"))


# ---------- AI Study Plan ----------

@app.route("/study-plan", methods=["GET", "POST"])
def study_plan():
    available_hours = float(request.form.get("available_hours", 3)) if request.method == "POST" else 3.0

    subjects_info = build_subjects_info()
    plan = recommend_study_plan(subjects_info, available_hours) if subjects_info else []

    return render_template("study_plan.html", plan=plan, available_hours=available_hours)


if __name__ == "__main__":
    app.run(debug=True)
