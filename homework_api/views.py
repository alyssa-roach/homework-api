"""
API views for assignments and submissions.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from homework_api.filters import HomeworkSubmissionFilter
from homework_api.models import Assignment, HomeworkSubmission, Student, Teacher, User
from homework_api.permissions import IsStudent, IsSubmissionOwner, IsTeacher
from homework_api.serializers import (
    AssignmentCreateSerializer,
    AssignmentSerializer,
    HomeworkSubmissionCreateSerializer,
    HomeworkSubmissionGradeSerializer,
    HomeworkSubmissionSerializer,
)
from homework_api.services import grade_submission, submit_homework


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Return the authenticated user (for clients that need role after token login)."""
    return Response(
        {
            "username": request.user.username,
            "role": request.user.role,
            "email": request.user.email or "",
        }
    )


class AssignmentViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin, GenericViewSet):
    """ViewSet for Assignment list, retrieve, create."""

    queryset = Assignment.objects.all().order_by("-created_at")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return AssignmentCreateSerializer
        return AssignmentSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsTeacher()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save()


class HomeworkSubmissionViewSet(
    GenericViewSet,
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
):
    """ViewSet for homework submissions. PATCH allows teachers to grade."""

    serializer_class = HomeworkSubmissionSerializer
    filterset_class = HomeworkSubmissionFilter

    def get_queryset(self):
        qs = (
            HomeworkSubmission.objects.select_related("student", "assignment", "graded_by")
            .order_by("-submission_date")
        )
        role = getattr(self.request.user, "role", None)
        if role == User.ROLE_STUDENT:
            try:
                student = self.request.user.student
                return qs.filter(student=student)
            except Student.DoesNotExist:
                return qs.none()
        if role == User.ROLE_TEACHER:
            if Teacher.objects.filter(user_id=self.request.user.pk).exists():
                return qs
            return qs.none()
        return qs.none()

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsStudent()]
        if self.action in ("partial_update", "update"):
            return [IsAuthenticated(), IsTeacher()]
        return [IsAuthenticated(), IsSubmissionOwner()]

    def create(self, request, *args, **kwargs):
        serializer = HomeworkSubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            student = request.user.student
        except Student.DoesNotExist:
            return Response(
                {"detail": "User is not a student."},
                status=status.HTTP_403_FORBIDDEN,
            )
        submission, error = submit_homework(
            student=student,
            assignment_id=serializer.validated_data["assignment_id"],
            content=serializer.validated_data["content"],
        )
        if error:
            if "due date has passed" in error:
                return Response({"detail": error}, status=status.HTTP_409_CONFLICT)
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        out_serializer = HomeworkSubmissionSerializer(submission)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """Teacher grades a submission (PATCH /submissions/{id}/)."""
        instance = self.get_object()
        try:
            teacher = request.user.teacher
        except Teacher.DoesNotExist:
            return Response(
                {"detail": "User is not a teacher."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = HomeworkSubmissionGradeSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if "final_grade" not in serializer.validated_data:
            return Response(
                {"detail": "final_grade is required for grading."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        success, error = grade_submission(
            submission=instance,
            final_grade=serializer.validated_data["final_grade"],
            teachers_notes=serializer.validated_data.get("teachers_notes", ""),
            teacher=teacher,
        )
        if not success:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        out_serializer = HomeworkSubmissionSerializer(instance)
        return Response(out_serializer.data)

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
