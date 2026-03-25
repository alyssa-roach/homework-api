"""
Management command to seed students, teachers, and their auth tokens.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from rest_framework.authtoken.models import Token

from homework_api.models import Assignment, Student, Teacher, User


def _upsert_user(username, *, email, role, password, is_staff=False, is_superuser=False):
    """Create or normalize user so re-running seed fixes role, email, and password."""
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "role": role,
            "is_staff": is_staff,
            "is_superuser": is_superuser,
        },
    )
    user.email = email
    user.role = role
    user.is_staff = is_staff
    user.is_superuser = is_superuser
    user.set_password(password)
    user.save()
    return user


def _upsert_student_profile(user, *, name, email):
    student, _ = Student.objects.get_or_create(user=user, defaults={"name": name, "email": email})
    student.name = name
    student.email = email
    student.save(update_fields=["name", "email"])
    return student


def _upsert_teacher_profile(user, *, name, email):
    teacher, _ = Teacher.objects.get_or_create(user=user, defaults={"name": name, "email": email})
    teacher.name = name
    teacher.email = email
    teacher.save(update_fields=["name", "email"])
    return teacher


class Command(BaseCommand):
    help = "Create sample students, teachers, assignments, and auth tokens"

    def handle(self, *args, **options):
        student1_user = _upsert_user(
            "alice",
            email="alice@school.edu",
            role=User.ROLE_STUDENT,
            password="studentpass",
        )
        _upsert_student_profile(
            student1_user, name="Alice", email="alice@school.edu"
        )

        student2_user = _upsert_user(
            "bob",
            email="bob@school.edu",
            role=User.ROLE_STUDENT,
            password="studentpass",
        )
        _upsert_student_profile(
            student2_user, name="Bob", email="bob@school.edu"
        )

        teacher1_user = _upsert_user(
            "teacher1",
            email="teacher1@school.edu",
            role=User.ROLE_TEACHER,
            password="teacherpass",
            is_staff=False,
        )
        _upsert_teacher_profile(
            teacher1_user, name="Ms. Smith", email="teacher1@school.edu"
        )

        # Create tokens
        Token.objects.get_or_create(user=student1_user)
        Token.objects.get_or_create(user=student2_user)
        Token.objects.get_or_create(user=teacher1_user)

        # Create sample assignment
        from datetime import timedelta

        Assignment.objects.get_or_create(
            name="Math Homework 1",
            defaults={"due_date": timezone.now() + timedelta(days=7)},
        )
        Assignment.objects.get_or_create(
            name="Reading Assignment",
            defaults={"due_date": timezone.now() + timedelta(days=14)},
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded:\n"
                "  Students: alice (password: studentpass), bob (password: studentpass)\n"
                "  Teacher: teacher1 (password: teacherpass)\n"
                "  Assignments: Math Homework 1, Reading Assignment\n"
                "  Run: python manage.py shell -c \"from rest_framework.authtoken.models import Token; "
                "from homework_api.models import User; "
                "print('alice token:', Token.objects.get(user__username='alice').key); "
                "print('teacher1 token:', Token.objects.get(user__username='teacher1').key)\""
            )
        )
