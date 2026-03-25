"""
Business logic for submissions and grading.
"""
from typing import Optional, Tuple

from django.utils import timezone

from homework_api.models import Assignment, HomeworkSubmission, Student


def submit_homework(student: Student, assignment_id: int, content: str) -> Tuple[Optional[HomeworkSubmission], Optional[str]]:
    """
    Create or overwrite a homework submission.
    Returns (submission, error_message). If error_message is set, submission is None.
    """
    try:
        assignment = Assignment.objects.get(pk=assignment_id)
    except Assignment.DoesNotExist:
        return None, "Assignment not found"

    now = timezone.now()
    if assignment.due_date < now:
        return None, "Assignment due date has passed"

    existing = HomeworkSubmission.objects.filter(
        student=student,
        assignment=assignment,
    ).first()

    if existing:
        # Resubmission: overwrite and clear grade for regrading
        existing.content = content
        existing.submission_date = now
        existing.final_grade = None
        existing.teachers_notes = ""
        existing.grading_date = None
        existing.graded_by = None
        existing.save()
        return existing, None

    # Concurrent first submits for the same (student, assignment) can race and raise IntegrityError.
    submission = HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student,
        content=content,
        submission_date=now,
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
