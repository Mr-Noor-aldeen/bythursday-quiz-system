import os
import sqlite3

def get_db_path():
    # استخدام مجلد /tmp في بيئة Vercel أو عند انعدام صلاحية الكتابة
    if os.environ.get("VERCEL") or not os.access(".", os.W_OK):
        return "/tmp/quiz.db"
    return "quiz.db"

def get_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        init_db_tables(conn)
        seed_initial_data(conn)
    else:
        # تحديث تلقائي للأسئلة في حال كانت الأسئلة القديمة مخزنة
        cursor.execute("SELECT question_text FROM questions WHERE id = 1")
        row = cursor.fetchone()
        if row and "المطروحة" in row["question_text"]:
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

    # 3. حسابات 60 طالباً للشعب الثلاث
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

    # 5. حذف الأسئلة القديمة وإدخال بنك الأسئلة الرياضية الحقيقية الـ 15
    cursor.execute("DELETE FROM questions WHERE quiz_id = 1")
    
    real_questions = [
        (1, 1, "ما هو حل المعادلة الخطية: 2س + 6 = 16 ؟", "س = 5", "س = 3", "س = 8", "س = 10", "A", 1.0),
        (2, 1, "أوجد قيمة س التي تحقق المعادلة: 3(س - 2) = 9", "س = 3", "س = 5", "س = 1", "س = -5", "B", 1.0),
        (3, 1, "ما هو ميل الخط المستقيم المار بالنقطتين (2, 3) و (4, 7)؟", "م = 1", "م = 2", "م = 4", "م = -2", "B", 1.0),
        (4, 1, "إذا كان 4س - 8 = 0، فإن قيمة س تساوي:", "س = 2", "س = -2", "س = 4", "س = 0", "A", 1.0),
        (5, 1, "ما هو محدد المصفوفة ثنائية الرتبة: [[2, 3], [1, 4]] ؟", "5", "11", "8", "-5", "A", 1.5),
        (6, 1, "حل نظام المعادلات: س + ص = 10 ، س - ص = 2. ما قيمة س؟", "س = 4", "س = 6", "س = 8", "س = 5", "B", 1.5),
        (7, 1, "إذا كانت رتبة المصفوفة (أ) هي 2×3، ورتبة المصفوفة (ب) هي 3×2، فإن رتبة حاصل الضرب (أ × ب) هي:", "3×3", "2×2", "2×3", "لا يمكن إجراء الضرب", "B", 1.0),
        (8, 1, "ما هو المقطع الصادي للمستقيم الممثل بالمعادلة: ص = 3س + 7 ؟", "ص = 3", "ص = 7", "ص = -7", "ص = 0", "B", 1.0),
        (9, 1, "حل المعادلة: 5س - 3 = 2س + 9", "س = 4", "س = 2", "س = 6", "س = -4", "A", 1.0),
        (10, 1, "أي من المعادلات التالية تمثل مستقيماً موازياً للمستقيم ص = 4س - 5 ؟", "ص = 4س + 1", "ص = -4س + 2", "ص = 0.25س + 3", "ص = -0.25س", "A", 1.5),
        (11, 1, "النظير الجمعي للمصفوفة [[-1, 2], [0, -3]] هو:", "[[1, -2], [0, 3]]", "[[1, 2], [0, 3]]", "[[-1, -2], [0, 3]]", "[[2, -1], [3, 0]]", "A", 1.0),
        (12, 1, "ما هي قيمة س في المعادلة الكسرية: س/3 + 2 = 5 ؟", "س = 3", "س = 6", "س = 9", "س = 15", "C", 1.0),
        (13, 1, "إذا كانت مصفوفة الوحدة م = [[1, 0], [0, 1]]، فإن قيمة 3 × م تساوي:", "[[3, 0], [0, 3]]", "[[3, 3], [3, 3]]", "[[1, 0], [0, 1]]", "[[3, 1], [1, 3]]", "A", 1.0),
        (14, 1, "ما هي مجموعة حل المتباينة الخطية: 2س - 1 < 5 ؟", "س > 3", "س < 3", "س ≤ 2", "س < 2", "B", 1.5),
        (15, 1, "محدد المصفوفة المنفردة [[3, 6], [1, 2]] يساوي:", "0", "12", "6", "-6", "A", 2.0),
    ]

    cursor.executemany("""
        INSERT INTO questions (id, quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, points)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, real_questions)
    
# حذف التسليم التجريبي القديم لضمان واقعية الإحصائيات
    cursor.execute("DELETE FROM submissions WHERE student_id = 6 AND quiz_id = 1")
    conn.commit()

    conn.commit()