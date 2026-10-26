from datetime import datetime, timedelta
import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, flash
from apscheduler.schedulers.background import BackgroundScheduler

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "calendar.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-for-production")


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                due_date TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'Medium',
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(task_id, notification_type),
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)


def calculate_priority(task):
    """Simple explainable AI-style score using urgency and user-selected priority."""
    due = datetime.fromisoformat(task["due_date"])
    now = datetime.now()
    hours_left = (due - now).total_seconds() / 3600
    priority_points = {"Low": 1, "Medium": 2, "High": 3}.get(task["priority"], 2)

    if hours_left < 0:
        urgency_points = 4
    elif hours_left <= 24:
        urgency_points = 4
    elif hours_left <= 72:
        urgency_points = 3
    elif hours_left <= 168:
        urgency_points = 2
    else:
        urgency_points = 1

    score = priority_points + urgency_points
    if score >= 6:
        return "Critical"
    if score >= 5:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"


def scan_deadlines():
    """Create one in-app alert per task and alert category."""
    now = datetime.now()
    with connect_db() as conn:
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE completed = 0"
        ).fetchall()

        for task in tasks:
            due = datetime.fromisoformat(task["due_date"])
            hours_left = (due - now).total_seconds() / 3600
            kind = None
            if hours_left < 0:
                kind = "overdue"
                message = f'"{task["title"]}" is overdue.'
            elif hours_left <= 24:
                kind = "due_soon"
                message = f'"{task["title"]}" is due within 24 hours.'
            elif hours_left <= 72:
                kind = "upcoming"
                message = f'"{task["title"]}" is due within 3 days.'

            if kind:
                conn.execute("""
                    INSERT OR IGNORE INTO notifications
                    (task_id, notification_type, message, created_at)
                    VALUES (?, ?, ?, ?)
                """, (task["id"], kind, message, now.isoformat(timespec="minutes")))


def format_task(row):
    task = dict(row)
    due = datetime.fromisoformat(task["due_date"])
    task["due_display"] = due.strftime("%d %b %Y, %I:%M %p")
    task["ai_priority"] = calculate_priority(task)
    task["is_overdue"] = due < datetime.now() and not task["completed"]
    task["is_due_today"] = due.date() == datetime.now().date() and not task["completed"]
    return task


@app.route("/")
def index():
    scan_deadlines()
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY completed ASC, due_date ASC"
        ).fetchall()
        notices = conn.execute("""
            SELECT notifications.*, tasks.title
            FROM notifications
            JOIN tasks ON tasks.id = notifications.task_id
            ORDER BY notifications.id DESC LIMIT 8
        """).fetchall()

    tasks = [format_task(row) for row in rows]
    active = [t for t in tasks if not t["completed"]]
    completed_count = sum(t["completed"] for t in tasks)
    return render_template(
        "index.html",
        tasks=tasks,
        notices=notices,
        active_count=len(active),
        completed_count=completed_count,
        overdue_count=sum(t["is_overdue"] for t in active),
        today_count=sum(t["is_due_today"] for t in active),
        now=datetime.now().strftime("%Y-%m-%dT%H:%M")
    )


@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("due_date", "").strip()
    priority = request.form.get("priority", "Medium")

    if not title or not due_date:
        flash("Please enter a task title and due date.", "error")
        return redirect(url_for("index"))

    try:
        due = datetime.fromisoformat(due_date)
    except ValueError:
        flash("Please enter a valid due date and time.", "error")
        return redirect(url_for("index"))

    if priority not in {"Low", "Medium", "High"}:
        priority = "Medium"

    with connect_db() as conn:
        conn.execute("""
            INSERT INTO tasks (title, description, due_date, priority, completed, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (
            title, description, due.isoformat(timespec="minutes"), priority,
            datetime.now().isoformat(timespec="minutes")
        ))

    scan_deadlines()
    flash("Task added successfully.", "success")
    return redirect(url_for("index"))


@app.route("/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    with connect_db() as conn:
        conn.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
    flash("Task marked as completed.", "success")
    return redirect(url_for("index"))


@app.route("/reopen/<int:task_id>", methods=["POST"])
def reopen_task(task_id):
    with connect_db() as conn:
        conn.execute("UPDATE tasks SET completed = 0 WHERE id = ?", (task_id,))
    scan_deadlines()
    flash("Task reopened.", "success")
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    with connect_db() as conn:
        conn.execute("DELETE FROM notifications WHERE task_id = ?", (task_id,))
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    flash("Task deleted.", "success")
    return redirect(url_for("index"))


@app.route("/demo")
def demo_data():
    """Optional route to add sample data for demonstration; remove in a deployed app."""
    now = datetime.now()
    examples = [
        ("Deep Learning Assignment", "Submit CNN architecture answers.", now + timedelta(hours=18), "High"),
        ("Distributed Computing Record", "Finish Unit 4 notes and diagrams.", now + timedelta(days=2), "Medium"),
        ("Big Data Analytics Revision", "Revise Hadoop and CAP theorem.", now + timedelta(days=5), "Low"),
    ]
    with connect_db() as conn:
        for title, description, due, priority in examples:
            exists = conn.execute("SELECT id FROM tasks WHERE title = ?", (title,)).fetchone()
            if not exists:
                conn.execute("""
                    INSERT INTO tasks (title, description, due_date, priority, completed, created_at)
                    VALUES (?, ?, ?, ?, 0, ?)
                """, (title, description, due.isoformat(timespec="minutes"), priority,
                      now.isoformat(timespec="minutes")))
    scan_deadlines()
    flash("Sample tasks added.", "success")
    return redirect(url_for("index"))


def start_scheduler():
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(scan_deadlines, "interval", minutes=1, id="deadline_scan",
                      replace_existing=True)
    scheduler.start()
    return scheduler


init_db()
scheduler = start_scheduler()

if __name__ == "__main__":
    # use_reloader=False avoids starting the scheduler twice in Flask debug mode
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
