import random
import string
from django.conf import settings
from django.db import models
from f1data.models import Constructor, Driver, Season


def generate_join_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


class PaddockRules(models.Model):
    DEADLINE_SESSION_CHOICES = [
        ("Q1", "Q1 / Qualifying"),
        ("SPRINT", "Sprint Race"),
        ("FP1", "FP1"),
    ]

    name = models.CharField(max_length=25)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="paddock_rules")

    # Racely
    racely_deadline_session = models.CharField(max_length=10, choices=DEADLINE_SESSION_CHOICES, default="Q1")
    racely_start_round = models.PositiveSmallIntegerField(default=1)
    racely_scoring_positions = models.PositiveSmallIntegerField(default=10)

    # Driver standing prediction
    driver_standing_deadline_session = models.CharField(max_length=10, choices=DEADLINE_SESSION_CHOICES, default="Q1")
    driver_standing_start_round = models.PositiveSmallIntegerField(default=1)

    # Constructor standing prediction
    constructor_standing_deadline_session = models.CharField(max_length=10, choices=DEADLINE_SESSION_CHOICES, default="Q1")
    constructor_standing_start_round = models.PositiveSmallIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.season.year})"


class Paddock(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="paddocks")
    name = models.CharField(max_length=30)
    rules = models.OneToOneField(PaddockRules, on_delete=models.CASCADE, related_name="paddock")
    join_code = models.CharField(max_length=6, unique=True, default=generate_join_code)
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_world_paddock = models.BooleanField(default=False)
    max_players = models.PositiveIntegerField(default=20)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_paddocks"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class PaddockMembership(models.Model):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    paddock = models.ForeignKey(Paddock, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="paddock_memberships"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("paddock", "user")

    def __str__(self):
        return f"{self.user} — {self.paddock} ({self.role})"


class PaddockPool(models.Model):
    """Season-level Racely prediction pool for a paddock."""
    paddock = models.ForeignKey(Paddock, on_delete=models.CASCADE, related_name="pool_entries")
    constructor = models.ForeignKey(
        Constructor, null=True, blank=True, on_delete=models.CASCADE, related_name="pool_entries"
    )
    driver = models.ForeignKey(
        Driver, null=True, blank=True, on_delete=models.CASCADE, related_name="pool_entries"
    )

    class Meta:
        unique_together = [("paddock", "constructor"), ("paddock", "driver")]

    def __str__(self):
        target = self.constructor or self.driver
        return f"{self.paddock} — {target}"


class PaddockDeadlineReopening(models.Model):
    """Audit trail for admin-reopened prediction deadlines."""
    DEADLINE_TYPE_CHOICES = [
        ("driver_standing", "Driver Standing"),
        ("constructor_standing", "Constructor Standing"),
    ]

    paddock = models.ForeignKey(Paddock, on_delete=models.CASCADE, related_name="deadline_reopenings")
    reopened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="deadline_reopenings"
    )
    deadline_type = models.CharField(max_length=25, choices=DEADLINE_TYPE_CHOICES)
    reopened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.paddock} — {self.deadline_type} reopened by {self.reopened_by}"


class PredictionSnapshot(models.Model):
    """Records prediction state before and after a deadline reopening."""
    reopening = models.ForeignKey(PaddockDeadlineReopening, on_delete=models.CASCADE, related_name="snapshots")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prediction_snapshots")
    snapshot_type = models.CharField(max_length=10, choices=[("before", "Before"), ("after", "After")])
    prediction_data = models.JSONField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reopening} — {self.user} ({self.snapshot_type})"
