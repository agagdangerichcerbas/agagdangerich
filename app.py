
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')


# Student Information API
@app.route('/student')
def get_student():
    return jsonify({
        "student_id": "2026-00123",
        "name": "Erich",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# Greeting API
@app.route('/hello')
def say_hello():
    name = request.args.get('name', 'Student')
    return jsonify({
        "message": f"Hello, {name}!"
    })


# Students API - Additional Task
@app.route('/students')
def get_students():
    return jsonify({
        "students": [
            {
                "student_id": "2026-00123",
                "name": "Erich",
                "program": "BSIT",
                "year": 3,
                "section": "A"
            },
            {
                "student_id": "2026-00124",
                "name": "Student 2",
                "program": "BSIT",
                "year": 2,
                "section": "B"
            },
            {
                "student_id": "2026-00125",
                "name": "Student 3",
                "program": "BSIT",
                "year": 1,
                "section": "A"
            }
        ]
    })


if __name__ == '__main__':
    app.run(debug=True)
