"""
recommendation.py
The AI/ML core of the Smart Student Planner.

Two priority engines are provided:
1. calculate_priority() - transparent rule-based formula (marks, difficulty,
   exam urgency, assignment urgency) as described in the project brief.
2. predict_priority_ml() - a trained Scikit-learn RandomForestClassifier
   (see model/train_model.py) that learns the same relationship from
   sample data, shown alongside the rule-based score for comparison.

recommend_study_plan() combines subjects, marks, exams, and assignments
into a prioritized, time-boxed study plan for a given number of available
study hours.
"""

import os
import pickle

import numpy as np

DIFFICULTY_SCORE = {"Low": 30, "Medium": 60, "High": 90}
MODEL_PATH = "model/study_model.pkl"

_ml_bundle = None


def _load_ml_bundle():
    global _ml_bundle
    if _ml_bundle is None and os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            _ml_bundle = pickle.load(f)
    return _ml_bundle


def calculate_priority(marks_percent, difficulty, days_left_exam, days_left_assignment=None):
    """
    Rule-based priority score (0-100+).

    marks_percent        : current percentage in the subject (0-100)
    difficulty            : 'Low' / 'Medium' / 'High'
    days_left_exam         : days remaining until the next exam for this subject
                              (use a large number, e.g. 999, if no exam is scheduled)
    days_left_assignment  : days remaining until the nearest pending assignment
                              deadline for this subject (None if no assignment)
    """
    performance_gap = max(0.0, 100 - marks_percent)  # weaker subjects -> higher gap
    difficulty_score = DIFFICULTY_SCORE.get(difficulty, 60)
    exam_urgency = 100 / (max(days_left_exam, 0) + 1)

    assignment_urgency = 0.0
    if days_left_assignment is not None:
        assignment_urgency = 100 / (max(days_left_assignment, 0) + 1)

    priority = (
        0.40 * performance_gap
        + 0.20 * difficulty_score
        + 0.25 * exam_urgency
        + 0.15 * assignment_urgency
    )
    return round(priority, 2)


def priority_label(priority_score):
    if priority_score >= 55:
        return "High"
    elif priority_score >= 30:
        return "Medium"
    else:
        return "Low"


def predict_priority_ml(marks_percent, difficulty, days_left_exam, days_left_assignment=None):
    """Use the trained RandomForestClassifier to predict a High/Medium/Low label.
    Falls back to the rule-based label if the model file hasn't been trained yet."""
    bundle = _load_ml_bundle()
    if bundle is None:
        score = calculate_priority(marks_percent, difficulty, days_left_exam, days_left_assignment)
        return priority_label(score)

    scaler = bundle["scaler"]
    clf = bundle["classifier"]

    assignment_days = days_left_assignment if days_left_assignment is not None else 999
    exam_days = min(days_left_exam, 999)
    difficulty_score = DIFFICULTY_SCORE.get(difficulty, 60)

    X = np.array([[marks_percent, difficulty_score, exam_days, assignment_days]])
    X_scaled = scaler.transform(X)
    return clf.predict(X_scaled)[0]


def recommend_study_plan(subjects_info, available_hours):
    """
    subjects_info: list of dicts, each with keys:
        subject, marks_percent, difficulty, days_left_exam, days_left_assignment
    available_hours: total study hours the student has available today (float)

    Returns a list of dicts sorted by priority (highest first), each with
    rule-based priority, ML-predicted label, and recommended study minutes.
    """
    plan = []
    for info in subjects_info:
        score = calculate_priority(
            info["marks_percent"],
            info["difficulty"],
            info["days_left_exam"],
            info.get("days_left_assignment"),
        )
        ml_label = predict_priority_ml(
            info["marks_percent"],
            info["difficulty"],
            info["days_left_exam"],
            info.get("days_left_assignment"),
        )
        plan.append({
            "subject": info["subject"],
            "priority_score": score,
            "priority_label": priority_label(score),
            "ml_priority_label": ml_label,
            "days_left_exam": info["days_left_exam"],
        })

    plan.sort(key=lambda x: x["priority_score"], reverse=True)

    total_score = sum(p["priority_score"] for p in plan) or 1.0
    remaining_minutes = round(available_hours * 60)

    for p in plan:
        share = p["priority_score"] / total_score
        p["recommended_minutes"] = max(10, round(share * remaining_minutes / 5) * 5)

    return plan
