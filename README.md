# AI Calendar and Deadline Reminder Automation

A college mini-project web application built with Python Flask and SQLite.

## Features
- Add tasks with descriptions, deadlines, and importance levels.
- View active, completed, due-today, and overdue task counts.
- Mark tasks complete, reopen them, or delete them.
- Explainable AI-style priority helper: combines user-selected importance with deadline urgency.
- Automated deadline scan runs on dashboard access and every minute while the server is running.
- In-app alerts for tasks due within 3 days, within 24 hours, or overdue.
- Optional demo data for quick testing.

> This is an educational mini-project. The priority helper is rule-based and explainable; it is not a trained machine-learning model. Notifications are in-app only; email/SMS and external calendar sync are not included.

## Requirements
- Python 3.10 or newer
- Internet connection only if you want the optional Google Fonts styling; the app itself works without it.

## Setup

### 1. Extract the ZIP
Open a terminal in the extracted `ai_calendar_deadline_reminder` folder.

### 2. Create a virtual environment (recommended)
Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install packages
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python app.py
```

### 5. Open in your browser
Visit: http://127.0.0.1:5000

Click **Load demo tasks** to add sample assignments. Or add your own task through the form.

## How the reminder automation works
1. A task is saved in the SQLite database (`calendar.db`).
2. The deadline scanner calculates the time remaining for each unfinished task.
3. It creates an in-app notification when a task is due within 3 days, within 24 hours, or overdue.
4. A uniqueness constraint prevents the same alert type from being inserted repeatedly for the same task.
5. APScheduler repeats the scan every minute while the server is running.

The dashboard also scans deadlines whenever it is opened, so alerts can be generated immediately during testing.

## Main routes
- `/` — dashboard
- `/add` — add task (POST)
- `/complete/<id>` — mark complete (POST)
- `/reopen/<id>` — reopen task (POST)
- `/delete/<id>` — delete task (POST)
- `/demo` — insert example tasks

## Database tables
- `tasks`: task title, description, due date, importance, completion state, creation time.
- `notifications`: task ID, alert type, message, and creation time.

## Suggested test cases
1. Add a task due in 12 hours; expect a “due within 24 hours” alert.
2. Add a task due in 2 days; expect a “due within 3 days” alert.
3. Add a task with a past due date; expect an overdue alert.
4. Mark a task complete; it should no longer be considered by future scans.
5. Delete a task; its notifications should also be deleted.
6. Load demo tasks more than once; duplicate demo task titles should not be inserted.

## Project report outline
1. Title page
2. Abstract
3. Introduction
4. Problem statement
5. Objectives
6. Existing system and proposed system
7. System requirements
8. System architecture and flowchart
9. Database design
10. Implementation and screenshots
11. Test cases and results
12. Advantages and limitations
13. Future enhancements
14. Conclusion
15. References

## Limitations and future enhancements
Current limitations: single-user local application, no login, in-app notifications only, and rule-based priority scoring. Future work could add user accounts, email notifications, Google Calendar integration, a true trained prediction model, and deployment to a hosted server.
