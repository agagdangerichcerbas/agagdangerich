
import sqlite3
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

DATABASE = "students.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# CREATE DATABASE AND TABLE
# ==========================================
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


# ==========================================
# HOME PAGE
# ==========================================
@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# SAMPLE STUDENT API
# GET /student
# ==========================================
@app.route("/student")
def get_student():
    return jsonify({
        "student_id": "2026-00123",
        "name": "Erich",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# ==========================================
# GREETING API
# GET /hello?name=Erich
# ==========================================
@app.route("/hello")
def say_hello():
    name = request.args.get("name", "Student").strip()

    if not name:
        name = "Student"

    return jsonify({
        "message": f"Hello, {name}!"
    })


# ==========================================
# READ: GET ALL LOCAL STUDENTS
# GET /students
# GET /api/students
# ==========================================
@app.route("/students", methods=["GET"])
@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db_connection()

    students = conn.execute(
        "SELECT * FROM students ORDER BY id"
    ).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# ==========================================
# READ: GET ONE LOCAL STUDENT
# GET /students/1
# GET /api/students/1
# ==========================================
@app.route("/students/<int:id>", methods=["GET"])
@app.route("/api/students/<int:id>", methods=["GET"])
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


# ==========================================
# READ: GET STUDENTS BY PROGRAM
# GET /students/program/BSIT
# ==========================================
@app.route("/students/program/<program>", methods=["GET"])
def get_students_by_program(program):
    conn = get_db_connection()

    students = conn.execute(
        """
        SELECT * FROM students
        WHERE LOWER(program) = LOWER(?)
        ORDER BY id
        """,
        (program,)
    ).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# ==========================================
# CREATE: ADD A STUDENT
# POST /api/students
# ==========================================
@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required"
        }), 400

    fields = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    for field in fields:
        if (
            field not in data
            or data[field] is None
            or str(data[field]).strip() == ""
        ):
            return jsonify({
                "error": f"{field} is required"
            }), 400

    try:
        year = int(data["year"])

        if year < 1:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Year must be a positive number"
        }), 400

    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO students
                (student_id, name, program, year, section)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(data["student_id"]).strip(),
            str(data["name"]).strip(),
            str(data["program"]).strip(),
            year,
            str(data["section"]).strip()
        ))

        conn.commit()
        new_id = cursor.lastrowid

        return jsonify({
            "message": "Student added successfully",
            "id": new_id
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists"
        }), 409

    finally:
        conn.close()


# ==========================================
# UPDATE: EDIT A STUDENT
# PUT /api/students/1
# ==========================================
@app.route("/api/students/<int:id>", methods=["PUT"])
def update_student(id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required"
        }), 400

    fields = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    for field in fields:
        if (
            field not in data
            or data[field] is None
            or str(data[field]).strip() == ""
        ):
            return jsonify({
                "error": f"{field} is required"
            }), 400

    try:
        year = int(data["year"])

        if year < 1:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Year must be a positive number"
        }), 400

    conn = get_db_connection()

    try:
        existing = conn.execute(
            "SELECT id FROM students WHERE id = ?",
            (id,)
        ).fetchone()

        if existing is None:
            return jsonify({
                "error": "Student not found"
            }), 404

        conn.execute("""
            UPDATE students
            SET student_id = ?,
                name = ?,
                program = ?,
                year = ?,
                section = ?
            WHERE id = ?
        """, (
            str(data["student_id"]).strip(),
            str(data["name"]).strip(),
            str(data["program"]).strip(),
            year,
            str(data["section"]).strip(),
            id
        ))

        conn.commit()

        return jsonify({
            "message": "Student updated successfully"
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists"
        }), 409

    finally:
        conn.close()


# ==========================================
# DELETE: REMOVE A LOCAL STUDENT
# DELETE /api/students/1
# ==========================================
@app.route("/api/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            "DELETE FROM students WHERE id = ?",
            (id,)
        )

        deleted = cursor.rowcount
        conn.commit()

        if deleted == 0:
            return jsonify({
                "error": "Student not found"
            }), 404

        return jsonify({
            "message": "Student deleted successfully"
        })

    finally:
        conn.close()


# ==========================================
# CLASSMATE'S RECORDS: API PROXY
# GET /api/classmate-students
# READ-ONLY: Does not modify classmate records
# ==========================================
@app.route("/api/classmate-students", methods=["GET"])
def get_classmate_students():
    url = "https://abordaje-jm.onrender.com/api/students"

    try:
        req = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urlopen(req, timeout=40) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        if not isinstance(data, list):
            return jsonify({
                "error": "Classmate API did not return a list of students"
            }), 502

        return jsonify(data)

    except HTTPError as e:
        return jsonify({
            "error": f"Classmate API returned HTTP {e.code}"
        }), 502

    except (URLError, TimeoutError) as e:
        return jsonify({
            "error": f"Unable to contact classmate API: {e}"
        }), 502

    except (json.JSONDecodeError, UnicodeDecodeError):
        return jsonify({
            "error": "Classmate API returned invalid JSON"
        }), 502


# ==========================================
# RUN APPLICATION
# ==========================================
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
