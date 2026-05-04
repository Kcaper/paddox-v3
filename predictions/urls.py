from django.urls import path
from . import views

urlpatterns = [
    path("racely/current/", views.racely_current),
    path("racely/submit/", views.submit_racely),
    path("season/<int:paddock_id>/", views.season_prediction),
    path("season/<int:paddock_id>/drivers/", views.submit_driver_standing),
    path("season/<int:paddock_id>/constructors/", views.submit_constructor_standing),
]
