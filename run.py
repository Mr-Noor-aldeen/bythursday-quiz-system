import sys
import subprocess
import os

def ensure_dependencies():
    """
    Guarantees that exact dependencies from requirements.txt are installed.
    Handles clean machines, missing packages, and pre-existing version conflicts automatically.
    """
    try:
        # Run silent dependency reconciliation
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        # Fallback to visible install if silent fails
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

if __name__ == "__main__":
    ensure_dependencies()
    
    # 1-Command Automated Testing Mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("[*] Running automated test suites via pytest...")
        sys.exit(subprocess.call([sys.executable, "-m", "pytest"]))
        
    # 1-Command Web Server Launch Mode
    import uvicorn
    print("\n" + "="*60)
    print("  Amman Tutoring Center Quiz Engine is Running!")
    print("  Open: http://127.0.0.1:8000")
    print("="*60 + "\n")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)