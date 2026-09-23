import pytest
from fastapi.testclient import TestClient
from main import app
from database import init_db, get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM submissions")
    cursor.execute("DELETE FROM questions")
    cursor.execute("DELETE FROM quizzes")
    cursor.execute("DELETE FROM users")

    cursor.execute("INSERT INTO users (id, name, username, password, role, class_name) VALUES (1, 'أستاذ أحمد', 't_ahmad', 'pass123', 'teacher', NULL)")
    cursor.execute("INSERT INTO users (id, name, username, password, role, class_name) VALUES (2, 'طالب تجريبي', 's_ali', 'pass123', 'student', '10A')")

    cursor.execute("""
        INSERT INTO quizzes (id, title, class_name, duration_minutes, start_date, end_date, has_negative_marking, negative_mark_value, teacher_id)
        VALUES (1, 'اختبار جبر تجريبي', '10A', 20, '2020-01-01 00:00', '2030-01-01 00:00', 1, 1.0, 1)
    """)

    cursor.execute("INSERT INTO questions (id, quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, points) VALUES (1, 1, '5 + 5؟', '10', '9', '8', '7', 'A', 2.0)")
    cursor.execute("INSERT INTO questions (id, quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, points) VALUES (2, 1, '10 - 3؟', '5', '7', '8', '6', 'B', 2.0)")

    conn.commit()
    conn.close()
    yield

def test_login_flow():
    res_bad = client.post("/login", data={"username": "wrong", "password": "bad"}, follow_redirects=False)
    assert res_bad.status_code == 400

    res_ok = client.post("/login", data={"username": "s_ali", "password": "pass123"}, follow_redirects=False)
    assert res_ok.status_code == 302
    assert "user_id" in res_ok.cookies

def test_negative_marking_calculation():
    client.cookies.set("user_id", "2")
    response = client.post("/quiz/1/submit", data={"q_1": "A", "q_2": "A"}, follow_redirects=False)
    assert response.status_code == 302

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT score, total_possible, percentage FROM submissions WHERE student_id = 2 AND quiz_id = 1")
    submission = cursor.fetchone()
    conn.close()

    assert submission["score"] == 1.0  # إجابة صحيحة (+2) وأخرى خاطئة (-1)
    assert submission["total_possible"] == 4.0
    assert submission["percentage"] == 25.0

def test_prevent_duplicate_submission():
    client.cookies.set("user_id", "2")
    res1 = client.post("/quiz/1/submit", data={"q_1": "A", "q_2": "B"}, follow_redirects=False)
    assert res1.status_code == 302

    res2 = client.post("/quiz/1/submit", data={"q_1": "A", "q_2": "A"}, follow_redirects=False)
    assert res2.status_code == 302
    assert "/result" in res2.headers["location"]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM submissions WHERE student_id = 2 AND quiz_id = 1")
    assert cursor.fetchone()["count"] == 1
    conn.close()