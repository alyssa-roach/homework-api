# Architecture Reference

## Data Model

```
User (custom, role: student|teacher)
  ├── Student (OneToOne)
  └── Teacher (OneToOne)

Assignment (name, due_date)
  └── HomeworkSubmission (student, assignment, content, submission_date, grading_date, final_grade, teachers_notes)
        └── UniqueConstraint(student, assignment)
```

## API Routes

| Method | Path | Role | Purpose |
|--------|------|------|---------|
| POST | `/api/auth/token/` | - | Login: `username`, `password` → `token` |
| GET | `/api/me/` | All | Current user: `username`, `role`, `email` (after token auth) |
| GET | `/api/assignments/` | All | List assignments (paginated) |
| POST | `/api/assignments/` | Teacher | Create assignment |
| GET | `/api/assignments/{id}/` | All | Retrieve assignment |
| POST | `/api/submissions/` | Student | Submit homework (create or overwrite if before due) |
| GET | `/api/submissions/` | Student/Teacher | List (student: own; teacher: all if `Teacher` profile exists) |
| GET | `/api/submissions/{id}/` | Student/Teacher | Retrieve (404 if student accesses another's) |
| PATCH | `/api/submissions/{id}/` | Teacher | Grade (`final_grade`, `teachers_notes`) |

## Query Parameters (GET /api/submissions/)

- **Student:** `grade` (A–F | ungraded | incomplete), `assignment_name`
- **Teacher:** `assignment_name`, `date_from`, `date_to`, `student_name`

## Auth & Scope

- Token auth: `Authorization: Token <key>`
- Students (`role == student`): list/retrieve scoped to `request.user.student`; missing `Student` profile → empty list / 404 on detail
- Teachers (`role == teacher`): list all submissions only if a `Teacher` row exists for the user; otherwise empty list
- Any other `role` (or missing profile for that role): submission list is empty
- Return 404 (not 403) when a student requests another student's submission (out-of-scope ids are not in the queryset)

## Submission Flow

1. **Create:** POST with `assignment_id`, `content`; unknown assignment → **400**; past due → **409**; first submit or resubmit before due → **201**
2. **Resubmit (before due):** Overwrite existing row; clear grade and grading metadata for regrading
3. **Grade:** Teacher PATCH with `final_grade` (A–F), `teachers_notes`; set `grading_date`, `graded_by`

## Testing

- `pytest tests/ -v`
- Fixtures: `student_client`, `teacher_client`, `assignment`, `past_due_assignment`
- Use `@pytest.mark.django_db` for DB tests
