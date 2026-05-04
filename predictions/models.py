from django.conf import settings
from django.db import models
from f1data.models import Driver, Constructor, Race
from paddocks.models import Paddock


class RacelyPrediction(models.Model):
    """One per user per race — covers all their paddocks."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="racely_predictions")
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="racely_predictions")
    submitted_at = models.DateTimeField(auto_now=True)
    is_rolled_over = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "race")

    def __str__(self):
        return f"{self.user} — {self.race}"


class RacelyPredictionEntry(models.Model):
    """Individual driver position in a Racely prediction."""
    prediction = models.ForeignKey(RacelyPrediction, on_delete=models.CASCADE, related_name="entries")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="racely_entries")
    position = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = [("prediction", "driver"), ("prediction", "position")]
        ordering = ["position"]


class PolePrediction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pole_predictions")
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="pole_predictions")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="pole_predictions")
    submitted_at = models.DateTimeField(auto_now=True)
    is_rolled_over = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "race")


class FastestLapPrediction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="fastest_lap_predictions")
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="fastest_lap_predictions")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="fastest_lap_predictions")
    submitted_at = models.DateTimeField(auto_now=True)
    is_rolled_over = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "race")


class DriverStandingPrediction(models.Model):
    """Pre-season driver championship order prediction — per user per paddock."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="driver_standing_predictions")
    paddock = models.ForeignKey(Paddock, on_delete=models.CASCADE, related_name="driver_standing_predictions")
    submitted_at = models.DateTimeField(auto_now=True)
    is_locked = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "paddock")

    def __str__(self):
        return f"{self.user} — {self.paddock} driver standing"


class DriverStandingPredictionEntry(models.Model):
    prediction = models.ForeignKey(DriverStandingPrediction, on_delete=models.CASCADE, related_name="entries")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="standing_prediction_entries")
    position = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = [("prediction", "driver"), ("prediction", "position")]
        ordering = ["position"]


class ConstructorStandingPrediction(models.Model):
    """Pre-season constructor championship order prediction — per user per paddock."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="constructor_standing_predictions")
    paddock = models.ForeignKey(Paddock, on_delete=models.CASCADE, related_name="constructor_standing_predictions")
    submitted_at = models.DateTimeField(auto_now=True)
    is_locked = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "paddock")

    def __str__(self):
        return f"{self.user} — {self.paddock} constructor standing"


class ConstructorStandingPredictionEntry(models.Model):
    prediction = models.ForeignKey(ConstructorStandingPrediction, on_delete=models.CASCADE, related_name="entries")
    constructor = models.ForeignKey(Constructor, on_delete=models.CASCADE, related_name="standing_prediction_entries")
    position = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = [("prediction", "constructor"), ("prediction", "position")]
        ordering = ["position"]
