# AI_USAGE.md — AI Tooling & Human Verification Workflow

## 1. AI Tools Employed
- **Google Gemini**: Primary architectural reasoning and rapid code generation engine.
- **OpenAI ChatGPT**: Secondary code review, edge-case analysis, and algorithmic logic refinement.

---

## 2. Prompting Strategy & Direction Methodology
The AI models were treated as high-velocity junior/mid-level pair programmers operating under strict engineering boundaries set by the human engineer:

1. **Contract-First Architectural Scaffolding**:
   - Rather than asking for a generic web app, prompts strictly specified data models (SQLite schema, foreign keys, table indexes), role constraints, and RESTful routing signatures before generating HTML or FastAPI endpoints.

2. **Negative Marking Algorithmic Isolation**:
   - Explicit instructions were given to isolate the scoring formula: correct answers earn question points, wrong answers subtract 0.5 points, while **unanswered questions strictly grant 0 points without penalty**. The AI was directed to enforce a minimum boundary clamp of `0.0` so scores never turn negative.

3. **Zero-Configuration Autonomous Seeding**:
   - Directed the AI to package all realistic test data (4 teachers, 60 students across 10A, 10B, 11A, and a 15-question algebra exam) inside `database.py` so the application runs locally on a clean machine with a single terminal command.

---

## 3. Human Oversight & Critical AI Output Corrections
AI output was never blindly trusted; several critical oversights and hallucinations were caught and manually engineered:

1. **The Radio Button Negative-Marking Dilemma (Critical UX Intervention)**:
   - *AI Flaw*: The AI initially generated standard HTML `<input type="radio">` tags for the quiz options.
   - *Human Insight*: In standard browsers, once a radio button is selected, it cannot be deselected—only switched. Under negative marking, if a student taps an option by mistake and wants to leave it blank to avoid the penalty, the standard UI traps them into losing points.
   - *Engineering Fix*: Overrode the AI's template by engineering a custom JavaScript double-tap toggle logic and an explicit **"إلغاء الاختيار ✕" (Clear Choice)** button per question.

2. **Serverless Ephemeral Storage (`/tmp/quiz.db`)**:
   - *AI Flaw*: Initial scripts attempted to write `quiz.db` directly to the project root directory, which fails on Vercel's read-only serverless runtime.
   - *Engineering Fix*: Diagnosed the environment constraint and dynamically routed SQLite writes to `/tmp/quiz.db` during cloud execution.

3. **Mock Data Class Average Skew**:
   - *AI Flaw*: An early seed script injected a dummy 19-point submission for one student while all real quiz questions totaled 18 points, skewing class averages.
   - *Engineering Fix*: Audited database records, removed the synthetic anomaly, and normalized class metrics to reflect authentic student submissions.

4. **Rigorous Automated Testing (`pytest`)**:
   - Created test suites in `test_quiz.py` verifying database constraints (`UNIQUE(quiz_id, student_id)`), negative score clamping, and route security.

---

## 4. Conclusion
Using Gemini and ChatGPT accelerated boilerplate development and initial scaffolding. However, domain-specific empathy (such as fairness under negative marking) and runtime cloud troubleshooting required active human-in-the-loop architectural control.