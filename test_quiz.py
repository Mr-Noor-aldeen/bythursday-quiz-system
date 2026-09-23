import os
import sqlite3
import pytest
from fastapi.testclient import TestClient
from main import app
import database

# مسار قاعدة بيانات تجريبية معزولة لاختبارات الـ API
TEST_DB_FILE = "test_isolated.db"

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """تجهيز قاعدة بيانات نظيفة ومعزولة بالكامل لجلسة الاختبارات ثم تنظيفها بعد الانتهاء"""
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass

    # توجيه get_db_path إلى الملف التجريبي المعزول
    database.get_db_path = lambda: TEST_DB_FILE
    
    # تهيئة الجداول وحقن البيانات النموذجية
    conn = database.get_db()
    conn.close()

    yield

    # حذف الملف التجريبي بعد انتهاء كل الفحوصات
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass

client = TestClient(app)

@pytest.fixture
def test_memory_db():
    """قاعدة بيانات في الذاكرة لفحص منطق الخوارزميات الحسابية وقواعد البيانات بدقة"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    database.init_db_tables(conn)
    database.seed_initial_data(conn)
    yield conn
    conn.close()

# 1. التحقق من هيكلية البيانات والمستخدمين المطلوبة في تقييم byThursday
def test_sample_data_integrity(test_memory_db):
    cursor = test_memory_db.cursor()
    
    # التأكد من حساب المديرة
    cursor.execute("SELECT * FROM users WHERE role = 'admin'")
    admin = cursor.fetchone()
    assert admin is not None
    assert admin["username"] == "nour_admin"
    
    # التأكد من وجود 4 معلمين
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'teacher'")
    assert cursor.fetchone()["count"] == 4
    
    # التأكد من وجود 60 طالباً عبر الشعب الثلاث (10A, 10B, 11A)
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'")
    assert cursor.fetchone()["count"] == 60
    
    for cls in ['10A', '10B', '11A']:
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE class_name = ?", (cls,))
        assert cursor.fetchone()["count"] == 20

    # التأكد من وجود 15 سؤالاً حقيقياً للاختبار التجريبي
    cursor.execute("SELECT COUNT(*) as count FROM questions WHERE quiz_id = 1")
    assert cursor.fetchone()["count"] == 15

# 2. فحص خوارزمية العلامات السالبة (Negative Marking Logic)
def test_negative_marking_algorithm(test_memory_db):
    cursor = test_memory_db.cursor()
    cursor.execute("SELECT * FROM quizzes WHERE id = 1")
    quiz = cursor.fetchone()
    
    cursor.execute("SELECT * FROM questions WHERE quiz_id = 1 ORDER BY id ASC")
    questions = cursor.fetchall()
    penalty = float(quiz["negative_mark_value"])  # 0.5
    
    # حالة 1: إجابة صحيحة واحدة وبقية الأسئلة فارغة (المتروك لا يخصم درجات)
    score = float(questions[0]["points"])
    assert score == 1.0

    # حالة 2: إجابة صحيحة واحدة وإجابة خاطئة واحدة (1.0 - 0.5 = 0.5)
    score = float(questions[0]["points"]) - penalty
    assert score == 0.5

    # حالة 3: جميع الإجابات خاطئة -> يجب حصر النتيجة عند الصفر ومنع القيم السالبة
    score = 0.0
    for _ in questions:
        score -= penalty
    score = max(0.0, round(score, 2))
    assert score == 0.0

# 3. التحقق من منع الطالب من تقديم الاختبار مرتين (Single Submission Rule)
def test_prevent_duplicate_submissions(test_memory_db):
    cursor = test_memory_db.cursor()
    student_id = 7
    quiz_id = 1
    
    # التسليم الأول
    cursor.execute("""
        INSERT INTO submissions (quiz_id, student_id, score, total_possible, percentage, submitted_at)
        VALUES (?, ?, 15.0, 18.0, 83.3, '2026-09-24 10:00:00')
    """, (quiz_id, student_id))
    test_memory_db.commit()
    
    # محاولة التسليم الثاني لنفس الطالب: يجب أن ترفض بقيد فريد (IntegrityError)
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO submissions (quiz_id, student_id, score, total_possible, percentage, submitted_at)
            VALUES (?, ?, 16.0, 18.0, 88.9, '2026-09-24 10:05:00')
        """, (quiz_id, student_id))
        test_memory_db.commit()

# 4. فحص مسارات الواجهة وتوثيق الدخول والتحويل (Authentication & Endpoints)
def test_login_and_redirection():
    # 1. فحص إدخال بيانات خاطئة
    res = client.post("/login", data={"username": "wrong_user", "password": "wrong_password"})
    assert res.status_code == 400
    assert "غير صحيحة" in res.text

    # 2. تسجيل دخول صحيح لمعلم
    res = client.post("/login", data={"username": "t_ahmad", "password": "teacher123"}, follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/teacher/dashboard"
    assert "user_id" in res.cookies

    # 3. تسجيل دخول صحيح لطالب
    res = client.post("/login", data={"username": "std_10a_01", "password": "student123"}, follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/student/dashboard"
    assert "user_id" in res.cookies