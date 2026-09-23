from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import json
from database import get_db

app = FastAPI(title="Amman Tutoring Center Quiz Engine")
templates = Jinja2Templates(directory="templates")

# --- دوال التحقق من الجلسات (Session Helpers) ---

def get_current_user(request: Request):
    """التحقق من جلسة المستخدم عبر الكوكيز"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

# --- المسارات الرئيسية (Routes) ---

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user["role"] == "student":
        return RedirectResponse(url="/student/dashboard", status_code=302)
    return RedirectResponse(url="/teacher/dashboard", status_code=302)

# 1. تسجيل الدخول والخروج
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username.strip(), password.strip()))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "اسم المستخدم أو كلمة المرور غير صحيحة"
        }, status_code=400)

    target_url = "/student/dashboard" if user["role"] == "student" else "/teacher/dashboard"
    res = RedirectResponse(url=target_url, status_code=302)
    res.set_cookie(key="user_id", value=str(user["id"]), httponly=True)
    return res

@app.get("/logout")
def logout():
    res = RedirectResponse(url="/login", status_code=302)
    res.delete_cookie(key="user_id")
    return res

# 2. لوحة تحكم الطالب (عرض الاختبارات المتاحة والمنجزة)
@app.get("/student/dashboard", response_class=HTMLResponse)
def student_dashboard(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "student":
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    cursor = conn.cursor()

    # جلب جميع اختبارات شعبة الطالب
    cursor.execute("""
        SELECT q.*, u.name as teacher_name,
               (SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) as question_count,
               s.id as submission_id, s.score, s.total_possible, s.percentage
        FROM quizzes q
        JOIN users u ON q.teacher_id = u.id
        LEFT JOIN submissions s ON s.quiz_id = q.id AND s.student_id = ?
        WHERE q.class_name = ?
        ORDER BY q.id DESC
    """, (user["id"], user["class_name"]))
    quizzes = cursor.fetchall()
    conn.close()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    return templates.TemplateResponse("student_dashboard.html", {
        "request": request,
        "user": user,
        "quizzes": quizzes,
        "now_str": now_str
    })

# 3. تقديم الاختبار (الواجهة والعداد الزمني)
@app.get("/quiz/{quiz_id}", response_class=HTMLResponse)
def take_quiz(request: Request, quiz_id: int):
    user = get_current_user(request)
    if not user or user["role"] != "student":
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    cursor = conn.cursor()

    # التحقق من وجود الاختبار ومطابقته لشعبة الطالب
    cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
    quiz = cursor.fetchone()
    if not quiz or quiz["class_name"] != user["class_name"]:
        conn.close()
        raise HTTPException(status_code=404, detail="الاختبار غير موجود أو غير مخصص لشعبتك")

    # منع إعادة تقديم الاختبار نهائياً
    cursor.execute("SELECT id FROM submissions WHERE quiz_id = ? AND student_id = ?", (quiz_id, user["id"]))
    if cursor.fetchone():
        conn.close()
        return RedirectResponse(url=f"/quiz/{quiz_id}/result", status_code=302)

    # التحقق من النطاق الزمني للاختبار
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    if now_str < quiz["start_date"] or now_str > quiz["end_date"]:
        conn.close()
        raise HTTPException(status_code=403, detail="هذا الاختبار مغلق حالياً وفق النطاق الزمني المحدد")

    # جلب الأسئلة
    cursor.execute("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", (quiz_id,))
    questions = cursor.fetchall()
    conn.close()

    return templates.TemplateResponse("take_quiz.html", {
        "request": request,
        "user": user,
        "quiz": quiz,
        "questions": questions
    })

# 4. تسليم الاختبار واحتساب العلامات (مع العلامات السالبة)
@app.post("/quiz/{quiz_id}/submit")
async def submit_quiz(request: Request, quiz_id: int):
    user = get_current_user(request)
    if not user or user["role"] != "student":
        return RedirectResponse(url="/login", status_code=302)

    form_data = await request.form()
    conn = get_db()
    cursor = conn.cursor()

    # حماية مضاعفة: التأكد مجدداً أن الطالب لم يسبق له التسليم
    cursor.execute("SELECT id FROM submissions WHERE quiz_id = ? AND student_id = ?", (quiz_id, user["id"]))
    if cursor.fetchone():
        conn.close()
        return RedirectResponse(url=f"/quiz/{quiz_id}/result", status_code=302)

    cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
    quiz = cursor.fetchone()

    cursor.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,))
    questions = cursor.fetchall()

    total_possible = sum(q["points"] for q in questions)
    score = 0.0
    student_answers = {}

    # خوارزمية احتساب الدرجات والعلامات السالبة
    for q in questions:
        q_id = str(q["id"])
        selected = form_data.get(f"q_{q_id}")
        student_answers[q_id] = selected

        if selected is None or selected == "":
            # ترك السؤال فارغاً: 0 علامة (لا مكافأة ولا خصم)
            continue
        elif selected == q["correct_option"]:
            # إجابة صحيحة: إضافة نقاط السؤال كاملة
            score += float(q["points"])
        else:
            # إجابة خاطئة: خصم في حال تفعيل نظام العلامات السالبة
            if quiz["has_negative_marking"]:
                score -= float(quiz["negative_mark_value"])

    # ضمان عدم نزول العلامة عن الصفر كقاعدة منطقية
    score = max(0.0, round(score, 2))
    percentage = round((score / total_possible * 100), 1) if total_possible > 0 else 0.0
    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    cursor.execute("""
        INSERT INTO submissions (quiz_id, student_id, score, total_possible, percentage, submitted_at, answers_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (quiz_id, user["id"], score, total_possible, percentage, submitted_at, json.dumps(student_answers)))

    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/quiz/{quiz_id}/result", status_code=302)

# 5. عرض نتيجة الطالب
@app.get("/quiz/{quiz_id}/result", response_class=HTMLResponse)
def quiz_result(request: Request, quiz_id: int):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
    quiz = cursor.fetchone()

    cursor.execute("SELECT * FROM submissions WHERE quiz_id = ? AND student_id = ?", (quiz_id, user["id"]))
    submission = cursor.fetchone()
    conn.close()

    if not submission:
        return RedirectResponse(url=f"/quiz/{quiz_id}", status_code=302)

    return templates.TemplateResponse("quiz_result.html", {
        "request": request,
        "user": user,
        "quiz": quiz,
        "submission": submission
    })

# 6. لوحة المعلم والإدارة (عرض النتائج والإحصائيات)
@app.get("/teacher/dashboard", response_class=HTMLResponse)
def teacher_dashboard(request: Request):
    user = get_current_user(request)
    if not user or user["role"] not in ["teacher", "admin"]:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    cursor = conn.cursor()

    # قائمة الاختبارات
    if user["role"] == "admin":
        cursor.execute("SELECT q.*, u.name as teacher_name FROM quizzes q JOIN users u ON q.teacher_id = u.id ORDER BY q.id DESC")
    else:
        cursor.execute("SELECT q.*, u.name as teacher_name FROM quizzes q JOIN users u ON q.teacher_id = u.id WHERE q.teacher_id = ? ORDER BY q.id DESC", (user["id"],))
    quizzes = cursor.fetchall()

    # قائمة نتائج الطلاب
    query = """
        SELECT s.*, u.name as student_name, u.class_name, q.title as quiz_title
        FROM submissions s
        JOIN users u ON s.student_id = u.id
        JOIN quizzes q ON s.quiz_id = q.id
    """
    if user["role"] == "teacher":
        query += " WHERE q.teacher_id = ?"
        cursor.execute(query + " ORDER BY s.id DESC", (user["id"],))
    else:
        cursor.execute(query + " ORDER BY s.id DESC")
    submissions = cursor.fetchall()

    # إحصائيات عامة
    total_submissions = len(submissions)
    avg_score = round(sum(s["percentage"] for s in submissions) / total_submissions, 1) if total_submissions > 0 else 0

    conn.close()

    return templates.TemplateResponse("teacher_dashboard.html", {
        "request": request,
        "user": user,
        "quizzes": quizzes,
        "submissions": submissions,
        "total_submissions": total_submissions,
        "avg_score": avg_score
    })