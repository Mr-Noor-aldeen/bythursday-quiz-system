import sys
import subprocess
import os

REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "jinja2",
    "python-multipart",
    "pytest",
    "httpx"
]

def ensure_dependencies():
    """التحقق من تثبيت الحزم المطلوبة وتثبيتها تلقائياً إن كان الجهاز نظيفاً"""
    missing = []
    for pkg in REQUIRED_PACKAGES:
        # استبدال الشرطات للتحقق من اسم الموديول البرمجي
        module_name = "multipart" if pkg == "python-multipart" else pkg.split("[")[0]
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pkg)
            
    if missing:
        print("[!] Clean machine detected. Installing missing packages:", missing)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("[✓] All packages successfully installed.\n")

if __name__ == "__main__":
    ensure_dependencies()
    
    # دعم تشغيل الاختبارات المؤتمتة بأمر واحد
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("[*] Running automated test suites via pytest...")
        sys.exit(subprocess.call([sys.executable, "-m", "pytest"]))
        
    # تشغيل السيرفر تلقائياً
    import uvicorn
    print("\n" + "="*60)
    print("  Amman Tutoring Center Quiz Engine is Running!")
    print("  Open: http://127.0.0.1:8000")
    print("="*60 + "\n")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)