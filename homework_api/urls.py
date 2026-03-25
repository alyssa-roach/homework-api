"""
URL configuration for homework_api.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from homework_api.views import AssignmentViewSet, HomeworkSubmissionViewSet

router = DefaultRouter()
router.register(r"assignments", AssignmentViewSet, basename="assignment")
router.register(r"submissions", HomeworkSubmissionViewSet, basename="submission")

urlpatterns = [
    path("", include(router.urls)),
]
