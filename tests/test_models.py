"""
Tests for homework_api models.
"""
from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone

from homework_api.models import Assignment, HomeworkSubmission, Student, Teacher, User


@pytest.mark.django_db
def test_create_assignment():
    """Assignment can be created with name and due_date."""
    due = timezone.now() + timedelta(days=7)
    a = Assignment.objects.create(name="Math HW", due_date=due)
    assert a.id is not None
    assert a.name == "Math HW"
    assert a.created_at is not None


@pytest.mark.django_db
def test_homework_submission_unique_constraint(student_user, assignment):
    """Only one submission per student per assignment."""
    student = student_user["student"]
    HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student,
        content="First submission",
        submission_date=timezone.now(),
    )
    with pytest.raises(IntegrityError):
        HomeworkSubmission.objects.create(
            assignment=assignment,
            student=student,
            content="Duplicate",
            submission_date=timezone.now(),
        )


@pytest.mark.django_db
def test_grade_choices():
    """HomeworkSubmission accepts valid grades."""
    user = User.objects.create_user(username="u1", password="x", role=User.ROLE_STUDENT)
    student = Student.objects.create(user=user, name="S", email="s@x.com")
    a = Assignment.objects.create(name="A", due_date=timezone.now() + timedelta(days=1))
    sub = HomeworkSubmission.objects.create(
        assignment=a,
        student=student,
        content="x",
        submission_date=timezone.now(),
    )
    for grade in HomeworkSubmission.GRADE_VALUES:
        sub.final_grade = grade
        sub.save()
        sub.refresh_from_db()
        assert sub.final_grade == grade
