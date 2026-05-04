from django.urls import path
from . import views

urlpatterns = [
    path("racely/current/", views.racely_current),
    path("racely/submit/", views.submit_racely),
]
