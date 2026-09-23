# Engineering Decisions & Trade-offs (DECISIONS.md)

This document details the architectural choices, assumptions, additions, and intentional deferrals made while delivering the quiz engine for Nour's tutoring center.

---

## 1. Assumptions Made
1. **Grading Boundary on Negative Marking:** When negative penalties exceed earned points, the total score is clamped to zero (`max(0.0, score)`). Negative aggregate scores are pedagogically demoralizing and rarely intended in secondary education.
2. **Unanswered Questions:** Blank/skipped questions neither grant points nor incur negative penalties. Penalties only apply to explicitly incorrect selections.
3. **Timer Expiration:** If the 20-minute client timer runs out, the client auto-submits current selections. The server verifies quiz availability windows (`start_date` to `end_date`).
4. **Data Delivery:** Because real spreadsheets will be provided later, structured seed generation (`seed.py`) was prioritized to model exact student/teacher cohorts realistically.

---

## 2. What Was Built That Nour Did Not Ask For (And Why)
- **Database-Level Unique Constraints (`UNIQUE(quiz_id, student_id)`):** To guarantee that a student cannot submit twice even under race conditions, network stutter, or rapid double-clicking.
- **Admin Unified Dashboard:** In addition to teacher views, an administrator role (`nour_admin`) was added so Nour can view center-wide metrics (average grades, total submissions across all 4 teachers).
- **Client-Side Live Watchdog Timer:** A persistent countdown bar that sticks to the top of the mobile viewport with automatic form dispatch upon zeroing out.
- **Native Arabic RTL & Mobile-First Touch Targets:** Styled using Tailwind CDN to ensure inputs and radio buttons are easily clickable on budget smartphones without UI breakage.

---

## 3. What Was Deliberately Left Out
- **File/Spreadsheet Import UI:** Nour noted that spreadsheets would arrive later. Building a brittle Excel parser without real sample files would introduce unverified assumptions; clean SQLite relational seeding was built instead.
- **Heavy JWT / Distributed Authentication:** Replaced with clean HTTP-only session cookies. This minimizes dependencies, avoids JWT expiration friction during evaluation, and runs instantly on any machine.
- **Rich-Text / WYSIWYG Question Editor:** Kept question authoring relational and programmatic to keep the code footprint clean and focused on quiz delivery and grading correctness.

---

## 4. What We Would Do With Another Week
1. **Excel/CSV Upload Pipeline:** Integrate Pandas/OpenPyXL with schema validation to ingest teacher rosters and quiz question banks seamlessly.
2. **Question Shuffling & Anti-Cheating Controls:** Randomize question order and answer options per student session to prevent peer copying in shared physical classrooms.
3. **Offline Re-connection Grace Window:** Store in-progress answers in browser `localStorage` to protect students from spotty mobile cellular connections in Amman.
4. **WebSocket Live Proctoring:** Allow teachers to see which students are actively taking the quiz in real time.