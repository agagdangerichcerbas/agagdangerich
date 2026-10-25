
import sqlite3

conn = sqlite3.connect("students.db")
cursor = conn.cursor()

cursor.execute("""
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

# Check whether the source column already exists
columns = [
    row[1] for row in cursor.execute(
        "PRAGMA table_info(students)"
    ).fetchall()
]

if "source" not in columns:
    cursor.execute(
        "ALTER TABLE students ADD COLUMN source TEXT DEFAULT 'Local'"
    )

# Mark existing records as Local if source is empty
cursor.execute("""
UPDATE students
SET source = 'Local'
WHERE source IS NULL OR source = ''
""")

# Reset the practice records for this laboratory
cursor.execute("DELETE FROM students")

students = [
    ('24-00268', 'Jessica Balcena', 'BSIT', 3, 'A', 'Local'),
    ('24-00357', 'Mariel Alada', 'BSIT', 3, 'A', 'Local'),
    ('24-00111', 'Jm Abordaje', 'BSIT', 3, 'A', 'Local'),
    ('24-00273', 'Necole Andrea Aloro', 'BSIT', 3, 'A', 'Local'),
    ('24-00328', 'Jaya Mekaela Almodiel', 'BSIT', 3, 'A', 'Local')
]

cursor.executemany("""
INSERT INTO students
(student_id, name, program, year, section, source)
VALUES (?, ?, ?, ?, ?, ?)
""", students)

conn.commit()
conn.close()

print("Database created successfully with source column.")
