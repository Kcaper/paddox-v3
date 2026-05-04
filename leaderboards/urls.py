from django.urls import path
from . import views

urlpatterns = [
    path("<int:paddock_id>/racely/", views.racely_leaderboard),
    path("<int:paddock_id>/racely/<int:race_id>/", views.racely_leaderboard_race),
    path("<int:paddock_id>/season/", views.season_leaderboard),
    path("me/", views.my_scores),
]
