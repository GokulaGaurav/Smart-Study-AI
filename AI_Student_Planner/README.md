# AI-Based Smart Student Planner

A complete, working Flask web app that helps a student manage their
timetable, marks, assignments, and exams — and generates a personalized,
AI-prioritized study plan.

## 🔧 Tech Stack
- Python, Flask
- SQLite (via the built-in `sqlite3` module)
- Scikit-learn (RandomForestClassifier for priority prediction)
- HTML/CSS (Jinja2 templates, sidebar dashboard layout)

## 📁 Project Structure
```
AI_Student_Planner/
│
├── app.py                  # Flask app & routes (dashboard, timetable, marks, assignments, exams, study plan)
├── database.py             # SQLite schema + CRUD helpers
├── recommendation.py       # AI/ML core: rule-based priority + ML classifier wrapper
├── requirements.txt
│
├── model/
│   ├── train_model.py      # Trains the RandomForestClassifier
│   └── study_model.pkl     # Trained model bundle (created by train_model.py)
│
├── data/
│   └── student_planner.db  # SQLite database (created automatically on first run)
│
├── templates/
│   ├── base.html           # Sidebar layout shared by all pages
│   ├── dashboard.html
│   ├── timetable.html
│   ├── marks.html
│   ├── assignments.html
│   ├── exams.html
│   └── study_plan.html
│
└── static/
    └── style.css
```

## ▶️ How to Run

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Train the AI priority model** (creates `model/study_model.pkl`)
   ```bash
   python model/train_model.py
   ```

3. **Run the app**
   ```bash
   python app.py
   ```
   Open **http://127.0.0.1:5000**. The SQLite database is created
   automatically the first time you run the app — no manual setup needed.

## 🧠 How the AI Study Plan Works

For every subject you've entered marks for, the system computes a
**priority score** from four signals:

- **Performance gap** — `100 − current mark %` (weaker subjects score higher)
- **Difficulty** — Low / Medium / High, as you set it per subject
- **Exam urgency** — `100 / (days until next exam + 1)`
- **Assignment urgency** — `100 / (days until nearest pending deadline + 1)`

```python
priority = 0.40 * performance_gap + 0.20 * difficulty_score \
           + 0.25 * exam_urgency + 0.15 * assignment_urgency
```

Subjects are then ranked High / Medium / Low priority, and your available
study hours are split across them proportionally to their priority score.

A **RandomForestClassifier** (`model/train_model.py`) is trained on
synthetic data that mirrors this same relationship, and its prediction is
shown alongside the rule-based label on the AI Study Plan page — so you
can see a transparent rule-based score and a genuine ML prediction agree
(or occasionally disagree) in real time. On the held-out test set, the
classifier reaches about **97–98% agreement** with the rule-based labels.

## 📝 Example Walkthrough

1. Add a class in **Timetable**: Mathematics, Monday, 10:00–11:00.
2. Add marks in **Academic Performance**: Mathematics 30/50, High difficulty.
3. Add an exam in **Exams**: Mathematics, in 3 days.
4. Open the **Dashboard** — you'll see a ⚠️ exam alert and Mathematics
   at the top of today's AI study plan.
5. Open **AI Study Plan** and set your available hours — Mathematics
   will receive the largest share of study time, with both the
   rule-based and ML-predicted priority shown as "High".

## 🚀 Possible Extensions
- Student login / multi-user support
- Charts (Matplotlib/Plotly) showing performance trends over time
- CSV import/export of marks and timetable
- Push/email reminders for approaching exams and deadlines
- Deploy with Streamlit as an alternative UI, per the original brief
