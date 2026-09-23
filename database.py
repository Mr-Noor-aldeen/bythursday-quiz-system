import os
import sqlite3

def get_db_path():
    # إذا كان التطبيق على Vercel أو المجلد الحالي للقراءة فقط، نستخدم /tmp
    if os.environ.get("VERCEL") or not os.access(".", os.W_OK):
        return "/tmp/quiz.db"
    return "quiz.db"

def get_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # التحقق من وجود الجداول، وبناؤها تلقائياً إن لم تكن موجودة
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        init_db_tables(conn)
        seed_initial_data(conn)
        
    return conn

def init_db_tables(conn):
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
            class_name TEXT
        );

        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            class_name TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL DEFAULT 20,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            has_negative_marking INTEGER NOT NULL DEFAULT 0,
            negative_mark_value REAL NOT NULL DEFAULT 0.0,
            teacher_id INTEGER NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL,
            points REAL NOT NULL DEFAULT 1.0,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        );

        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            score REAL NOT NULL,
            total_possible REAL NOT NULL,
            percentage REAL NOT NULL,
            submitted_at TEXT NOT NULL,
            UNIQUE(quiz_id, student_id),
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id),
            FOREIGN KEY (student_id) REFERENCES users(id)
        );
    """)
    conn.commit()

def init_db():
    conn = get_db()
    conn.close()

def seed_initial_data(conn):
    cursor = conn.cursor()
    
    # 1. حساب المديرة
    cursor.execute("INSERT OR IGNORE INTO users (id, name, username, password, role, class_name) VALUES (1, 'نور (المديرة العامة)', 'nour_admin', 'admin123', 'admin', NULL)")
    
    # 2. حسابات المعلمين الأربعة
    teachers = [
        (2, 'أ. أحمد الحسين (رياضيات)', 't_ahmad', 'teacher123', 'teacher', None),
        (3, 'أ. سارة النجار (فيزياء)', 't_sarah', 'teacher123', 'teacher', None),
        (4, 'أ. خالد التميمي (كيمياء)', 't_khaled', 'teacher123', 'teacher', None),
        (5, 'أ. ريم الكردي (أحياء)', 't_reem', 'teacher123', 'teacher', None),
    ]
    cursor.executemany("INSERT OR IGNORE INTO users (id, name, username, password, role, class_name) VALUES (?, ?, ?, ?, ?, ?)", teachers)

    # 3. حسابات 60 طالباً عبر الشعب الثلاث
    classes = ['10A', '10B', '11A']
    names_pool = [
        "محمد العدوان", "عبدالله المجالي", "عمر الطراونة", "زيد الرواشدة",
        "حمزة العبادي", "سيف الخصاونة", "يوسف العرموطي", "كريم الفايز",
        "سارة الحديد", "لين الشوابكة", "نور الهنداوي", "آية حداد",
        "رنيم المعاني", "منى المصري", "دانا الكيلاني", "تالا سختيان",
        "فيصل الزعبي", "طارق الداوود", "إبراهيم القاسم", "أحمد العساف"
    ]
    student_id = 6
    for cls in classes:
        for i in range(1, 21):
            name = names_pool[(i - 1) % len(names_pool)]
            uname = f"std_{cls.lower()}_{i:02d}"
            cursor.execute(
                "INSERT OR IGNORE INTO users (id, name, username, password, role, class_name) VALUES (?, ?, ?, ?, 'student', ?)",
                (student_id, f"{name} ({cls})", uname, "student123", cls)
            )
            student_id += 1

    # 4. الاختبار التجريبي لشعبة 10A
    cursor.execute("""
        INSERT OR IGNORE INTO quizzes (id, title, class_name, duration_minutes, start_date, end_date, has_negative_marking, negative_mark_value, teacher_id)
        VALUES (1, 'اختبار الرياضيات الأسبوعي - الجبر والمصفوفات', '10A', 20, '2026-09-01 00:00', '2026-10-01 00:00', 1, 0.5, 2)
    """)

    # 5. بنك الأسئلة (15 سؤالاً)
    for q_idx in range(1, 16):
        cursor.execute("""
            INSERT OR IGNORE INTO questions (id, quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, points)
            VALUES (?, 1, ?, 'أ) س = 2', 'ب) س = 5', 'ج) س = -1', 'د) س = 0', 'A', 1.0)
        """, (q_idx, f"السؤال رقم {q_idx}: ما هو ناتج المعادلة الخطية المطروحة؟"))

    # 6. تسليم تجريبي سابق للطالب الأول لتوضيح الإحصائيات
    cursor.execute("""
        INSERT OR IGNORE INTO submissions (quiz_id, student_id, score, total_possible, percentage, submitted_at)
        VALUES (1, 6, 17.5, 20.0, 87.5, '2026-09-23 22:30:00')
    """)

    conn.commit()