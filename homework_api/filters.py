"""
Filter backends for submission list queries.
"""
import django_filters
from django.utils import timezone

from homework_api.models import HomeworkSubmission


class HomeworkSubmissionFilter(django_filters.FilterSet):
    """Filters for GET /submissions/."""

    grade = django_filters.CharFilter(method="filter_grade")
    assignment_name = django_filters.CharFilter(field_name="assignment__name", lookup_expr="icontains")
    date_from = django_filters.DateTimeFilter(field_name="submission_date", lookup_expr="gte")
    date_to = django_filters.DateTimeFilter(field_name="submission_date", lookup_expr="lte")
    student_name = django_filters.CharFilter(field_name="student__name", lookup_expr="icontains")

    class Meta:
        model = HomeworkSubmission
        fields = ["grade", "assignment_name", "date_from", "date_to", "student_name"]

    def filter_grade(self, queryset, name, value):
        value = (value or "").strip().lower()
        if not value:
            return queryset
        if value == "ungraded":
            return queryset.filter(final_grade__isnull=True)
        if value == "incomplete":
            now = timezone.now()
            return queryset.filter(
                final_grade__isnull=True,
                assignment__due_date__lt=now,
            )
        if value in HomeworkSubmission.GRADE_VALUES_LOWER:
            return queryset.filter(final_grade__iexact=value)
        return queryset.none()
