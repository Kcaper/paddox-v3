from django.urls import path
from . import views

urlpatterns = [
    path("", views.my_paddocks),
    path("create/", views.create_paddock),
    path("join/", views.join_paddock),
    path("<int:pk>/", views.paddock_detail),
    path("<int:pk>/members/<int:user_id>/", views.manage_member),
]
