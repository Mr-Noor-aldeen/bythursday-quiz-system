import subprocess

# 1. تثبيت قيد الإصدار المتوافق داخل requirements.txt
req_text = """fastapi>=0.110.0
uvicorn[standard]>=0.28.0
jinja2>=3.1.3
python-multipart>=0.0.9
pytest>=8.0.0
httpx>=0.27.0,<0.28.0
"""
with open("requirements.txt", "w", encoding="utf-8") as f:
    f.write(req_text.strip())
print("[✓] تم تثبيت قيد التوافقية في requirements.txt.")

# 2. تحديث دالة admin_dashboard ومسار impersonate في main.py
with open("main.py", "r", encoding="utf-8") as f:
    code = f.read()

# تحديث دالة لوحة تحكم الإدارة لتمرير المعلمين والطلاب للقالب
old_admin_return = 'return templates.TemplateResponse("admin_dashboard.html", {"request": request, "submissions": subs, "total_submissions": total_subs, "avg_score": avg_score})'
new_admin_return = '''cursor.execute("SELECT * FROM users WHERE role = 'teacher' ORDER BY name ASC")
    teachers = cursor.fetchall()
    cursor.execute("SELECT * FROM users WHERE role = 'student' ORDER BY class_name, name ASC")
    students = cursor.fetchall()
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "submissions": subs,
        "total_submissions": total_subs,
        "avg_score": avg_score,
        "teachers": teachers,
        "students": students
    })'''

if old_admin_return in code:
    code = code.replace(old_admin_return, new_admin_return)
    print("[✓] تم تحديث دالة admin_dashboard لتمرير بيانات المعلمين والطلاب.")

# التأكد من وجود مسار التقمص
impersonate_code = """
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
"""

if "/admin/impersonate" not in code:
    code += "\n" + impersonate_code
    print("[✓] تم دمج مسار impersonate في main.py.")

with open("main.py", "w", encoding="utf-8") as f:
    f.write(code)

# 3. تشغيل الفحص المؤتمت
print("[*] جاري التحقق من الاختبارات المؤتمتة عبر pytest...")
res = subprocess.call(["pytest"])
if res == 0:
    print("[✓] جميع الاختبارات نجحت بنسبة 100%!")
    print("[*] جاري الرفع الآن إلى GitHub...")
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "feat: complete admin master roster, impersonation switcher and pin httpx compatibility"])
    subprocess.run(["git", "push", "origin", "main"])
    print("\n" + "="*50)
    print(" [✓] تم الرفع بنجاح تام إلى GitHub و Vercel!")
    print("="*50)
else:
    print("[!] يرجى تثبيت إصدار httpx المتوافق أولاً: pip install \"httpx<0.28.0\"")