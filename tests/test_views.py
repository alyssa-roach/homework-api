"""
Tests for homework_api API endpoints.
"""
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from homework_api.models import Assignment, HomeworkSubmission, Student, Teacher, User


@pytest.mark.django_db
def test_me_endpoint_requires_auth(api_client):
    """GET /api/me/ without token returns 401."""
    resp = api_client.get("/api/me/")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_me_endpoint_returns_role(student_client, student_user):
    """GET /api/me/ returns username and role for logged-in user."""
    resp = student_client.get("/api/me/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "teststudent"
    assert data["role"] == "student"


@pytest.mark.django_db
def test_auth_token_endpoint(api_client):
    """POST /api/auth/token/ returns token for valid credentials."""
    from homework_api.models import User

    User.objects.create_user(username="authuser", password="pass123", role="student")
    resp = api_client.post(
        "/api/auth/token/",
        {"username": "authuser", "password": "pass123"},
        format="json",
    )
    assert resp.status_code == 200
    assert "token" in resp.json()


@pytest.mark.django_db
def test_assignments_list_requires_auth(api_client):
    """GET /api/assignments/ requires authentication."""
    resp = api_client.get("/api/assignments/")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_assignments_list_student(student_client, assignment):
    """Student can list assignments."""
    resp = student_client.get("/api/assignments/")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert len(data["results"]) >= 1


@pytest.mark.django_db
def test_assignments_create_teacher(teacher_client, assignment):
    """Teacher can create assignment."""
    due = (timezone.now() + timedelta(days=14)).isoformat()
    resp = teacher_client.post(
        "/api/assignments/",
        {"name": "New HW", "due_date": due},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "New HW"


@pytest.mark.django_db
def test_assignments_create_forbidden_student(student_client):
    """Student cannot create assignment."""
    due = (timezone.now() + timedelta(days=14)).isoformat()
    resp = student_client.post(
        "/api/assignments/",
        {"name": "New HW", "due_date": due},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_submit_homework(student_client, assignment):
    """Student can submit homework."""
    resp = student_client.post(
        "/api/submissions/",
        {"assignment_id": assignment.id, "content": "My homework answer"},
        format="json",
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "My homework answer"
    assert data["assignment"]["id"] == assignment.id


@pytest.mark.django_db
def test_submit_past_due_returns_409(student_client, past_due_assignment):
    """Student cannot submit after due date."""
    resp = student_client.post(
        "/api/submissions/",
        {
            "assignment_id": past_due_assignment.id,
            "content": "Late submission",
        },
        format="json",
    )
    assert resp.status_code == 409


@pytest.mark.django_db
def test_submit_forbidden_teacher(teacher_client, assignment):
    """Teacher cannot submit homework."""
    resp = teacher_client.post(
        "/api/submissions/",
        {"assignment_id": assignment.id, "content": "Teacher tries"},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_student_sees_only_own_submissions(student_client, student_user, assignment):
    """Student list shows only their submissions."""
    other_user = User.objects.create_user(username="otherstudent", password="x", role="student")
    other_student = Student.objects.create(user=other_user, name="Other", email="other@x.com")

    HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="Mine",
        submission_date=timezone.now(),
    )
    HomeworkSubmission.objects.create(
        assignment=assignment,
        student=other_student,
        content="Theirs",
        submission_date=timezone.now(),
    )

    resp = student_client.get("/api/submissions/")
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["content"] == "Mine"


@pytest.mark.django_db
def test_teacher_can_grade(teacher_client, student_user, assignment):
    """Teacher can grade a submission."""
    sub = HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="To grade",
        submission_date=timezone.now(),
    )
    resp = teacher_client.patch(
        f"/api/submissions/{sub.id}/",
        {"final_grade": "A", "teachers_notes": "Excellent"},
        format="json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["final_grade"] == "A"
    assert data["teachers_notes"] == "Excellent"


@pytest.mark.django_db
def test_teacher_can_regrade_with_second_patch(teacher_client, student_user, assignment):
    """Teacher can PATCH the same submission again to change grade and notes."""
    sub = HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="Paper",
        submission_date=timezone.now(),
    )
    first = teacher_client.patch(
        f"/api/submissions/{sub.id}/",
        {"final_grade": "A", "teachers_notes": "First pass"},
        format="json",
    )
    assert first.status_code == 200
    assert first.json()["final_grade"] == "A"
    assert first.json()["teachers_notes"] == "First pass"

    second = teacher_client.patch(
        f"/api/submissions/{sub.id}/",
        {"final_grade": "B", "teachers_notes": "After review"},
        format="json",
    )
    assert second.status_code == 200
    body = second.json()
    assert body["final_grade"] == "B"
    assert body["teachers_notes"] == "After review"

    sub.refresh_from_db()
    assert sub.final_grade == "B"
    assert sub.teachers_notes == "After review"


@pytest.mark.django_db
def test_student_gets_404_for_others_submission(student_client, student_user, assignment):
    """Student GET another's submission returns 404."""
    other_user = User.objects.create_user(username="otherstu", password="x", role="student")
    other_student = Student.objects.create(user=other_user, name="Other", email="o@x.com")
    sub = HomeworkSubmission.objects.create(
        assignment=assignment,
        student=other_student,
        content="Not mine",
        submission_date=timezone.now(),
    )
    resp = student_client.get(f"/api/submissions/{sub.id}/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_resubmission_before_due_overwrites(student_client, student_user, assignment):
    """Student can resubmit before due date (overwrites)."""
    sub = HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="First",
        submission_date=timezone.now(),
    )
    resp = student_client.post(
        "/api/submissions/",
        {"assignment_id": assignment.id, "content": "Second"},
        format="json",
    )
    assert resp.status_code == 201
    sub.refresh_from_db()
    assert sub.content == "Second"
    assert HomeworkSubmission.objects.filter(assignment=assignment, student=student_user["student"]).count() == 1


@pytest.mark.django_db
def test_submit_invalid_assignment_id_returns_400(student_client):
    """POST submission with non-existent assignment_id returns 400."""
    bad_id = (Assignment.objects.order_by("-id").values_list("id", flat=True).first() or 0) + 10_000
    resp = student_client.post(
        "/api/submissions/",
        {"assignment_id": bad_id, "content": "No such assignment"},
        format="json",
    )
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.django_db
def test_teacher_filters_submissions_grade_ungraded(teacher_client, student_user, assignment):
    """Teacher can filter list by grade=ungraded."""
    other_assignment = Assignment.objects.create(
        name="Second HW",
        due_date=timezone.now() + timedelta(days=5),
    )
    ungraded = HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="Todo",
        submission_date=timezone.now(),
        final_grade=None,
    )
    graded = HomeworkSubmission.objects.create(
        assignment=other_assignment,
        student=student_user["student"],
        content="Done",
        submission_date=timezone.now(),
        final_grade="A",
    )
    resp = teacher_client.get("/api/submissions/", {"grade": "ungraded"})
    assert resp.status_code == 200
    ids = {row["id"] for row in resp.json()["results"]}
    assert ungraded.id in ids
    assert graded.id not in ids


@pytest.mark.django_db
def test_teacher_filters_submissions_grade_letter_http(teacher_client, student_user, assignment):
    """Teacher can filter list by letter grade via grade= (case-insensitive)."""
    other_assignment = Assignment.objects.create(
        name="Letter filter HW",
        due_date=timezone.now() + timedelta(days=5),
    )
    sub_a = HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="Got A",
        submission_date=timezone.now(),
        final_grade="A",
    )
    HomeworkSubmission.objects.create(
        assignment=other_assignment,
        student=student_user["student"],
        content="Got B",
        submission_date=timezone.now(),
        final_grade="B",
    )
    for param in ("a", "A"):
        resp = teacher_client.get("/api/submissions/", {"grade": param})
        assert resp.status_code == 200
        ids = {row["id"] for row in resp.json()["results"]}
        assert ids == {sub_a.id}


@pytest.mark.django_db
def test_teacher_filters_submissions_grade_incomplete(
    teacher_client, student_user, assignment, past_due_assignment
):
    """Teacher can filter by grade=incomplete (ungraded and past due)."""
    incomplete = HomeworkSubmission.objects.create(
        assignment=past_due_assignment,
        student=student_user["student"],
        content="Late ungraded",
        submission_date=timezone.now(),
        final_grade=None,
    )
    not_incomplete = HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="Still open",
        submission_date=timezone.now(),
        final_grade=None,
    )
    resp = teacher_client.get("/api/submissions/", {"grade": "incomplete"})
    assert resp.status_code == 200
    ids = {row["id"] for row in resp.json()["results"]}
    assert incomplete.id in ids
    assert not_incomplete.id not in ids


@pytest.mark.django_db
def test_teacher_filters_submissions_assignment_name(teacher_client, student_user, assignment):
    """Teacher can filter by assignment_name (icontains)."""
    other = Assignment.objects.create(
        name="Science Lab",
        due_date=timezone.now() + timedelta(days=3),
    )
    sub_math = HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="Math work",
        submission_date=timezone.now(),
    )
    sub_sci = HomeworkSubmission.objects.create(
        assignment=other,
        student=student_user["student"],
        content="Science work",
        submission_date=timezone.now(),
    )
    resp = teacher_client.get("/api/submissions/", {"assignment_name": "Test"})
    assert resp.status_code == 200
    ids = {row["id"] for row in resp.json()["results"]}
    assert sub_math.id in ids
    assert sub_sci.id not in ids


@pytest.mark.django_db
def test_teacher_filters_submissions_date_range(teacher_client, student_user, assignment):
    """Teacher can filter by date_from / date_to on submission_date."""
    other_assignment = Assignment.objects.create(
        name="Date range HW",
        due_date=timezone.now() + timedelta(days=5),
    )
    early = timezone.now() - timedelta(days=10)
    late = timezone.now() - timedelta(days=2)
    sub_early = HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="Early",
        submission_date=early,
    )
    sub_late = HomeworkSubmission.objects.create(
        assignment=other_assignment,
        student=student_user["student"],
        content="Late",
        submission_date=late,
    )
    start = (timezone.now() - timedelta(days=7)).isoformat()
    end = (timezone.now() - timedelta(days=1)).isoformat()
    resp = teacher_client.get(
        "/api/submissions/",
        {"date_from": start, "date_to": end},
    )
    assert resp.status_code == 200
    ids = {row["id"] for row in resp.json()["results"]}
    assert sub_early.id not in ids
    assert sub_late.id in ids


@pytest.mark.django_db
def test_teacher_filters_submissions_student_name(teacher_client, assignment):
    """Teacher can filter by student_name (icontains)."""
    u_alice = User.objects.create_user(username="alicefilter", password="x", role=User.ROLE_STUDENT)
    u_bob = User.objects.create_user(username="bobfilter", password="x", role=User.ROLE_STUDENT)
    s_alice = Student.objects.create(user=u_alice, name="Alice Uniquexyz", email="a@x.com")
    s_bob = Student.objects.create(user=u_bob, name="Bob Other", email="b@x.com")
    sub_alice = HomeworkSubmission.objects.create(
        assignment=assignment,
        student=s_alice,
        content="From Alice",
        submission_date=timezone.now(),
    )
    HomeworkSubmission.objects.create(
        assignment=assignment,
        student=s_bob,
        content="From Bob",
        submission_date=timezone.now(),
    )
    resp = teacher_client.get("/api/submissions/", {"student_name": "Uniquexyz"})
    assert resp.status_code == 200
    ids = {row["id"] for row in resp.json()["results"]}
    assert ids == {sub_alice.id}


@pytest.mark.django_db
def test_teacher_filters_invalid_grade_returns_empty(teacher_client, student_user, assignment):
    """Unknown grade= value yields no rows (not an unfiltered list)."""
    HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="Any",
        submission_date=timezone.now(),
    )
    resp = teacher_client.get("/api/submissions/", {"grade": "not-a-valid-grade"})
    assert resp.status_code == 200
    assert resp.json()["results"] == []


@pytest.mark.django_db
def test_submissions_list_unknown_role_sees_no_submissions(student_user, assignment):
    """Authenticated user whose role is not student or teacher must not see any submissions."""
    lurker = User.objects.create_user(username="lurker", password="x", role=User.ROLE_STUDENT)
    User.objects.filter(pk=lurker.pk).update(role="alumni")
    lurker.refresh_from_db()
    token = Token.objects.create(user=lurker)
    HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="Classified",
        submission_date=timezone.now(),
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    resp = client.get("/api/submissions/")
    assert resp.status_code == 200
    assert resp.json()["results"] == []


@pytest.mark.django_db
def test_submissions_list_teacher_without_profile_sees_no_submissions(student_user, assignment):
    """Teacher role without a Teacher profile must not get the global submissions queryset."""
    orphan = User.objects.create_user(
        username="teacher_noplace",
        password="x",
        role=User.ROLE_TEACHER,
    )
    assert not Teacher.objects.filter(user=orphan).exists()
    token = Token.objects.create(user=orphan)
    HomeworkSubmission.objects.create(
        assignment=assignment,
        student=student_user["student"],
        content="Private",
        submission_date=timezone.now(),
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    resp = client.get("/api/submissions/")
    assert resp.status_code == 200
    assert resp.json()["results"] == []
