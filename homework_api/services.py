"""
Business logic for submissions and grading.
"""
from typing import Optional, Tuple

from django.utils import timezone

from homework_api.models import Assignment, HomeworkSubmission, Student


class DueDatePassedError(Exception):
    """Raised when a student submits or resubmits after the assignment due date."""

    code = "DUE_DATE_PASSED"


def submit_homework(student: Student, assignment_id: int, content: str) -> Tuple[Optional[HomeworkSubmission], Optional[str]]:
    """
    Create or overwrite a homework submission.
    Raises DueDatePassedError if the assignment is past due.
    Returns (submission, error_message). If error_message is set, submission is None.
    """
    try:
        assignment = Assignment.objects.get(pk=assignment_id)
    except Assignment.DoesNotExist:
        return None, "Assignment not found"

    now = timezone.now()
    if assignment.due_date < now:
        raise DueDatePassedError("Assignment due date has passed")

    submission, _created = HomeworkSubmission.objects.update_or_create(
        student=student,
        assignment=assignment,
        defaults={
            "content": content,
            "submission_date": now,
            "final_grade": None,
            "teachers_notes": "",
            "grading_date": None,
            "graded_by": None,
        },
    )
    return submission, None


def grade_submission(submission: HomeworkSubmission, final_grade: str, teachers_notes: str, teacher) -> Tuple[bool, Optional[str]]:
    """
    Grade a submission. Returns (success, error_message).
    """
    if final_grade not in HomeworkSubmission.GRADE_VALUES:
        allowed = ", ".join(HomeworkSubmission.GRADE_VALUES)
        return False, f"Invalid grade. Must be one of: {allowed}"

    submission.final_grade = final_grade
    submission.teachers_notes = teachers_notes or ""
    submission.grading_date = timezone.now()
    submission.graded_by = teacher
    submission.save()
    return True, None
