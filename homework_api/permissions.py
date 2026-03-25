"""
Custom permission classes for role-based access.
"""
from rest_framework import permissions

from homework_api.models import HomeworkSubmission, Student


class IsStudent(permissions.BasePermission):
    """Only users with a Student profile may access."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, "role", None) == "student"


class IsTeacher(permissions.BasePermission):
    """Only users with a Teacher profile may access."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, "role", None) == "teacher"


class IsSubmissionOwner(permissions.BasePermission):
    """Students may only access their own submissions."""

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, HomeworkSubmission):
            return False
        if getattr(request.user, "role", None) != "student":
            return True  # Teachers can access any submission
        try:
            student = request.user.student
        except Student.DoesNotExist:
            return False
        return obj.student_id == student.id
