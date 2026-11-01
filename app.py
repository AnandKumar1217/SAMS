from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sqlite3, csv, io, os
from datetime import date

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
DB_PATH = os.environ.get("SAMS_DB", "sams.db")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT, roll_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL, course TEXT NOT NULL, section TEXT NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
        att_date TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('Present','Absent')),
        UNIQUE(student_id, att_date), FOREIGN KEY(student_id) REFERENCES students(id))""")
    conn.commit()
    return conn

@app.route("/")
def dashboard():
    conn = db()
    total = conn.execute("SELECT COUNT(*) n FROM students").fetchone()["n"]
    today = date.today().isoformat()
    present = conn.execute("SELECT COUNT(*) n FROM attendance WHERE att_date=? AND status='Present'", (today,)).fetchone()["n"]
    absent = conn.execute("SELECT COUNT(*) n FROM attendance WHERE att_date=? AND status='Absent'", (today,)).fetchone()["n"]
    students = conn.execute("SELECT * FROM students ORDER BY roll_no LIMIT 8").fetchall()
    conn.close()
    pct = round(present * 100 / (present + absent)) if present + absent else 0
    return render_template("dashboard.html", total=total, present=present, absent=absent, pct=pct, students=students, today=today)

@app.route("/students", methods=["GET","POST"])
def students():
    conn = db()
    if request.method == "POST":
        try:
            conn.execute("INSERT INTO students(roll_no,name,course,section) VALUES(?,?,?,?)",
                (request.form["roll_no"].strip(), request.form["name"].strip(),
                 request.form["course"].strip(), request.form["section"].strip()))
            conn.commit()
            flash("Student added successfully.", "success")
        except sqlite3.IntegrityError:
            flash("Roll number already exists. Use a unique roll number.", "error")
        finally:
            conn.close()
        return redirect(url_for("students"))
    rows = conn.execute("SELECT * FROM students ORDER BY roll_no").fetchall()
    conn.close()
    return render_template("students.html", students=rows)

@app.route("/attendance", methods=["GET","POST"])
def attendance():
    conn = db()
    selected_date = request.values.get("att_date", date.today().isoformat())
    if request.method == "POST":
        for s in conn.execute("SELECT id FROM students").fetchall():
            status = request.form.get(f"status_{s['id']}", "Absent")
            conn.execute("""INSERT INTO attendance(student_id,att_date,status) VALUES(?,?,?)
                ON CONFLICT(student_id,att_date) DO UPDATE SET status=excluded.status""",
                (s["id"], selected_date, status))
        conn.commit()
        flash("Attendance saved.", "success")
        conn.close()
        return redirect(url_for("attendance", att_date=selected_date))
    students = conn.execute("""SELECT s.*, a.status FROM students s LEFT JOIN attendance a
        ON a.student_id=s.id AND a.att_date=? ORDER BY s.roll_no""", (selected_date,)).fetchall()
    conn.close()
    return render_template("attendance.html", students=students, selected_date=selected_date)

@app.route("/reports")
def reports():
    conn = db()
    rows = conn.execute("""SELECT s.roll_no,s.name,
        SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) present,
        COUNT(a.id) total,
        CASE WHEN COUNT(a.id)=0 THEN 0 ELSE ROUND(100.0*SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)/COUNT(a.id),1) END pct
        FROM students s LEFT JOIN attendance a ON a.student_id=s.id
        GROUP BY s.id ORDER BY s.roll_no""").fetchall()
    conn.close()
    return render_template("reports.html", rows=rows)

@app.route("/reports.csv")
def report_csv():
    conn = db()
    rows = conn.execute("""SELECT s.roll_no,s.name,
        SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) present, COUNT(a.id) total
        FROM students s LEFT JOIN attendance a ON a.student_id=s.id GROUP BY s.id ORDER BY s.roll_no""").fetchall()
    conn.close()
    out = io.StringIO()
    writer = csv.writer(out); writer.writerow(["Roll No","Student Name","Present","Recorded Classes","Attendance %"])
    for r in rows:
        pct = round(100*r["present"]/r["total"],1) if r["total"] else 0
        writer.writerow([r["roll_no"],r["name"],r["present"],r["total"],pct])
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=attendance_report.csv"})

if __name__ == "__main__":
    with db() as conn: pass
    app.run(debug=True)
