from django.db import models


class Constructor(models.Model):
    ref = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100, blank=True)
    is_on_grid = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Driver(models.Model):
    ref = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    number = models.PositiveSmallIntegerField(null=True, blank=True)
    abbreviation = models.CharField(max_length=3, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    constructor = models.ForeignKey(
        Constructor, null=True, blank=True, on_delete=models.SET_NULL, related_name="drivers"
    )
    is_on_grid = models.BooleanField(default=True)
    is_reserve = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Circuit(models.Model):
    ref = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Season(models.Model):
    year = models.PositiveSmallIntegerField(unique=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return str(self.year)


class Race(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="races")
    round = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=200)
    circuit = models.ForeignKey(Circuit, on_delete=models.CASCADE, related_name="races")
    is_sprint_weekend = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)

    # Session datetimes (UTC)
    fp1_at = models.DateTimeField(null=True, blank=True)
    fp2_at = models.DateTimeField(null=True, blank=True)
    fp3_at = models.DateTimeField(null=True, blank=True)
    sprint_quali_at = models.DateTimeField(null=True, blank=True)
    sprint_at = models.DateTimeField(null=True, blank=True)
    quali_at = models.DateTimeField(null=True, blank=True)
    race_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("season", "round")
        ordering = ["round"]

    def __str__(self):
        return f"{self.season.year} R{self.round} — {self.name}"


class RaceEntry(models.Model):
    """Confirmed driver entries per race, resolved after qualifying."""
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="entries")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="race_entries")
    constructor = models.ForeignKey(Constructor, on_delete=models.CASCADE, related_name="race_entries")
    grid_position = models.PositiveSmallIntegerField(null=True, blank=True)
    finish_position = models.PositiveSmallIntegerField(null=True, blank=True)
    is_substitute = models.BooleanField(default=False)
    substituted_for = models.ForeignKey(
        Driver, null=True, blank=True, on_delete=models.SET_NULL, related_name="substituted_entries"
    )
    is_fastest_lap = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("race", "driver")

    def __str__(self):
        return f"{self.race} — {self.driver}"


class DriverChampionshipStanding(models.Model):
    """Real-world driver championship standings after each race."""
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="driver_standings")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="championship_standings")
    position = models.PositiveSmallIntegerField()
    points = models.FloatField(default=0)

    class Meta:
        unique_together = ("race", "driver")
        ordering = ["position"]


class ConstructorChampionshipStanding(models.Model):
    """Real-world constructor championship standings after each race."""
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="constructor_standings")
    constructor = models.ForeignKey(Constructor, on_delete=models.CASCADE, related_name="championship_standings")
    position = models.PositiveSmallIntegerField()
    points = models.FloatField(default=0)

    class Meta:
        unique_together = ("race", "constructor")
        ordering = ["position"]
