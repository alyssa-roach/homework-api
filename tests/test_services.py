"""
Tests for homework_api services.
"""
from unittest.mock import patch

import pytest
from django.utils import timezone

from homework_api.models import Assignment, HomeworkSubmission, Student, Teacher, User
from homework_api.services import DueDatePassedError, grade_submission, submit_homework


@pytest.mark.django_db
def test_submit_homework_creates_new(student_user, assignment):
    """submit_homework creates new submission when none exists."""
    sub, err = submit_homework(student_user["student"], assignment.id, "My content")
    assert err is None
    assert sub is not None
    assert sub.content == "My content"


@pytest.mark.django_db
def test_submit_homework_past_due_raises_due_date_passed(student_user, past_due_assignment):
    """submit_homework raises DueDatePassedError when assignment is past due."""
    with pytest.raises(DueDatePassedError) as exc_info:
        submit_homework(
            student_user["student"],
            past_due_assignment.id,
            "Late",
        )
    assert exc_info.value.code == "DUE_DATE_PASSED"
    assert "due date" in str(exc_info.value).lower()


@pytest.mark.django_db
def test_submit_homework_resubmission_overwrites(student_user, assignment):
    """submit_homework overwrites existing submission before due."""
    s1, _ = submit_homework(student_user["student"], assignment.id, "First")
    s2, err = submit_homework(student_user["student"], assignment.id, "Second")
    assert err is None
    assert s2.id == s1.id
    assert s2.content == "Second"


@pytest.mark.django_db
def test_submit_homework_uses_update_or_create_for_race_safe_upsert(student_user, assignment):
    """
    submit_homework must delegate to HomeworkSubmission.objects.update_or_create so
    Django's get_or_create IntegrityError retry can run on concurrent first inserts.
    (Real thread contention is unreliable on SQLite's writer lock; this asserts
    the intended ORM primitive and resubmission defaults.)
    """
    student = student_user["student"]
    with patch.object(
        HomeworkSubmission.objects,
        "update_or_create",
        wraps=HomeworkSubmission.objects.update_or_create,
    ) as upsert:
        sub, err = submit_homework(student, assignment.id, "concurrent-proof body")
    assert err is None
    assert sub is not None
    assert sub.content == "concurrent-proof body"
    assert upsert.call_count == 1
    call_kw = upsert.call_args.kwargs
    assert call_kw["student"] == student
    assert call_kw["assignment"].pk == assignment.pk
    defaults = call_kw["defaults"]
    assert defaults["content"] == "concurrent-proof body"
    assert defaults["final_grade"] is None
    assert defaults["teachers_notes"] == ""
    assert defaults["grading_date"] is None
    assert defaults["graded_by"] is None
    assert defaults["submission_date"] == sub.submission_date


@pytest.mark.django_db
def test_grade_submission_success(teacher_user, student_user, assignment):
    """grade_submission sets grade and teachers_notes."""
    sub = HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="X",
        submission_date=timezone.now(),
    )
    success, err = grade_submission(
        sub,
        "A",
        "Great work!",
        teacher_user["teacher"],
    )
    assert success
    assert err is None
    sub.refresh_from_db()
    assert sub.final_grade == "A"
    assert sub.teachers_notes == "Great work!"
    assert sub.grading_date is not None


@pytest.mark.django_db
def test_grade_submission_invalid_grade(teacher_user, student_user, assignment):
    """grade_submission returns error for invalid grade."""
    sub = HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="X",
        submission_date=timezone.now(),
    )
    success, err = grade_submission(sub, "X", "", teacher_user["teacher"])
    assert not success
    assert err
    assert "invalid" in err.lower()
