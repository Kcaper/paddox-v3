from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/", include("allauth.urls")),
    path("api/users/", include("users.urls")),
    path("api/paddocks/", include("paddocks.urls")),
    path("api/predictions/", include("predictions.urls")),
    path("api/leaderboards/", include("leaderboards.urls")),
    path("api/quiz/", include("quiz.urls")),
    path("api/f1/", include("f1data.urls")),
]
