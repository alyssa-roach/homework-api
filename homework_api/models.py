"""
Models for the homework submission platform.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with role (student or teacher)."""

    ROLE_STUDENT = "student"
    ROLE_TEACHER = "teacher"
    ROLE_CHOICES = [
        (ROLE_STUDENT, "Student"),
        (ROLE_TEACHER, "Teacher"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)


class Assignment(models.Model):
    """Homework assignment that students submit to."""

    name = models.CharField(max_length=255)
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    """Student profile linked to a User."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student",
        limit_choices_to={"role": User.ROLE_STUDENT},
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()

    def __str__(self):
        return self.name


class Teacher(models.Model):
    """Teacher profile linked to a User."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="teacher",
        limit_choices_to={"role": User.ROLE_TEACHER},
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()

    def __str__(self):
        return self.name


class HomeworkSubmission(models.Model):
    """A student's submission for an assignment."""

    GRADE_CHOICES = [
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
        ("F", "F"),
    ]
    GRADE_VALUES = tuple(c[0] for c in GRADE_CHOICES)
    GRADE_VALUES_LOWER = frozenset(v.lower() for v in GRADE_VALUES)

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    graded_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_submissions",
    )
    content = models.TextField()
    submission_date = models.DateTimeField()
    grading_date = models.DateTimeField(null=True, blank=True)
    final_grade = models.CharField(
        max_length=1,
        choices=GRADE_CHOICES,
        null=True,
        blank=True,
    )
    teachers_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "assignment"],
                name="unique_student_assignment",
            )
        ]

    def __str__(self):
        return f"{self.student.name} - {self.assignment.name}"
