"""
Pytest fixtures for homework API tests.
"""
import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from homework_api.models import Assignment, Student, Teacher, User


@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


@pytest.fixture
def student_user(db):
    """Create a student user with token."""
    user = User.objects.create_user(
        username="teststudent",
        password="testpass123",
        email="student@test.edu",
        role=User.ROLE_STUDENT,
    )
    student = Student.objects.create(user=user, name="Test Student", email="student@test.edu")
    token = Token.objects.create(user=user)
    return {"user": user, "student": student, "token": token.key}


@pytest.fixture
def teacher_user(db):
    """Create a teacher user with token."""
    user = User.objects.create_user(
        username="testteacher",
        password="testpass123",
        email="teacher@test.edu",
        role=User.ROLE_TEACHER,
    )
    teacher = Teacher.objects.create(user=user, name="Test Teacher", email="teacher@test.edu")
    token = Token.objects.create(user=user)
    return {"user": user, "teacher": teacher, "token": token.key}


@pytest.fixture
def student_client(api_client, student_user):
    """API client authenticated as student."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {student_user['token']}")
    return api_client


@pytest.fixture
def teacher_client(api_client, teacher_user):
    """API client authenticated as teacher."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {teacher_user['token']}")
    return api_client


@pytest.fixture
def assignment(db):
    """Create a sample assignment with future due date."""
    from django.utils import timezone
    from datetime import timedelta

    return Assignment.objects.create(
        name="Test Assignment",
        due_date=timezone.now() + timedelta(days=7),
    )


@pytest.fixture
def past_due_assignment(db):
    """Create an assignment with past due date."""
    from django.utils import timezone
    from datetime import timedelta

    return Assignment.objects.create(
        name="Past Due Assignment",
        due_date=timezone.now() - timedelta(days=1),
    )
