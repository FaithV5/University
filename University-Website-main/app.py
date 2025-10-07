# app.py
import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
import pandas as pd
from gspread_helper import get_sheet

app = Flask(__name__)
app.secret_key = 'apos_pearl_2025'

# CONFIG - change if needed
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '', 
    'database': 'univdb'
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# Ensure default admin & instructor exist (run once)
def ensure_default_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    if count == 0:
        # create default admin and instructor
        users = [
            ('admin', generate_password_hash('admin123'), 'admin'),
            ('instructor', generate_password_hash('instructor123'), 'instructor')
        ]
        cursor.executemany("INSERT INTO users (username,password,role) VALUES (%s,%s,%s)", users)
        db.commit()
    cursor.close()
    db.close()

# Helpers
def query(sql, params=None, fetch=False, one=False):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(sql, params or ())
    if fetch:
        res = cursor.fetchone() if one else cursor.fetchall()
    else:
        db.commit()
        res = None
    cursor.close()
    db.close()
    return res

def sync_students_to_sheet():
    """
    Fetch all students ordered alphabetically by name and overwrite the Google Sheet contents.
    Returns True if sync succeeded, False otherwise.
    """
    try:
        # fetch students ordered by name
        sql = """
            SELECT s.student_id, s.name,
                   d.code AS department,
                   COALESCE(p.name, '') AS program,
                   COALESCE(c.name, '') AS course,
                   COALESCE(s.semester, '') AS semester,
                   COALESCE(s.grade, '') AS grade
            FROM students s
            JOIN departments d ON s.dept_id = d.id
            LEFT JOIN programs p ON s.program_id = p.id
            LEFT JOIN courses c ON s.course_id = c.id
            ORDER BY s.name ASC
        """
        rows = query(sql, fetch=True)

        # build values for sheet: header + rows (list of lists)
        header = ['StudentID', 'Name', 'Department', 'Program', 'Course', 'Semester', 'Grade']
        values = [header]
        for r in rows:
            values.append([
                r.get('student_id', ''),
                r.get('name', ''),
                r.get('department', ''),
                r.get('program', ''),
                r.get('course', ''),
                r.get('semester', ''),
                r.get('grade', '')
            ])

        sheet = get_sheet()  # must return gspread Worksheet
        # Clear and write fresh
        sheet.clear()
        # gspread's update expects a 2D list and a starting cell
        sheet.update('A1', values)
        return True
    except Exception as e:
        # Log the exception for debugging; do not raise so DB ops remain intact
        print("Google Sheets sync failed:", e)
        return False

# Login
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        role = request.form['role']
        user = query("SELECT * FROM users WHERE username=%s AND role=%s", (username, role), fetch=True, one=True)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Logged in successfully','success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Home
@app.route('/home')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('index.html')

# Students list & CRUD
@app.route('/students')
def students():
    if 'user_id' not in session: return redirect(url_for('login'))
    dept = request.args.get('dept')
    program = request.args.get('program')
    course = request.args.get('course')
    sql = """SELECT s.*, d.code AS dept_code, d.name AS dept_name, p.name AS program_name, c.name AS course_name
             FROM students s
             JOIN departments d ON s.dept_id=d.id
             LEFT JOIN programs p ON s.program_id=p.id
             LEFT JOIN courses c ON s.course_id=c.id"""
    conditions = []
    params = []
    if dept:
        conditions.append("d.code=%s"); params.append(dept)
    if program:
        conditions.append("p.id=%s"); params.append(program)
    if course:
        conditions.append("c.id=%s"); params.append(course)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY s.name ASC"
    students = query(sql, tuple(params), fetch=True)
    departments = query("SELECT * FROM departments", fetch=True)
    programs = query("SELECT * FROM programs", fetch=True)
    courses = query("SELECT * FROM courses", fetch=True)
    return render_template('students.html', students=students, departments=departments, programs=programs, courses=courses, selected_dept=dept, selected_program=program,selected_course=course)

@app.route('/students/add', methods=['GET','POST'])
def add_student():
    if 'user_id' not in session: return redirect(url_for('login'))
    departments = query("SELECT * FROM departments", fetch=True)
    programs = query("SELECT * FROM programs", fetch=True)
    courses = query("SELECT * FROM courses", fetch=True)
    if request.method == 'POST':
        student_id = request.form['student_id'].strip()
        name = request.form['name'].strip()
        dept_id = request.form['dept_id']
        program_id = request.form.get('program_id') or None
        course_id = request.form.get('course_id') or None
        semester = request.form.get('semester').strip()
        grade = request.form.get('grade') or None

        if not re.match(r'^\d{2}-\d{5}$', student_id):
            flash('Invalid Student ID format. Must be NN-##### (e.g., 25-12345)','danger')
            return render_template('add_student.html', departments=departments, programs=programs, courses=courses)

        try:
            query("INSERT INTO students (student_id,name,dept_id,program_id,course_id,semester,grade) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                  (student_id,name,dept_id,program_id,course_id,semester,grade))
            ok = sync_students_to_sheet()
            if not ok:
                flash('Student added, but Google Sheets sync failed. Check server logs.','warning')
            else:
                flash('Student added','success')
            return redirect(url_for('students'))
        except Exception as e:
            flash(f'Error: {e}','danger')
    return render_template('add_student.html', departments=departments, programs=programs, courses=courses)

@app.route('/students/edit/<int:id>', methods=['GET','POST'])
def edit_student(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    student = query("SELECT * FROM students WHERE id=%s", (id,), fetch=True, one=True)
    if not student:
        flash('Student not found','danger'); return redirect(url_for('students'))
    departments = query("SELECT * FROM departments", fetch=True)
    programs = query("SELECT * FROM programs", fetch=True)
    courses = query("SELECT * FROM courses", fetch=True)
    if request.method == 'POST':
        student_id = request.form['student_id'].strip()
        name = request.form['name'].strip()
        dept_id = request.form['dept_id']
        program_id = request.form.get('program_id') or None
        course_id = request.form.get('course_id') or None
        semester = request.form.get('semester').strip()
        grade = request.form.get('grade') or None

        if not re.match(r'^\d{2}-\d{5}$', student_id):
            flash('Invalid Student ID format. Must be NN-##### (e.g., 25-12345)','danger')
            return render_template('add_student.html', student=student, departments=departments, programs=programs, courses=courses)

        try:
            query("UPDATE students SET student_id=%s,name=%s,dept_id=%s,program_id=%s,course_id=%s,semester=%s,grade=%s WHERE id=%s",
                  (student_id,name,dept_id,program_id,course_id,semester,grade,id))
            ok = sync_students_to_sheet()
            if not ok:
                flash('Student updated, but Google Sheets sync failed. Check server logs.','warning')
            else:
                flash('Student updated','success')
        except Exception as e:
            flash(f'Error: {e}','danger')
        return redirect(url_for('students'))
    return render_template('add_student.html', student=student, departments=departments, programs=programs, courses=courses)

@app.route('/students/delete/<int:id>', methods=['POST'])
def delete_student(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    # Fetch the student's student_id first if you need it for logging
    student = query("SELECT student_id FROM students WHERE id=%s", (id,), fetch=True, one=True)
    try:
        query("DELETE FROM students WHERE id=%s", (id,))
        ok = sync_students_to_sheet()
        if not ok:
            flash('Student removed from system, but Google Sheets sync failed. Check server logs.','warning')
        else:
            flash('Student removed','success')
    except Exception as e:
        flash(f'Error removing student: {e}','danger')
    return redirect(url_for('students'))

# Admin-only: manage programs
def require_admin():
    if 'user_id' not in session or session.get('role')!='admin':
        flash('Admin access required','danger')
        return False
    return True

@app.route('/programs', methods=['GET','POST'])
def manage_programs():
    if not require_admin(): return redirect(url_for('login'))
    departments = query("SELECT * FROM departments", fetch=True)
    programs = query("SELECT p.*, d.code as dept_code FROM programs p JOIN departments d ON p.dept_id=d.id", fetch=True)
    if request.method=='POST':
        dept_id = request.form['dept_id']
        name = request.form['name'].strip()
        query("INSERT INTO programs (dept_id,name) VALUES (%s,%s)", (dept_id,name))
        flash('Program added','success')
        return redirect(url_for('manage_programs'))
    return render_template('programs.html', departments=departments, programs=programs)

@app.route('/programs/delete/<int:id>', methods=['POST'])
def delete_program(id):
    if not require_admin(): return redirect(url_for('login'))
    query("DELETE FROM programs WHERE id=%s", (id,))
    flash('Program deleted','success')
    return redirect(url_for('manage_programs'))

# Admin-only: manage courses
@app.route('/courses', methods=['GET','POST'])
def manage_courses():
    if not require_admin(): return redirect(url_for('login'))
    courses = query("SELECT * FROM courses", fetch=True)
    if request.method=='POST':
        code = request.form['code'].strip()
        name = request.form['name'].strip()
        query("INSERT INTO courses (code,name) VALUES (%s,%s)", (code,name))
        flash('Course added','success')
        return redirect(url_for('manage_courses'))
    return render_template('courses.html', courses=courses)

@app.route('/courses/delete/<int:id>', methods=['POST'])
def delete_course(id):
    if not require_admin(): return redirect(url_for('login'))
    query("DELETE FROM courses WHERE id=%s", (id,))
    flash('Course deleted','success')
    return redirect(url_for('manage_courses'))

# Google Sheets Sync 
@app.route('/sync_from_gsheet')
def sync_from_gsheet():
    if 'user_id' not in session: return redirect(url_for('login'))
    sheet = get_sheet()
    records = sheet.get_all_values()[1:]  
    for row in records:
        if not row:
            continue
        row = row + ['']*(7 - len(row))
        student_id, name, dept_id, program_id, course_id, semester, grade = row
        existing = query("SELECT * FROM students WHERE student_id=%s", (student_id,), fetch=True, one=True)
        if existing:
            query("""UPDATE students SET name=%s, dept_id=%s, program_id=%s, course_id=%s, semester=%s, grade=%s 
                     WHERE student_id=%s""",
                  (name, dept_id, program_id, course_id, semester, grade, student_id))
        else:
            query("""INSERT INTO students (student_id,name,dept_id,program_id,course_id,semester,grade) 
                     VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                  (student_id,name,dept_id,program_id,course_id,semester,grade))
    flash("System synced with Google Sheets","success")
    return redirect(url_for('students'))

# Export to Excel
@app.route('/export')
def export_students():
    if 'user_id' not in session: return redirect(url_for('login'))
    dept = request.args.get('dept')
    sql = """SELECT s.student_id AS StudentID, s.name AS Name, d.code AS Department, p.name AS Program, c.name AS Course, s.semester AS Semester, s.grade AS Grade
             FROM students s
             JOIN departments d ON s.dept_id=d.id
             LEFT JOIN programs p ON s.program_id=p.id
             LEFT JOIN courses c ON s.course_id=c.id"""
    params = []
    if dept:
        sql += " WHERE d.code=%s"; params.append(dept)
    sql += " ORDER BY s.name ASC"
    rows = query(sql, tuple(params), fetch=True)
    df = pd.DataFrame(rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Students')
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name='students.xlsx')

if __name__ == '__main__':
    ensure_default_users()
    app.run(debug=True)
