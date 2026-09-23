# Amman Tutoring Center Quiz Engine

A clean, mobile-first assessment system built for **Amman Tutoring Center (مركز نور التعليمي)** to replace paper quizzes with timed, auto-graded digital assessments.

Supports multi-role access (Admin, Teachers, Students), class-isolated quizzes, configurable negative marking (-0.5 penalties), and single-submission enforcement.

---

## 🚀 Quickstart (One Command to Run)

The application starts immediately on any clean machine. The SQLite database self-initializes and seeds all sample data on first launch.

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Server (Single Command)

```bash
uvicorn main:app --reload
```

Open [**http://localhost:8000**](http://localhost:8000) in your browser or phone.

### 3. Run Automated Tests

```bash
pytest
```

*Executes all test suites (`test_quiz.py`) verifying schema integrity, negative marking edge cases, duplicate submission locks, and endpoint authentication.*

## 👥 Seeded Users & Login Credentials

All sample data described in the client brief is automatically seeded on startup:

| **Role**                    | **Username**                 | **Password** | **Notes / Scope**                       |
| --------------------------- | ---------------------------- | ------------ | --------------------------------------- |
| **Center Director (Admin)** | `nour_admin`                 | `admin123`   | Center-wide overview and global metrics |
| **Teacher (Math)**          | `t_ahmad`                    | `teacher123` | Class 10A Mathematics                   |
| **Teacher (Physics)**       | `t_sarah`                    | `teacher123` | Physics curriculum                      |
| **Teacher (Chemistry)**     | `t_khaled`                   | `teacher123` | Chemistry curriculum                    |
| **Teacher (Biology)**       | `t_reem`                     | `teacher123` | Biology curriculum                      |
| **Student (Class 10A)**     | `std_10a_01` to `std_10a_20` | `student123` | Class 10A (20 students)                 |
| **Student (Class 10B)**     | `std_10b_01` to `std_10b_20` | `student123` | Class 10B (20 students)                 |
| **Student (Class 11A)**     | `std_11a_01` to `std_11a_20` | `student123` | Class 11A (20 students)                 |

## 🌐 Live Production Deployment

The project is deployed and live on Vercel:

[**https://bythursday-quiz-system.vercel.app**](https://bythursday-quiz-system.vercel.app)
