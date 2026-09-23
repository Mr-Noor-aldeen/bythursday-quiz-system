# Amman Tutoring Center Quiz Engine

A clean, responsive, and robust web-based assessment platform built for **Amman Tutoring Center (مركز نور التعليمي)** to replace paper quizzes with timed, auto-graded digital assessments.

Designed with a mobile-first approach, the system supports multi-role access (Admin, Teachers, Students), class-isolated quizzes, configurable negative marking (-0.5 penalties), and strict single-submission enforcement.

---

## 🚀 One-Command Launch (Zero-Config / Clean Machine)

The application starts immediately on any clean machine. The startup runner automatically detects and installs any missing dependencies, initializes the SQLite database schema, and seeds all sample data before launching.

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

*(Or run `pytest` directly)*.

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

## 🌐 Live Production Deployment

The application is deployed and live on Vercel:

[**https://bythursday-quiz-system.vercel.app**](https://bythursday-quiz-system.vercel.app)
