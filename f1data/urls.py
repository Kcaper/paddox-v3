from django.urls import path

from . import views

urlpatterns = [
    path("season/", views.active_season),
    path("races/", views.RaceListView.as_view()),
    path("races/<int:pk>/", views.RaceDetailView.as_view()),
    path("drivers/", views.DriverListView.as_view()),
    path("constructors/", views.ConstructorListView.as_view()),
    path("standings/drivers/", views.driver_standings),
    path("standings/constructors/", views.constructor_standings),
]
