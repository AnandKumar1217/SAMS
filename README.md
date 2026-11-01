# SAMS — Student Attendance Management System

A runnable Flask MVP for student records, daily attendance, summary dashboard, and CSV reports.

## Features
- Add and list students (unique roll number)
- Mark Present/Absent by date
- Dashboard with today's totals
- Attendance percentage report and CSV export
- SQLite database created automatically for a zero-configuration demo

## Run (Python 3.10+)
```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Database
For a quick local demo, SQLite is used by default. The DB file is `sams.db`.
For a college deployment, replace the small SQLite helper with MySQL connector/pooling and configure credentials via environment variables. Do not use the development secret key in production.

## Main routes
- `/` dashboard
- `/students` student management
- `/attendance` mark attendance by date
- `/reports` attendance summary
- `/reports.csv` download report

## Notes
This is an academic MVP, not a hardened production system. Add authentication/role-based access, CSRF protection, audit logs, backups, migrations, and MySQL deployment configuration before real institutional use.
