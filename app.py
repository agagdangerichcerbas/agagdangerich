
import sqlite3
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

DATABASE = "students.db"

# Partner API URL
PARTNER_API_URL = "https://abordaje-jm.onrender.com/api/students"


# ==========================================
# DATABASE CONNECTION
# ==========================================
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# INITIALIZE DATABASE
# ==========================================
def init_db():
    conn = get_db_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                program TEXT NOT NULL,
                year INTEGER NOT NULL,
                section TEXT NOT NULL,
                source TEXT DEFAULT 'Local'
            )
        """)

        columns = [
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(students)"
            ).fetchall()
        ]

        if "source" not in columns:
            conn.execute("""
                ALTER TABLE students
                ADD COLUMN source TEXT DEFAULT 'Local'
            """)

        conn.execute("""
            UPDATE students
            SET source = 'Local'
            WHERE source IS NULL OR source = ''
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0]

        if count == 0:
            conn.execute("""
                INSERT INTO students
                    (student_id, name, program, year, section, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "LAB9-001",
                "Sample Student",
                "BSIT",
                3,
                "A",
                "Local"
            ))

        conn.commit()

    finally:
        conn.close()


# ==========================================
# VALIDATE STUDENT DATA
# ==========================================
def validate_student(data):
    if not isinstance(data, dict):
        return None, "A valid JSON object is required."

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
            return None, f"{field} is required."

    try:
        year = int(data["year"])

        if year < 1:
            raise ValueError

    except (ValueError, TypeError):
        return None, "Year must be a positive number."

    return {
        "student_id": str(data["student_id"]).strip(),
        "name": str(data["name"]).strip(),
        "program": str(data["program"]).strip(),
        "year": year,
        "section": str(data["section"]).strip()
    }, None


# ==========================================
# HOME PAGE
# ==========================================
@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# STUDENT INFORMATION API
# GET /student
# ==========================================
@app.route("/student", methods=["GET"])
def get_student():
    return jsonify({
        "student_id": "24-00316",
        "name": "Erich Agagdang",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# ==========================================
# GREETING API
# GET /hello?name=Student
# ==========================================
@app.route("/hello", methods=["GET"])
def say_hello():
    name = request.args.get("name", "Student").strip()

    if not name:
        name = "Student"

    return jsonify({
        "message": f"Hello, {name}!"
    })


# ==========================================
# READ ALL STUDENTS
# GET /students
# GET /api/students
# ==========================================
@app.route("/students", methods=["GET"])
@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db_connection()

    try:
        students = conn.execute("""
            SELECT * FROM students
            ORDER BY id
        """).fetchall()

        return jsonify([
            dict(student) for student in students
        ])

    finally:
        conn.close()


# ==========================================
# READ ONE STUDENT
# GET /students/1
# GET /api/students/1
# ==========================================
@app.route("/students/<int:id>", methods=["GET"])
@app.route("/api/students/<int:id>", methods=["GET"])
def get_student_by_id(id):
    conn = get_db_connection()

    try:
        student = conn.execute("""
            SELECT * FROM students
            WHERE id = ?
        """, (id,)).fetchone()

        if student is None:
            return jsonify({
                "error": "Student not found."
            }), 404

        return jsonify(dict(student))

    finally:
        conn.close()


# ==========================================
# READ STUDENTS BY PROGRAM
# GET /students/program/BSIT
# ==========================================
@app.route("/students/program/<program>", methods=["GET"])
def get_students_by_program(program):
    conn = get_db_connection()

    try:
        students = conn.execute("""
            SELECT * FROM students
            WHERE LOWER(program) = LOWER(?)
            ORDER BY id
        """, (program,)).fetchall()

        return jsonify([
            dict(student) for student in students
        ])

    finally:
        conn.close()


# ==========================================
# CREATE STUDENT
# POST /api/students
# ==========================================
@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True)
    student, error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    source = str(
        data.get("source", "External API")
    ).strip() or "External API"

    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO students
                (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student["student_id"],
            student["name"],
            student["program"],
            student["year"],
            student["section"],
            source
        ))

        conn.commit()

        return jsonify({
            "message": "Student added successfully.",
            "id": cursor.lastrowid,
            "student": student,
            "source": source
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists in this database."
        }), 409

    finally:
        conn.close()


# ==========================================
# UPDATE STUDENT
# PUT /api/students/1
# ==========================================
@app.route("/api/students/<int:id>", methods=["PUT"])
def update_student(id):
    data = request.get_json(silent=True)
    student, error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        existing = conn.execute("""
            SELECT id FROM students
            WHERE id = ?
        """, (id,)).fetchone()

        if existing is None:
            return jsonify({
                "error": "Student not found."
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
            student["student_id"],
            student["name"],
            student["program"],
            student["year"],
            student["section"],
            id
        ))

        conn.commit()

        return jsonify({
            "message": "Student updated successfully.",
            "student": student
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Another student already uses this Student ID."
        }), 409

    finally:
        conn.close()


# ==========================================
# DELETE STUDENT
# DELETE /api/students/1
# ==========================================
@app.route("/api/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            DELETE FROM students
            WHERE id = ?
        """, (id,))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Student not found."
            }), 404

        return jsonify({
            "message": "Student deleted successfully."
        })

    finally:
        conn.close()


# ==========================================
# RETRIEVE PARTNER RECORDS
# GET /partner-records
# GET /api/classmate-students
# ==========================================
@app.route("/partner-records", methods=["GET"])
@app.route("/api/classmate-students", methods=["GET"])
def get_classmate_students():
    try:
        req = Request(
            PARTNER_API_URL,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0"
            },
            method="GET"
        )

        with urlopen(req, timeout=40) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)

        if not isinstance(data, list):
            return jsonify({
                "error": "Partner API did not return a list.",
                "response": data
            }), 502

        return jsonify(data)

    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")

        return jsonify({
            "error": "Unable to retrieve partner records.",
            "partner_status": e.code,
            "partner_response": body
        }), 502

    except (URLError, TimeoutError, OSError) as e:
        return jsonify({
            "error": "Unable to contact partner API.",
            "details": str(e)
        }), 502

    except (json.JSONDecodeError, UnicodeDecodeError):
        return jsonify({
            "error": "Partner API returned invalid JSON."
        }), 502


# ==========================================
# IMPORT PARTNER RECORD INTO LOCAL DATABASE
# POST /import-student
# ==========================================
@app.route("/import-student", methods=["POST"])
def import_student():
    data = request.get_json(silent=True)
    student, error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO students
                (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student["student_id"],
            student["name"],
            student["program"],
            student["year"],
            student["section"],
            "Classmate API"
        ))

        conn.commit()

        return jsonify({
            "message": "Partner record saved to your database.",
            "id": cursor.lastrowid,
            "student": student,
            "source": "Classmate API"
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "This Student ID already exists in your database."
        }), 409

    finally:
        conn.close()


# ==========================================
# SEND RECORD TO PARTNER API
# POST /send-to-partner
# ==========================================
@app.route("/send-to-partner", methods=["POST"])
def send_to_partner():
    data = request.get_json(silent=True)
    student, error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    # Send only the five standard student fields.
    # Do not send the local "source" field because the
    # partner API may not support additional fields.
    payload_data = {
        "student_id": student["student_id"],
        "name": student["name"],
        "program": student["program"],
        "year": student["year"],
        "section": student["section"]
    }

    try:
        payload = json.dumps(payload_data).encode("utf-8")

        req = Request(
            PARTNER_API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0"
            },
            method="POST"
        )

        with urlopen(req, timeout=30) as response:
            body = response.read().decode(
                "utf-8", errors="replace"
            )

            try:
                partner_response = json.loads(body)
            except json.JSONDecodeError:
                partner_response = {"response": body}

            return jsonify({
                "message": "Record sent successfully to partner API.",
                "status_code": response.status,
                "sent_record": payload_data,
                "partner_response": partner_response
            }), 200

    except HTTPError as e:
        body = e.read().decode(
            "utf-8", errors="replace"
        )

        try:
            partner_response = json.loads(body)
        except json.JSONDecodeError:
            partner_response = {"response": body}

        return jsonify({
            "error": "Partner API rejected the record.",
            "status_code": e.code,
            "partner_response": partner_response,
            "sent_record": payload_data,
            "possible_causes": [
                "The Student ID may already exist in the partner database.",
                "The partner API may require different fields or validation.",
                "The partner API may not allow POST requests."
            ]
        }), 502

    except (URLError, TimeoutError, OSError) as e:
        return jsonify({
            "error": "Unable to contact partner API.",
            "details": str(e)
        }), 502


# ==========================================
# RUN APPLICATION
# ==========================================
init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
