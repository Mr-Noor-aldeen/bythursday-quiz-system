# DECISIONS.md — Engineering Decisions & Architectural Tradeoffs

## 1. Assumptions Made

1. **Negative Marking Rules**:
   - Incorrect answers incur a penalty of **-0.5 points**.
   - **Blank / unanswered questions incur 0 points and 0 penalty.** Penalizing students for leaving questions blank would encourage wild guessing rather than honest knowledge assessment.
   - The total score is clamped to `0.0` (scores cannot fall below zero).

2. **Strict Single-Attempt Enforcement**:
   - Enforced at the database level via a `UNIQUE(quiz_id, student_id)` constraint on the `submissions` table, and at the route level via FastAPI redirection. Once submitted, visiting `/quiz/{id}` immediately redirects to `/quiz/{id}/result`.

3. **Cohort / Class-Based Isolation**:
   - Students in section `10A` only have visibility into quizzes assigned to `10A`. Cross-class quiz access is prevented.

4. **Arabic RTL & Mobile-First Priority**:
   - The majority of students take quizzes on smartphones. The interface is built entirely in Arabic RTL with comfortable 48px touch targets for answer options.

---

## 2. Built Beyond the Brief (And Why)

1. **Center Director Dashboard (`nour_admin`)**:
   - Nour requested teacher tools, but as the owner of an Amman center with 300 students and 12 teachers, she needs high-level operational visibility: total submissions and school-wide grade averages.

2. **Radio Button Deselection UX & Clear Option Button**:
   - Standard HTML radio buttons cannot be unchecked. Under negative marking, this unfairly penalizes students who make accidental taps. We engineered a double-tap uncheck mechanism and a clear button per question.

3. **Unanswered Question Modal Warning**:
   - A client-side check alerts students before final submission if they have blank questions, clarifying that blanks carry zero penalty.

4. **Automated Zero-Timer Submission Flush**:
   - When the 20-minute countdown reaches zero, the form automatically submits to prevent overtime tampering.

---

## 3. Deliberately Left Out (And Why)

1. **Public Self-Registration**:
   - Private tutoring centers maintain precise student rosters. Public signups invite unauthorized users and pollute data. Roster accounts are seeded centrally.

2. **Heavy Mathematical Rendering Libraries**:
   - Arabic algebra questions (e.g. 2س + 6 = 16) render cleanly via UTF-8 typography. Avoiding heavy libraries preserves instant mobile load times on weak data connections.

---

## 4. Next Steps With Another Week

1. **Persistent Cloud Database (Turso / libSQL)**:
   - Connect an external persistent database to replace ephemeral local SQLite files, ensuring permanent cloud storage across serverless deployments.

2. **Bulk Spreadsheet Ingestion (CSV / XLSX)**:
   - Build a drag-and-drop parser for teachers to upload student rosters and quiz question banks directly from Excel files.