from django.contrib.auth.models import AbstractUser
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [
        ("race_scored", "Race Scored"),
        ("quiz_live", "Quiz Questions Live"),
        ("quiz_confirmed", "Quiz Answers Confirmed"),
        ("paddock_joined", "Someone Joined Your Paddock"),
        ("deadline_soon", "Prediction Deadline Soon"),
        ("general", "General"),
    ]

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="general")
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.title}"


class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar_url = models.URLField(blank=True, default="")
    is_super_admin = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
