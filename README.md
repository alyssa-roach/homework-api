# Backend Take Home Assignment

## Project Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (use requirements-dev.txt to include pytest)
pip install -r requirements-dev.txt

# Configure environment (copy and edit)
cp .env.example .env

# Run migrations
python manage.py migrate

# Seed sample users (students, teachers, assignments)
python manage.py seed_users

# Start server
python manage.py runserver
```

**Seeded users:** `alice` / `bob` (students, password: `studentpass`), `teacher1` (teacher, password: `teacherpass`)

## API Documentation

- **OpenAPI schema:** http://127.0.0.1:8000/api/schema/
- **Swagger UI:** http://127.0.0.1:8000/api/docs/

### Obtain token

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"studentpass"}'
# Returns: {"token":"<token>"}
```

### Assignments (authenticated)

```bash
# List assignments
curl -H "Authorization: Token <token>" http://127.0.0.1:8000/api/assignments/

# Create assignment (teacher only)
curl -X POST http://127.0.0.1:8000/api/assignments/ \
  -H "Authorization: Token <teacher_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Math HW 2","due_date":"2027-04-15T23:59:59Z"}'
```

### Submissions

```bash
# Submit homework (student)
curl -X POST http://127.0.0.1:8000/api/submissions/ \
  -H "Authorization: Token <student_token>" \
  -H "Content-Type: application/json" \
  -d '{"assignment_id":1,"content":"My homework answer"}'

# List submissions (student: own only; teacher: all)
curl -H "Authorization: Token <token>" "http://127.0.0.1:8000/api/submissions/?grade=ungraded&assignment_name=Math"

# Teacher filters: assignment_name, date_from, date_to, student_name
curl -H "Authorization: Token <teacher_token>" "http://127.0.0.1:8000/api/submissions/?date_from=2025-03-01&date_to=2025-03-31"

# Grade submission (teacher)
curl -X PATCH http://127.0.0.1:8000/api/submissions/1/ \
  -H "Authorization: Token <teacher_token>" \
  -H "Content-Type: application/json" \
  -d '{"final_grade":"A","teachers_notes":"Great work!"}'
```

### Run tests

```bash
# Install dev dependencies first if needed (see Project Setup)
pytest tests/ -v
```

### Terminal UI (demo client)

Lightweight Rich-based CLI that talks to the same REST API. **Every HTTP call is printed** in the terminal (and appended to `tui_api_calls.log` by default) so you can show interviewers exactly what hits the backend.

```bash
# Terminal 1: API
source .venv/bin/activate
python manage.py runserver

# Terminal 2: TUI
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m tui
```

Options:

- `--base-url http://127.0.0.1:8000` (or set `HOMEWORK_API_BASE_URL`)
- `--log-file path/to.log` (or `HOMEWORK_API_LOG_FILE`; use `--no-log-file` to disable)
- Login with seeded users (e.g. `alice` / `studentpass`, `teacher1` / `teacherpass`)

Flow: token login → role-aware menu (student: list/submit; teacher: list/grade/create assignment).

---

## Objective

Your objective is to implement a simple API for a school's homework submission platform that enables students to submit their homework and teachers to grade students' submissions. Please spend about **3–4 hours** on the assignment.

---

## Brief

Using Python, your challenge is to build a REST API for a school's homework submission platform. You are expected to design any required models and routes for your API and document your endpoints.

---

## Tasks

### Implementation Requirements

- **Language:** Python
- **Framework:** Any Python framework (we use Django Rest Framework, but this is not a requirement)

### Student API Routes

There should be API routes that allow students to:

- Submit their homework
- View their homework submissions
  - Filter by grade (A–F, incomplete, ungraded)
  - Filter by assignment name

### Teacher API Routes

There should be API routes that allow teachers to:

- See an overview of all homework submissions
  - Filter by assignment name
  - Filter by date range (to–from)
  - Filter by individual student name
- Grade individual homework submissions (A–F, comments)

### Testing

- Add unit tests for your business logic

---

## Homework Object Model

Each homework object should minimally include the following fields:

- Assignment
- Student
- Submission date
- Grading date
- Final grade
- Teachers Notes

---

## Evaluation Criteria

- **Python best practices**
- **Completeness:** Did you include all features?
- **Correctness:** Does the solution perform in a logical way?
- **Maintainability:** Is the solution written in a clean, maintainable way?
- **Testing:** Has the solution been adequately tested?
- **Documentation:** Is the API well-documented?

---

## Code Submit

Please organize, design, test, and document your code—then push your changes to Git.

Please send us the code **at least 24 hours before** the scheduled code review so that the team has a chance to review the project.

---

*All the best and happy coding,*  
*The Stride Team*
