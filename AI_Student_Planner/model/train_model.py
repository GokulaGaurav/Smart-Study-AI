"""
model/train_model.py
Trains a Scikit-learn RandomForestClassifier that predicts study priority
(High / Medium / Low) from marks, difficulty, exam proximity, and
assignment proximity, learning the same relationship encoded in the
rule-based formula in recommendation.py -- so the app can show a
rule-based score AND a genuine ML prediction side by side.

Run with: python model/train_model.py
Creates: model/study_model.pkl
"""

import os
import pickle
import sys

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from recommendation import calculate_priority, priority_label, DIFFICULTY_SCORE  # noqa: E402

np.random.seed(42)

N = 1200
marks_percent = np.random.uniform(20, 100, N)
difficulty_choice = np.random.choice(["Low", "Medium", "High"], N)
days_left_exam = np.random.choice(list(range(0, 30)) + [999] * 20, N)  # some subjects: no exam soon
days_left_assignment = np.random.choice(list(range(0, 20)) + [None] * 40, N)

X = []
y = []
for i in range(N):
    diff = difficulty_choice[i]
    exam_days = int(days_left_exam[i])
    assign_days = days_left_assignment[i]
    assign_days = None if assign_days is None else int(assign_days)

    score = calculate_priority(marks_percent[i], diff, exam_days, assign_days)
    label = priority_label(score)

    diff_score = DIFFICULTY_SCORE[diff]
    assign_feat = assign_days if assign_days is not None else 999

    X.append([marks_percent[i], diff_score, exam_days, assign_feat])
    y.append(label)

X = np.array(X)
y = np.array(y)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X_train_scaled, y_train)

preds = clf.predict(X_test_scaled)
acc = accuracy_score(y_test, preds)
print(f"Priority classifier accuracy on held-out test set: {acc:.3f}")

os.makedirs("model", exist_ok=True)
with open("model/study_model.pkl", "wb") as f:
    pickle.dump({"scaler": scaler, "classifier": clf}, f)

print("Saved model/study_model.pkl")
