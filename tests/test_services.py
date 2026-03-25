"""
Tests for homework_api services.
"""
from datetime import timedelta

import pytest
from django.utils import timezone

from homework_api.models import Assignment, HomeworkSubmission, Student, Teacher, User
from homework_api.services import grade_submission, submit_homework


@pytest.mark.django_db
def test_submit_homework_creates_new(student_user, assignment):
    """submit_homework creates new submission when none exists."""
    sub, err = submit_homework(student_user["student"], assignment.id, "My content")
    assert err is None
    assert sub is not None
    assert sub.content == "My content"


@pytest.mark.django_db
def test_submit_homework_past_due_returns_error(student_user, past_due_assignment):
    """submit_homework returns error when assignment is past due."""
    sub, err = submit_homework(
        student_user["student"],
        past_due_assignment.id,
        "Late",
    )
    assert sub is None
    assert "due date" in err.lower()


@pytest.mark.django_db
def test_submit_homework_resubmission_overwrites(student_user, assignment):
    """submit_homework overwrites existing submission before due."""
    s1, _ = submit_homework(student_user["student"], assignment.id, "First")
    s2, err = submit_homework(student_user["student"], assignment.id, "Second")
    assert err is None
    assert s2.id == s1.id
    assert s2.content == "Second"


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
    assert "invalid" in err.lower()
