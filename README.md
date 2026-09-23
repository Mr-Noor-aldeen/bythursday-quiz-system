# Amman Tutoring Center — Online Quiz Platform

A lightweight, mobile-first web-based assessment platform built for Nour's tutoring center in Amman to replace paper-based weekly quizzes[cite: 1].

## Tech Stack

* **Backend:** Python 3.10+ / FastAPI
* **Database:** SQLite (Zero external configuration required)
* **Frontend:** Jinja2 Templates + Tailwind CSS (Responsive & Native Arabic RTL support)[cite: 1]
* **Testing:** Pytest & HTTPX TestClient

---

## Quickstart (One Command Setup)[cite: 1]

### 1. Environment Setup

```bash
python -m venv venv

# Windows:
.\venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies & Seed Sample Data

```bash
pip install -r requirements.txt
python seed.py
```

### 3. Run the Application

```bash
uvicorn main:app --reload
```

Open your browser at: `http://127.0.0.1:8000`

---

## Automated Tests

Run the test suite covering authentication, negative grading calculations, and duplicate submission prevention:

```bash
pytest -v
```

---

## Demo Login Credentials

The database is pre-seeded with cohorts for classes `10A`, `10B`, and `11A` (60 students total), 4 teachers, and the administrator:

| Role                  | Username     | Password     | Notes                                            |
| --------------------- | ------------ | ------------ | ------------------------------------------------ |
| **Admin (Nour)**      | `nour_admin` | `admin123`   | Full access across all classes and teachers      |
| **Teacher (Math)**    | `t_ahmad`    | `teacher123` | Manages 10A quiz & views live submissions        |
| **Teacher (Physics)** | `t_sarah`    | `teacher123` | Manages 11A quiz                                 |
| **Student (10A)**     | `std_10a_01` | `student123` | Pre-submitted demo quiz (Score: 17.5 / 20)       |
| **Student (10A)**     | `std_10a_02` | `student123` | Fresh student ready to take the 15-question quiz |
| **Student (11A)**     | `std_11a_01` | `student123` | Access to Physics quiz                           |

(All student accounts follow the pattern `std_10a_01` to `std_10a_20`, `std_10b_01` to `std_10b_20`, and `std_11a_01` to `std_11a_20` with password `student123`).
