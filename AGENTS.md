# Agent Context: Homework Submission API

This document gives AI agents persistent context for iterating on this codebase.

## Project Purpose

REST API for a school homework submission platform. Students submit homework; teachers grade submissions. Built for a backend take-home assessment.

## Tech Stack

- **Python** 3.8+
- **Django** 4.2 + **Django REST Framework**
- **django-filter**, **django-environ**, **drf-spectacular**, **pytest**, **pytest-django**

## Architecture Overview

- **User** (custom, extends AbstractUser): has `role` (`student` | `teacher`)
- **Student** / **Teacher**: OneToOne to User; each person has one profile
- **Assignment**: `name`, `due_date`; students submit to assignments
- **HomeworkSubmission**: links Student + Assignment; fields: `content`, `submission_date`, `grading_date`, `final_grade`, `teachers_notes`; `UniqueConstraint(student, assignment)`

## Key Business Rules

- **Resubmission:** Students may overwrite their submission until `assignment.due_date` has passed; after that, return 409 Conflict.
- **Scoping:** Students see only their own submissions (via `Student` profile). Teachers see all submissions only when `role` is teacher **and** a `Teacher` profile exists; other roles get an empty list. When a student requests another's submission, return **404** (not 403) to avoid leaking resource existence.
- **Grading:** Teachers PATCH submissions with `final_grade` (A–F) and `teachers_notes`.
- **Auth:** Token auth via `Authorization: Token <token>`. No registration endpoint; use `python manage.py seed_users` for demo users.

## How to Run

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py seed_users
python manage.py runserver
pytest tests/ -v
```

## Terminal UI (demo)

- `python -m tui` — interactive client; logs all API calls to console + `tui_api_calls.log`
- Uses `GET /api/me/` after login for role-based menus

## Where Things Live

| Concern | Location |
|---------|----------|
| Models | `homework_api/models.py` |
| Business logic | `homework_api/services.py` |
| Permissions | `homework_api/permissions.py` |
| Filters | `homework_api/filters.py` |
| Views | `homework_api/views.py` |
| Serializers | `homework_api/serializers.py` |
| Management commands | `homework_api/management/commands/` |
| Tests | `tests/` |

## Full Spec

See `docs/ARCHITECTURE.md` for detailed technical reference.
