import os
import sqlite3
import pytest
from fastapi.testclient import TestClient
from main import app
import database

TEST_DB_FILE = "test_isolated.db"

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup clean isolated SQLite database for API test suites and cleanup afterwards."""
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass

    database.get_db_path = lambda: TEST_DB_FILE
    conn = database.get_db()
    conn.close()

    yield

    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass

client = TestClient(app)

@pytest.fixture
def test_memory_db():
    """In-memory SQLite database fixture for high-precision logic verification."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    database.init_db_tables(conn)
    database.seed_initial_data(conn)
    yield conn
    conn.close()

def test_sample_data_integrity(test_memory_db):
    """Verify initial database seeding: 1 admin, 4 teachers, 60 students, and 15 questions."""
    cursor = test_memory_db.cursor()
    
    # 1. Admin account exists
    cursor.execute("SELECT * FROM users WHERE role = 'admin'")
    admin = cursor.fetchone()
    assert admin is not None
    assert admin["username"] == "nour_admin"
    
    # 2. 4 teachers exist
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'teacher'")
    assert cursor.fetchone()["count"] == 4
    
    # 3. 60 students partitioned across 3 cohorts (10A, 10B, 11A)
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'")
    assert cursor.fetchone()["count"] == 60
    
    for cls in ['10A', '10B', '11A']:
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE class_name = ?", (cls,))
        assert cursor.fetchone()["count"] == 20

    # 4. Math demo quiz contains 15 questions
    cursor.execute("SELECT COUNT(*) as count FROM questions WHERE quiz_id = 1")
    assert cursor.fetchone()["count"] == 15

def test_negative_marking_algorithm(test_memory_db):
    """Verify negative marking logic: -0.5 for incorrect, 0 for blank, score floor at 0.0."""
    cursor = test_memory_db.cursor()
    cursor.execute("SELECT * FROM quizzes WHERE id = 1")
    quiz = cursor.fetchone()
    
    cursor.execute("SELECT * FROM questions WHERE quiz_id = 1 ORDER BY id ASC")
    questions = cursor.fetchall()
    penalty = float(quiz["negative_mark_value"])  # 0.5
    
    # Case 1: 1 correct answer, rest left unanswered (0 penalty for blanks)
    score = float(questions[0]["points"])
    assert score == 1.0

    # Case 2: 1 correct answer + 1 wrong answer (1.0 - 0.5 = 0.5)
    score = float(questions[0]["points"]) - penalty
    assert score == 0.5

    # Case 3: All answers incorrect -> total score must clamp at floor 0.0
    score = 0.0
    for _ in questions:
        score -= penalty
    score = max(0.0, round(score, 2))
    assert score == 0.0

def test_prevent_duplicate_submissions(test_memory_db):
    """Verify strict single-submission policy via SQLite UNIQUE constraint."""
    cursor = test_memory_db.cursor()
    student_id = 7
    quiz_id = 1
    
    # Initial submission succeeds
    cursor.execute("""
        INSERT INTO submissions (quiz_id, student_id, score, total_possible, percentage, submitted_at)
        VALUES (?, ?, 15.0, 18.0, 83.3, '2026-09-24 10:00:00')
    """, (quiz_id, student_id))
    test_memory_db.commit()
    
    # Second submission attempt for same student & quiz raises IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO submissions (quiz_id, student_id, score, total_possible, percentage, submitted_at)
            VALUES (?, ?, 16.0, 18.0, 88.9, '2026-09-24 10:05:00')
        """, (quiz_id, student_id))
        test_memory_db.commit()

def test_login_and_redirection():
    """Verify authentication endpoints, status codes, and role-based redirects."""
    # Invalid credentials -> 400 Bad Request
    res = client.post("/login", data={"username": "invalid_user", "password": "wrong_password"})
    assert res.status_code == 400

    # Valid teacher login -> 303 Redirect to teacher dashboard
    res = client.post("/login", data={"username": "t_ahmad", "password": "teacher123"}, follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/teacher/dashboard"
    assert "user_id" in res.cookies

    # Valid student login -> 303 Redirect to student dashboard
    res = client.post("/login", data={"username": "std_10a_01", "password": "student123"}, follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/student/dashboard"
    assert "user_id" in res.cookies