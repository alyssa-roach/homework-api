"""Root URLconf: admin, API (homework app), auth token, OpenAPI schema and Swagger UI."""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token

from homework_api.views import current_user

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("homework_api.urls")),
    path("api/me/", current_user),
    path("api/auth/token/", obtain_auth_token),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
