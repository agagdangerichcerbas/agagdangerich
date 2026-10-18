
import sqlite3
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

DATABASE = "students.db"


# Database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create database and students table
def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL
        )
    """)

    # Add a sample student if the table is empty
    count = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    if count == 0:
        conn.execute("""
            INSERT INTO students
                (student_id, name, program, year, section)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "2026-00123",
            "Erich",
            "BSIT",
            3,
            "A"
        ))

    conn.commit()
    conn.close()


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Get one sample student
@app.route("/student")
def get_student():
    return jsonify({
        "student_id": "2026-00123",
        "name": "Erich",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# Greeting API
@app.route("/hello")
def say_hello():
    name = request.args.get("name", "Student").strip()

    if not name:
        name = "Student"

    return jsonify({
        "message": f"Hello, {name}!"
    })


# Get all students from the database
@app.route("/students")
def get_students():
    conn = get_db_connection()

    students = conn.execute(
        "SELECT * FROM students ORDER BY id"
    ).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# Get one student by database ID
@app.route("/students/<int:id>")
def get_student_by_id(id):
    conn = get_db_connection()

    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (id,)
    ).fetchone()

    conn.close()

    if student is None:
        return jsonify({
            "error": "Student not found"
        }), 404

    return jsonify(dict(student))


# Get students by program
@app.route("/students/program/<program>")
def get_students_by_program(program):
    conn = get_db_connection()

    students = conn.execute(
        "SELECT * FROM students WHERE LOWER(program) = LOWER(?)",
        (program,)
    ).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# Run the application
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
