from django.conf import settings
from django.db import models
from f1data.models import Race
from paddocks.models import Paddock


class RacelyScore(models.Model):
    """Racely points earned by a user for a specific race in a specific paddock."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="racely_scores")
    paddock = models.ForeignKey(Paddock, on_delete=models.CASCADE, related_name="racely_scores")
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="racely_scores")

    position_points = models.FloatField(default=0)
    pole_points = models.FloatField(default=0)
    fastest_lap_points = models.FloatField(default=0)
    quiz_points = models.FloatField(default=0)
    quiz_pending = models.BooleanField(default=True)

    @property
    def total(self):
        return self.position_points + self.pole_points + self.fastest_lap_points + self.quiz_points

    class Meta:
        unique_together = ("user", "paddock", "race")

    def __str__(self):
        return f"{self.user} — {self.paddock} — {self.race} racely"


class SeasonScore(models.Model):
    """Driver + constructor standing scores per user per paddock, recalculated after each race."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="season_scores")
    paddock = models.ForeignKey(Paddock, on_delete=models.CASCADE, related_name="season_scores")
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="season_scores")

    driver_standing_points = models.FloatField(default=0)
    constructor_standing_points = models.FloatField(default=0)

    @property
    def combined(self):
        return self.driver_standing_points + self.constructor_standing_points

    class Meta:
        unique_together = ("user", "paddock", "race")

    def __str__(self):
        return f"{self.user} — {self.paddock} — {self.race} season"
