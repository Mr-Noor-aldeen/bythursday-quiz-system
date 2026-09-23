import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_db


# Universal backward & forward compatibility wrapper for Jinja2Templates
from starlette.templating import Jinja2Templates

_real_template_response = Jinja2Templates.TemplateResponse

def _compat_template_response(self, *args, **kwargs):
    if args and isinstance(args[0], str):
        name = args[0]
        context = args[1] if len(args) > 1 else kwargs.get("context", {})
        request = context.get("request") if isinstance(context, dict) else kwargs.get("request")
        clean_kwargs = {k: v for k, v in kwargs.items() if k not in ("context", "name", "request")}
        if request is not None:
            try:
                return _real_template_response(self, request, name, context, **clean_kwargs)
            except TypeError:
                pass
        return _real_template_response(self, name, context, **clean_kwargs)
    return _real_template_response(self, *args, **kwargs)

Jinja2Templates.TemplateResponse = _compat_template_response

app = FastAPI(title="Amman Tutoring Center Quiz Engine")

# مسار مطلق يضمن وصول خوادم Vercel للقوالب دون أي خطأ
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- دوال التحقق من الجلسات (Session Helpers) ---

def get_current_user(request: Request):
    """التحقق الآمن من جلسة المستخدم عبر الكوكيز"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception:
        return None

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
    res = RedirectResponse(url=target_url, status_code=303)
    res.set_cookie(key="user_id", value=str(user["id"]), httponly=True, path="/")
    return res

@app.get("/logout")
def logout():
    res = RedirectResponse(url="/login", status_code=302)
    res.delete_cookie(key="user_id", path="/")
    return res

# 2. لوحة تحكم الطالب
@app.get("/student/dashboard", response_class=HTMLResponse)
def student_dashboard(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "student":
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    cursor = conn.cursor()

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

# 3. واجهة تقديم الاختبار
@app.get("/quiz/{quiz_id}", response_class=HTMLResponse)
def take_quiz(request: Request, quiz_id: int):
    user = get_current_user(request)
    if not user or user["role"] != "student":
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
    quiz = cursor.fetchone()
    if not quiz or quiz["class_name"] != user["class_name"]:
        conn.close()
        raise HTTPException(status_code=404, detail="الاختبار غير موجود أو غير مخصص لشعبتك")

    # إذا كان الطالب قد سلم مسبقاً، يحول فوراً لصفحة النتيجة
    cursor.execute("SELECT id FROM submissions WHERE quiz_id = ? AND student_id = ?", (quiz_id, user["id"]))
    if cursor.fetchone():
        conn.close()
        return RedirectResponse(url=f"/quiz/{quiz_id}/result", status_code=302)

    # التحقق من النطاق الزمني
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    if quiz["start_date"] and quiz["end_date"]:
        if now_str < quiz["start_date"] or now_str > quiz["end_date"]:
            conn.close()
            raise HTTPException(status_code=403, detail="هذا الاختبار مغلق حالياً وفق النطاق الزمني المحدد")

    cursor.execute("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", (quiz_id,))
    questions = cursor.fetchall()
    conn.close()

    return templates.TemplateResponse("take_quiz.html", {
        "request": request,
        "user": user,
        "quiz": quiz,
        "questions": questions
    })

# 4. تسليم الاختبار واحتساب العلامات (معالجة محصنة بالكامل)
@app.post("/quiz/{quiz_id}/submit")
async def submit_quiz(request: Request, quiz_id: int):
    user = get_current_user(request)
    if not user or user["role"] != "student":
        return RedirectResponse(url="/login", status_code=303)

    conn = get_db()
    cursor = conn.cursor()

    # فحص مسبق: إذا كان مسلماً بالفعل، يتم التحويل لصفحة النتيجة فوراً
    cursor.execute("SELECT id FROM submissions WHERE quiz_id = ? AND student_id = ?", (quiz_id, user["id"]))
    if cursor.fetchone():
        conn.close()
        return RedirectResponse(url=f"/quiz/{quiz_id}/result", status_code=303)

    cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
    quiz = cursor.fetchone()
    if not quiz:
        conn.close()
        raise HTTPException(status_code=404, detail="الاختبار غير موجود")

    cursor.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,))
    questions = cursor.fetchall()

    form_data = await request.form()
    score = 0.0
    total_possible = sum(float(q["points"]) for q in questions) if questions else 0.0
    student_answers = {}

    has_negative = bool(quiz["has_negative_marking"])
    negative_val = float(quiz["negative_mark_value"])

    for q in questions:
        q_id = str(q["id"])
        selected = form_data.get(f"q_{q_id}")
        student_answers[q_id] = selected

        if selected is None or selected == "":
            continue
        elif selected == q["correct_option"]:
            score += float(q["points"])
        elif has_negative:
            score -= negative_val

    # حصر النتيجة عند الصفر
    score = max(0.0, round(score, 2))
    percentage = round((score / total_possible * 100), 1) if total_possible > 0 else 0.0
    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # إدخال مرن يتعامل مع وجود أو غياب حقل answers_json بأمان
    try:
        cursor.execute("""
            INSERT INTO submissions (quiz_id, student_id, score, total_possible, percentage, submitted_at, answers_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (quiz_id, user["id"], score, total_possible, percentage, submitted_at, json.dumps(student_answers)))
        conn.commit()
    except sqlite3.OperationalError:
        # إذا لم يكن العمود answers_json موجوداً في الجدول
        cursor.execute("""
            INSERT INTO submissions (quiz_id, student_id, score, total_possible, percentage, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (quiz_id, user["id"], score, total_possible, percentage, submitted_at))
        conn.commit()
    except sqlite3.IntegrityError:
        # إذا حدث تكرار تسليم متزامن يتم تجاوزه بسلام
        pass
    finally:
        conn.close()

    return RedirectResponse(url=f"/quiz/{quiz_id}/result", status_code=303)

# 5. عرض نتيجة الاختبار
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

# 6. لوحة تحكم المعلم والإدارة
@app.get("/teacher/dashboard", response_class=HTMLResponse)
def teacher_dashboard(request: Request):
    user = get_current_user(request)
    if not user or user["role"] not in ["teacher", "admin"]:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_db()
    cursor = conn.cursor()

    if user["role"] == "admin":
        cursor.execute("SELECT q.*, u.name as teacher_name FROM quizzes q JOIN users u ON q.teacher_id = u.id ORDER BY q.id DESC")
    else:
        cursor.execute("SELECT q.*, u.name as teacher_name FROM quizzes q JOIN users u ON q.teacher_id = u.id WHERE q.teacher_id = ? ORDER BY q.id DESC", (user["id"],))
    quizzes = cursor.fetchall()

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

@app.get("/admin/impersonate/{target_user_id}")
def admin_impersonate(request: Request, target_user_id: int):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/login", status_code=303)
    
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (target_user_id,))
    target = cursor.fetchone()
    conn.close()
    
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
        
    redirect_url = "/teacher/dashboard" if target["role"] == "teacher" else "/student/dashboard"
    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie(key="user_id", value=str(target["id"]))
    return response
