"""
Tests for homework_api serializers.
"""
import pytest

from homework_api.models import HomeworkSubmission
from homework_api.serializers import (
    AssignmentCreateSerializer,
    HomeworkSubmissionCreateSerializer,
    HomeworkSubmissionGradeSerializer,
)


@pytest.mark.django_db
def test_assignment_create_serializer_valid():
    """AssignmentCreateSerializer accepts valid data."""
    from django.utils import timezone
    from datetime import timedelta

    data = {
        "name": "New Assignment",
        "due_date": (timezone.now() + timedelta(days=5)).isoformat(),
    }
    serializer = AssignmentCreateSerializer(data=data)
    assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
def test_submission_create_serializer_valid():
    """HomeworkSubmissionCreateSerializer accepts valid data."""
    data = {"assignment_id": 1, "content": "My homework content"}
    serializer = HomeworkSubmissionCreateSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert not serializer.errors
    assert serializer.validated_data["assignment_id"] == 1
    assert serializer.validated_data["content"] == "My homework content"


def test_submission_create_serializer_empty_content_rejected():
    """HomeworkSubmissionCreateSerializer rejects empty content."""
    data = {"assignment_id": 1, "content": "   "}
    serializer = HomeworkSubmissionCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert "content" in serializer.errors


def test_grade_serializer_valid():
    """HomeworkSubmissionGradeSerializer accepts valid grades."""
    for grade in HomeworkSubmission.GRADE_VALUES:
        data = {"final_grade": grade, "teachers_notes": "Good job"}
        serializer = HomeworkSubmissionGradeSerializer(data=data)
        assert serializer.is_valid(), f"Grade {grade}: {serializer.errors}"


def test_grade_serializer_invalid_grade():
    """HomeworkSubmissionGradeSerializer rejects invalid grade."""
    data = {"final_grade": "X", "teachers_notes": ""}
    serializer = HomeworkSubmissionGradeSerializer(data=data)
    assert not serializer.is_valid()
    assert "final_grade" in serializer.errors
