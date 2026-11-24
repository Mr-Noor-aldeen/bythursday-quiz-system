# Arabic Quiz App | FastAPI + SQLite

A server-rendered quiz demo for an Arabic tutoring-center workflow: students view their class's quizzes, submit multiple-choice answers, and see their scores. Teachers see results for their quizzes, while an admin dashboard provides a center-wide overview and account-preview controls.

Built with Python, FastAPI, SQLite, Jinja2, and browser JavaScript. The interface uses Arabic right-to-left layouts.

## Try the demo

**[Open the live demo](https://bythursday-quiz-system.vercel.app/)**

This is a portfolio demo with public sample accounts, not a service for real student records. Do not enter personal information or reuse a real password. On Vercel, the SQLite file lives in temporary storage, so changes may disappear and are not guaranteed to be shared between instances.

| Role | Username | Demo password |
| --- | --- | --- |
| Student, class 10A | `std_10a_01` | `student123` |
| Teacher, mathematics | `t_ahmad` | `teacher123` |
| Admin | `nour_admin` | `admin123` |

These credentials are intentionally public and were already documented in this repository. They are not suitable for real accounts. The seeded quiz uses a deliberately broad 2020-2099 demo availability window so reviewers can try it. This is a demo setting, not a real assessment schedule. Existing local databases keep their saved dates.

## Implemented features

- **Student workflow:** class-specific quiz listings, multiple-choice questions, answer clearing, submission, and a result page.
- **Scoring:** per-question points, configurable negative marking, no penalty for unanswered questions, and a final score floored at zero.
- **Single submission:** an existing-submission check and a SQLite unique constraint on each student/quiz pair.
- **Quiz timing:** class membership and availability are checked both when opening and submitting a quiz; a browser countdown submits the form when it reaches zero. This is not a server-enforced exam timer.
- **Teacher dashboard:** quizzes, submitted results, and average percentages filtered by the teacher's quiz ownership.
- **Admin dashboard:** center-wide submission statistics, teacher/student rosters, and signed reviewer switching with return to the original admin.
- **Demo data:** one admin, four teachers, 60 students across three classes, and a 15-question mathematics quiz seeded on a fresh database.

There is no self-service registration, password-reset flow, or quiz-authoring interface in the current app.

## Tech stack

| Layer | Implementation |
| --- | --- |
| Backend | Python, FastAPI, Starlette responses |
| Data | SQLite through Python's `sqlite3`, SQL queries |
| Pages | Jinja2 templates, HTML, Arabic RTL layouts |
| Styling | Tailwind CSS CDN and Google Fonts |
| Browser behavior | JavaScript countdown and answer controls |
| Password storage | Standard-library PBKDF2-HMAC-SHA256 |
| Session integrity | Standard-library HMAC-SHA256 signed cookies |
| Tests | pytest, FastAPI TestClient, HTTPX |
| Demo hosting | Vercel |

## Run locally

Use a Python environment with `venv` and `pip` available. Python 3.10 was used for the verification described below. Dependency versions are ranged in `requirements.txt`, not locked.

```bash
git clone https://github.com/Mr-Noor-aldeen/bythursday-quiz-system.git
cd bythursday-quiz-system
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install dependencies and start the app:

```bash
python -m pip install -r requirements.txt
python run.py
```

Open **http://127.0.0.1:8000/** on the same computer. The runner binds to localhost, not to other devices on the network. It also reconciles dependencies from `requirements.txt` before launch, so the initial setup needs network access.

The first database access creates `quiz.db` and seeds sample data. Creating separate salted hashes for all 65 accounts adds time to that first initialization. Later starts reuse the database. The page styling and fonts also require access to their external CDNs.

Use the app's automatic seed path for this setup. The separate `seed.py` script has pre-existing duplicate-user and schema mismatches and is not the supported fresh-start command.

### Session-secret configuration

For a single-process local demo, the app generates a random in-memory signing key if `QUIZ_SESSION_SECRET` is unset and prints a warning. Restarting the process, including a development reload, invalidates those local sessions.

For deployment or multiple workers, securely generate a random secret of at least 32 bytes and supply it as `QUIZ_SESSION_SECRET`. Keep it out of source control and chat messages. All instances in the same environment must use the same stable value.

On Vercel:

1. Open the project's **Settings > Environment Variables**.
2. Add `QUIZ_SESSION_SECRET` as a **Secret** variable for Production and for Preview if preview deployments are used.
3. Deploy again after saving it. Changing the key signs out existing sessions.

On Vercel, startup fails clearly if this variable is missing or shorter than 32 bytes. Other deployed environments must also set it explicitly rather than relying on the local fallback.

## Tests and verification

```bash
python -m pytest -q
```

The runner also supports `python run.py --test`, which installs/reconciles dependencies before running pytest.

At commit `5e0f062`, all **37 tests passed** in a Python 3.10 environment. Coverage includes seed-data checks, scoring calculations, the duplicate-submission constraint, login behavior, password hashing, legacy password upgrades, cookie tampering and expiry, configuration checks, reviewer switching/authorization, and HTTP quiz-submission checks for class membership, both availability boundaries, scoring/results, and duplicate submission.

Some original scoring tests check calculations directly rather than submitting a quiz through HTTP. The suite is not full end-to-end coverage of every route.

Additional checks included real Uvicorn startup and the complete student login, quiz, submission, and result path on the Vercel preview and on production after merging PR #3. Earlier checks covered deployed admin/student login plus admin-to-teacher preview and return. This is verification of those paths, not a claim that every workflow or device has been tested.

## Security and current limits

### Improvements implemented

- Newly seeded passwords use PBKDF2-HMAC-SHA256 with 600,000 iterations and a separate random 16-byte salt per account.
- Existing plaintext password rows are upgraded only after a successful login. Rows for users who have not logged in remain in the legacy format until then.
- User and reviewer cookies are signed, purpose-bound, and expire after 12 hours. Signature verification uses constant-time comparison.
- Cookies are HttpOnly and SameSite=Lax; on Vercel they also use Secure for HTTPS.
- Reviewer proof is tied to the current target user and original admin. Login/logout clear reviewer state, and returning to admin requires valid reviewer proof.
- Old unsigned cookies are not accepted. Users with those sessions must sign in again; account passwords are unchanged.

### Limits before real use

- Public demo credentials still allow anyone to enter the demo accounts. Hashing does not make a published password private.
- Signed cookies are not encrypted. A stolen valid cookie can be replayed until expiry; logout clears the browser's copy rather than revoking it server-side.
- The submit endpoint rechecks class membership and availability, but does not enforce elapsed exam time on the server. A durable, shared attempt store is needed before adding reliable server-side duration enforcement. Do not use this as a high-stakes assessment system.
- Dedicated CSRF protection, login rate limiting, password recovery, and a full authorization/security audit are not implemented.
- SQLite under Vercel's `/tmp` is not durable shared storage. Use a suitable persistent database before collecting real records.
- Some routes are defined more than once in `main.py`; consolidating them is future cleanup, not a completed refactor.
- The seeded 2020-2099 availability window is deliberately broad for the portfolio demo. It is not a real assessment schedule; saved local databases retain their existing dates.

## Project layout

```text
main.py                    FastAPI routes and page responses
database.py                SQLite schema and automatic sample data
password_security.py       Password hashing and legacy-login upgrade
session_security.py        Cookie signing, expiry, and key configuration
templates/                 Arabic pages and browser behavior
test_quiz.py               Original data, scoring, and login checks
test_password_security.py  Password-storage regression tests
test_session_security.py   Session and reviewer-authorization tests
test_quiz_submission.py    HTTP submission-access and availability tests
run.py                     Dependency setup, dev server, and test runner
seed.py                    Older standalone seed script; see limits above
AI_USAGE.md                Project's AI-use notes
DECISIONS.md               Project's implementation notes
```

## Next steps

- Add server-enforced attempt deadlines using durable shared storage.
- Replace temporary demo storage with a persistent deployment database.
- Add CSRF protection, login throttling, and session revocation.
- Consolidate duplicate routes and reconcile the standalone seed script.
- Expand browser tests for the full student workflow and HTTP coverage beyond submission access.

These are planned improvements, not existing features.
