from django.urls import path
from . import views

urlpatterns = [
    path("current/", views.live_questions),
    path("answer/<int:question_id>/", views.submit_answer),
]
