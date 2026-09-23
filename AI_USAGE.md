# AI Collaboration & Engineering Workflow (AI_USAGE.md)

In accordance with the assessment requirements, AI tools were leveraged as the primary development accelerator. This document details the prompts, architectural direction, verification mechanisms, and manual reviews applied throughout development.

---

## 1. Tools Employed
- **Large Language Model (LLM) Coding Assistant:** Used for rapid modular scaffolding, relational database schema formulation, FastAPI routing, and algorithmic score verification.
- **Python / Pytest Runtime:** Used as the deterministic ground truth to validate business rules and catch runtime/logical regressions.

---

## 2. Direction & Prompting Methodology
Rather than requesting a single monolithic application, implementation was broken into isolated architectural iterations:

1. **Schema Formulation:** 
   - Directed the model to write an SQLite schema with strict relational integrity.
   - Mandated explicit columns for negative grading (`has_negative_marking`, `negative_mark_value`) and database-level retake prevention (`UNIQUE(quiz_id, student_id)`).

2. **Realistic Cohort Generation (`seed.py`):**
   - Prompted generation of three specific cohorts (`10A`, `10B`, `11A`) totaling 60 students with authentic Arabic naming conventions.
   - Generated 4 distinct teacher profiles and a comprehensive 15-question Math quiz with variable question weighting (1.0 to 2.0 points).

3. **Backend Logic & Routing (`main.py`):**
   - Structured session-based role routing (Student vs. Teacher/Admin).
   - Enforced negative marking computation:
     $$\text{Score} = \max\left(0.0, \sum \text{Correct} - \sum \text{Wrong Penalty}\right)$$
   - Ensured unanswered/skipped questions incur zero penalty.

4. **Mobile-Responsive RTL UI:**
   - Guided generation of Arabic-first templates using Tailwind CSS via CDN.
   - Enforced high-contrast touch targets, top-anchored sticky countdown timers, and automatic form submission upon timer expiration.

5. **Automated Test Scenarios (`test_quiz.py`):**
   - Instructed the model to write automated unit tests specifically covering:
     - Authentication flow (valid vs. invalid credentials).
     - Exact mathematical correctness of negative marking penalty deductions.
     - Enforcement of the single-submission constraint.

---

## 3. Verification & Code Review
Every code artifact was validated against three verification checkpoints:

- **Mathematical Audit:** Verified that penalty subtractions never produce negative aggregate grades and verified that blank submissions do not deduct points.
- **Automated Test Suite:** Ran `pytest -v test_quiz.py` to confirm all 3 automated tests passed without assertion errors.
- **Manual End-to-End Simulation:** Verified the mobile viewport layout via browser developer tools, submitted a live test as student `std_10a_02`, and verified score aggregation on the teacher dashboard (`t_ahmad`).