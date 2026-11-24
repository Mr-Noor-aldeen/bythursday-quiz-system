# Amman Tutoring Center Quiz Engine

A clean, responsive, and robust web-based assessment platform built for Amman Tutoring Center (مركز نور التعليمي) to replace paper quizzes with timed, auto-graded digital assessments.

Designed with a mobile-first approach, the system supports multi-role access (Admin, Teachers, Students), class-isolated quizzes, configurable negative marking (-0.5 penalties), and strict single-submission enforcement.

---

## 🚀 One-Command Launch (Zero-Config / Clean Machine)

The application starts immediately on any clean machine. The startup runner automatically detects missing dependencies, initializes the SQLite database schema, and seeds all sample data before launching.

### Single Command to Run:

```bash
python run.py
```

Open [**http://127.0.0.1:8000**](http://127.0.0.1:8000) in your browser or phone.

## 🧪 Run Automated Tests (Single Command)

To execute the test suite verifying data integrity, negative marking rules, single-submission constraints, and authentication:

```bash
python run.py --test
```

*(Or run `pytest` directly).*

## 👥 Seeded Users & Login Credentials

All sample data described in the client brief is automatically seeded on startup:

| **Role**                    | **Username**                 | **Password** | **Scope / Description**                                           |
| --------------------------- | ---------------------------- | ------------ | ----------------------------------------------------------------- |
| **Center Director (Admin)** | `nour_admin`                 | `admin123`   | Global overview across all teachers, classes, and center averages |
| **Teacher (Math)**          | `t_ahmad`                    | `teacher123` | Class 10A Mathematics                                             |
| **Teacher (Physics)**       | `t_sarah`                    | `teacher123` | Physics curriculum                                                |
| **Teacher (Chemistry)**     | `t_khaled`                   | `teacher123` | Chemistry curriculum                                              |
| **Teacher (Biology)**       | `t_reem`                     | `teacher123` | Biology curriculum                                                |
| **Student (Class 10A)**     | `std_10a_01` to `std_10a_20` | `student123` | Class 10A (20 students)                                           |
| **Student (Class 10B)**     | `std_10b_01` to `std_10b_20` | `student123` | Class 10B (20 students)                                           |
| **Student (Class 11A)**     | `std_11a_01` to `std_11a_20` | `student123` | Class 11A (20 students)                                           |

> 💡 **Reviewer Sandbox Tip:** Log in as **`nour_admin`** to access the **Reviewer Sandbox** directly inside the Admin Dashboard. You can preview and test any teacher or student portal with a single click without logging out!

## 🌐 Live Production Deployment

The application is deployed and live for visual preview:

* **Live URL:** https://bythursday-quiz-system.vercel.app

*(Note: For full state persistence and test isolation with SQLite, running locally via `python run.py` is recommended).*


## Session-cookie configuration

Cookies are signed with HMAC-SHA256, purpose-bound, and expire after 12 hours.
They are HttpOnly and SameSite=Lax; Vercel also uses Secure cookies (HTTPS).
Signing prevents editing an ID, but does not encrypt cookie contents or stop
someone who steals a valid cookie. The public demo passwords are still public.

For a single-process local demo, `python run.py` works without configuration:
a random in-memory key is generated and a warning is printed. Restarting the
process invalidates local sessions. Do not use this fallback with multiple
workers or on a deployed service.

For Vercel or another deployment, securely generate and store a random secret
of at least 32 bytes as `QUIZ_SESSION_SECRET`. Never commit it. In Vercel:

1. Open this project's Settings > Environment Variables.
2. Add `QUIZ_SESSION_SECRET` as a sensitive variable for Production and for
   Preview if preview deployments are used. Use a securely generated value,
   not a password or an example copied from documentation.
3. Redeploy after saving the variable. All instances for each environment
   must receive the same stable value. Changing it signs everyone out.

On Vercel, startup fails clearly if the secret is missing or shorter than
32 bytes, instead of silently using a known or unstable signing key.

Existing unsigned sessions cannot be trusted and must sign in once again.
User accounts and passwords are unchanged. Reviewer switching uses a separate
signed proof tied to the current user and the original admin, and return to
admin requires that proof. Logging out or logging in clears reviewer state.
These changes are not a complete security audit or a production-readiness claim.
