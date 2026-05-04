from django.contrib import admin
from .models import RacelyScore, SeasonScore


@admin.register(RacelyScore)
class RacelyScoreAdmin(admin.ModelAdmin):
    list_display = ["user", "paddock", "race", "position_points", "pole_points", "fastest_lap_points", "quiz_points", "quiz_pending", "total"]
    list_filter = ["paddock", "race", "quiz_pending"]
    search_fields = ["user__email"]
    readonly_fields = ["total"]

    def total(self, obj):
        return obj.total
    total.short_description = "Total"


@admin.register(SeasonScore)
class SeasonScoreAdmin(admin.ModelAdmin):
    list_display = ["user", "paddock", "race", "driver_standing_points", "constructor_standing_points", "combined"]
    list_filter = ["paddock", "race"]
    search_fields = ["user__email"]
    readonly_fields = ["combined"]

    def combined(self, obj):
        return obj.combined
    combined.short_description = "Combined"
