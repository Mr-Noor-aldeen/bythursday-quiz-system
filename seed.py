import sqlite3
from datetime import datetime, timedelta
from database import get_db, init_db

def seed_all():
    # إعادة تهيئة الجداول لتنظيف قاعدة البيانات
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    print("جاري تفريغ وتوليد البيانات الأولية...")

    # 1. حساب الإدارة (نور)
    cursor.execute("""
        INSERT INTO users (name, username, password, role, class_name)
        VALUES (?, ?, ?, ?, ?)
    """, ("نور المشرف", "nour_admin", "admin123", "admin", None))

    # 2. حسابات المعلمين الأربعة
    teachers = [
        ("أ. أحمد الحسين", "t_ahmad", "teacher123", "teacher"),
        ("أ. سارة خليل", "t_sarah", "teacher123", "teacher"),
        ("أ. عمر النابلسي", "t_omar", "teacher123", "teacher"),
        ("أ. ليلى المصري", "t_layla", "teacher123", "teacher"),
    ]
    cursor.executemany("""
        INSERT INTO users (name, username, password, role, class_name)
        VALUES (?, ?, ?, ?, NULL)
    """, teachers)

    # 3. توليد 60 طالباً (20 لكل شعبة: 10A, 10B, 11A) بأسماء عربية واقعية
    first_names = [
        "محمد", "عبدالله", "يوسف", "حمزة", "عمر", "طارق", "كريم", "خالد", "زيد", "إبراهيم",
        "مريم", "سارة", "فاطمة", "نور", "رنيم", "آية", "شهد", "ليان", "جود", "هند"
    ]
    last_names = ["العدوان", "المجالي", "العبادي", "الحديدي", "النسور", "الزبن", "الفايز", "الكسواني", "الريماوي", "الكركي"]

    classes = ["10A", "10B", "11A"]
    students = []
    
    for c_name in classes:
        for i in range(1, 21):
            name = f"{first_names[(i - 1) % len(first_names)]} {last_names[(i - 1) % len(last_names)]}"
            username = f"std_{c_name.lower()}_{i:02d}"
            password = "student123"  # كلمة مرور موحدة لتسهيل الاختبار للمراجعين
            students.append((name, username, password, "student", c_name))

    cursor.executemany("""
        INSERT INTO users (name, username, password, role, class_name)
        VALUES (?, ?, ?, ?, ?)
    """, students)

    # 4. توليد الاختبار النموذجي للشعبة 10A (15 سؤالاً مع تفعيل العلامات السالبة)
    now = datetime.now()
    start_date = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    end_date = (now + timedelta(days=7)).strftime("%Y-%m-%d %H:%M")

    cursor.execute("""
        INSERT INTO quizzes (
            title, description, class_name, duration_minutes,
            start_date, end_date, has_negative_marking, negative_mark_value, teacher_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "اختبار الرياضيات الأسبوعي - الجبر والمصفوفات",
        "اختبار يقيس المفاهيم الأساسية. تنبيه: كل إجابة خاطئة تخصم نصف درجة (-0.5).",
        "10A",
        20,
        start_date,
        end_date,
        1,       # تفعيل العلامات السالبة
        0.5,     # خصم 0.5 لكل خطأ
        2        # أ. أحمد الحسين
    ))
    quiz_id_10a = cursor.lastrowid

    # 15 سؤالاً ببيانات عربية ونقاط متنوعة
    questions_10a = [
        ("ما هي قيمة الجذر التربيعي للعدد 144؟", "10", "12", "14", "16", "B", 1.0),
        ("حل المعادلة: 2س + 6 = 16", "س = 5", "س = 4", "س = 6", "س = 3", "A", 1.0),
        ("ما هو ناتج ضرب مصفوفة رتبتها (2x3) في مصفوفة رتبتها (3x2)؟", "مصفوفة رتبتها 3x3", "مصفوفة رتبتها 2x2", "مصفوفة رتبتها 2x3", "لا يمكن الضرب", "B", 2.0),
        ("إذا كانت ق(س) = س² + 3، فما قيمة ق(3)؟", "9", "12", "15", "6", "B", 1.0),
        ("مجموع زوايا المثلث الداخلية يساوي:", "180 درجة", "360 درجة", "90 درجة", "270 درجة", "A", 1.0),
        ("ما هو المعكوس الضربي للعدد 4/5؟", "-4/5", "5/4", "-5/4", "1", "B", 1.0),
        ("قيمة المقدار: 3³ - 2² تساوي:", "23", "25", "5", "19", "A", 1.0),
        ("محدد المصفوفة القطرية يساوي:", "مجموع عناصر القطر", "حاصل ضرب عناصر القطر", "صفر دائماً", "واحد دائماً", "B", 2.0),
        ("ما هي نقطة تقاطع المستقيم س = 3 مع محور السينات؟", "(0, 3)", "(3, 0)", "(3, 3)", "(0, 0)", "B", 1.0),
        ("إذا كان محيط مربع 24 سم، فإن مساحته تساوي:", "36 سم²", "48 سم²", "16 سم²", "24 سم²", "A", 1.0),
        ("العدد الأولي من بين الأعداد التالية هو:", "9", "15", "17", "21", "C", 1.0),
        ("ميل الخط المستقيم الموازي لمحور السينات يساوي:", "1", "غير معرّف", "0", "-1", "C", 1.0),
        ("ما هي النسبة المئوية للكسر 3/4؟", "25%", "50%", "75%", "80%", "C", 1.0),
        ("قيمة اللوغاريتم log10(1000) تساوي:", "2", "3", "10", "100", "B", 2.0),
        ("إذا كان س + ص = 10 و س - ص = 4، فإن قيمة س هي:", "7", "3", "6", "5", "A", 2.0),
    ]

    for q in questions_10a:
        cursor.execute("""
            INSERT INTO questions (
                quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, points
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (quiz_id_10a, q[0], q[1], q[2], q[3], q[4], q[5], q[6]))

    # 5. اختبار للشعبة 11A (بدون علامات سالبة)
    cursor.execute("""
        INSERT INTO quizzes (
            title, description, class_name, duration_minutes,
            start_date, end_date, has_negative_marking, negative_mark_value, teacher_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "اختبار الفيزياء العامة - الحركة والقوى",
        "اختبار تجريبي في قوانين نيوتن (لا يوجد خصم للإجابات الخاطئة).",
        "11A",
        20,
        start_date,
        end_date,
        0,       # بدون علامات سالبة
        0.0,
        3        # أ. سارة خليل
    ))
    quiz_id_11a = cursor.lastrowid

    # 15 سؤالاً لفيزياء 11A
    questions_11a = [
        (f"سؤال فيزياء تجريبي رقم {i}: ما وحدة قياس القوة في النظام الدولي؟", "جول", "واط", "نيوتن", "باسكال", "C", 1.0)
        for i in range(1, 16)
    ]
    for q in questions_11a:
        cursor.execute("""
            INSERT INTO questions (
                quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, points
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (quiz_id_11a, q[0], q[1], q[2], q[3], q[4], q[5], q[6]))

    # 6. إضافة تسليمات تجريبية سابقة لعرضها فوراً في لوحة المعلم
    cursor.execute("""
        INSERT INTO submissions (quiz_id, student_id, score, total_possible, percentage, submitted_at, answers_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (quiz_id_10a, 6, 17.5, 20.0, 87.5, now.strftime("%Y-%m-%d %H:%M"), "{}"))

    conn.commit()
    conn.close()
    print(" اكتمل توليد 60 طالباً، 4 معلمين، حساب المدير، واختبارين كاملين بنجاح.")

if __name__ == "__main__":
    seed_all()