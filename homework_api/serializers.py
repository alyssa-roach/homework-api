"""
Serializers for the homework API.
"""
from rest_framework import serializers

from homework_api.models import Assignment, HomeworkSubmission, Student, Teacher


class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer for Assignment model."""

    class Meta:
        model = Assignment
        fields = ["id", "name", "due_date", "created_at"]
        read_only_fields = ["created_at"]


class AssignmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating assignments (teacher only)."""

    class Meta:
        model = Assignment
        fields = ["id", "name", "due_date"]


class StudentSerializer(serializers.ModelSerializer):
    """Minimal serializer for nested student info in submissions."""

    class Meta:
        model = Student
        fields = ["id", "name", "email"]


class TeacherSerializer(serializers.ModelSerializer):
    """Minimal serializer for nested teacher info."""

    class Meta:
        model = Teacher
        fields = ["id", "name", "email"]


class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for HomeworkSubmission (read)."""

    student = StudentSerializer(read_only=True)
    assignment = AssignmentSerializer(read_only=True)
    graded_by = TeacherSerializer(read_only=True, allow_null=True)

    class Meta:
        model = HomeworkSubmission
        fields = [
            "id",
            "assignment",
            "student",
            "content",
            "submission_date",
            "grading_date",
            "final_grade",
            "teachers_notes",
            "graded_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "student",
            "submission_date",
            "grading_date",
            "graded_by",
            "created_at",
            "updated_at",
        ]


class HomeworkSubmissionCreateSerializer(serializers.Serializer):
    """Serializer for student submitting homework."""

    assignment_id = serializers.IntegerField()
    content = serializers.CharField(allow_blank=False)

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Content cannot be empty")
        return value


class HomeworkSubmissionGradeSerializer(serializers.Serializer):
    """Serializer for teacher grading a submission."""

    final_grade = serializers.ChoiceField(choices=HomeworkSubmission.GRADE_CHOICES)
    teachers_notes = serializers.CharField(required=False, allow_blank=True, default="")
