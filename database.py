import sqlite3
from datetime import datetime

DB_NAME = "quiz.db"

def get_db():
    """الحصول على اتصال بقاعدة البيانات مع إرجاع الصفوف كقواميس (Dictionary)"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """إنشاء الجداول الأساسية وفق متطلبات مركز نور التعليمي"""
    conn = get_db()
    cursor = conn.cursor()

    # 1. جدول المستخدمين (طلاب، معلمين، إدارة)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'teacher', 'admin')),
        class_name TEXT  -- مثل 10A, 10B, 11A للطلاب
    )
    """)

    # 2. جدول الاختبارات (توقيت، نطاق زمني، نظام العلامات السالبة)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        class_name TEXT NOT NULL,
        duration_minutes INTEGER NOT NULL DEFAULT 20,
        start_date TEXT NOT NULL,  -- صيغة YYYY-MM-DD HH:MM
        end_date TEXT NOT NULL,    -- صيغة YYYY-MM-DD HH:MM
        has_negative_marking INTEGER NOT NULL DEFAULT 0, -- 1 نعم، 0 لا
        negative_mark_value REAL NOT NULL DEFAULT 0.0,   -- مقدار الخصم لكل خطأ
        teacher_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (teacher_id) REFERENCES users(id)
    )
    """)

    # 3. جدول الأسئلة (نص عربي، 4 خيارات، نقاط السؤال)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        question_text TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_option TEXT NOT NULL CHECK(correct_option IN ('A', 'B', 'C', 'D')),
        points REAL NOT NULL DEFAULT 1.0,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
    )
    """)

    # 4. جدول تسليم الاختبارات (منع الإعادة، حساب النتيجة والوقت)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        score REAL NOT NULL,
        total_possible REAL NOT NULL,
        percentage REAL NOT NULL,
        submitted_at TEXT NOT NULL,
        answers_json TEXT,  -- لحفظ تفاصيل إجابات الطالب
        UNIQUE(quiz_id, student_id), -- منع تقديم الاختبار مرتين نهائياً
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id),
        FOREIGN KEY (student_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully with UTF-8 support.")