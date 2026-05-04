from django.contrib import admin
from .models import (
    RacelyPrediction, RacelyPredictionEntry,
    PolePrediction, FastestLapPrediction,
    DriverStandingPrediction, DriverStandingPredictionEntry,
    ConstructorStandingPrediction, ConstructorStandingPredictionEntry,
)


class RacelyPredictionEntryInline(admin.TabularInline):
    model = RacelyPredictionEntry
    extra = 0
    ordering = ["position"]


@admin.register(RacelyPrediction)
class RacelyPredictionAdmin(admin.ModelAdmin):
    list_display = ["user", "race", "submitted_at", "is_rolled_over"]
    list_filter = ["race", "is_rolled_over"]
    search_fields = ["user__email"]
    readonly_fields = ["submitted_at"]
    inlines = [RacelyPredictionEntryInline]


@admin.register(PolePrediction)
class PolePredictionAdmin(admin.ModelAdmin):
    list_display = ["user", "race", "driver", "submitted_at", "is_rolled_over"]
    list_filter = ["race", "is_rolled_over"]
    search_fields = ["user__email"]
    readonly_fields = ["submitted_at"]


@admin.register(FastestLapPrediction)
class FastestLapPredictionAdmin(admin.ModelAdmin):
    list_display = ["user", "race", "driver", "submitted_at", "is_rolled_over"]
    list_filter = ["race", "is_rolled_over"]
    search_fields = ["user__email"]
    readonly_fields = ["submitted_at"]


class DriverStandingPredictionEntryInline(admin.TabularInline):
    model = DriverStandingPredictionEntry
    extra = 0
    ordering = ["position"]


@admin.register(DriverStandingPrediction)
class DriverStandingPredictionAdmin(admin.ModelAdmin):
    list_display = ["user", "paddock", "submitted_at", "is_locked"]
    list_editable = ["is_locked"]
    list_filter = ["paddock", "is_locked"]
    search_fields = ["user__email"]
    readonly_fields = ["submitted_at"]
    inlines = [DriverStandingPredictionEntryInline]


class ConstructorStandingPredictionEntryInline(admin.TabularInline):
    model = ConstructorStandingPredictionEntry
    extra = 0
    ordering = ["position"]


@admin.register(ConstructorStandingPrediction)
class ConstructorStandingPredictionAdmin(admin.ModelAdmin):
    list_display = ["user", "paddock", "submitted_at", "is_locked"]
    list_editable = ["is_locked"]
    list_filter = ["paddock", "is_locked"]
    search_fields = ["user__email"]
    readonly_fields = ["submitted_at"]
    inlines = [ConstructorStandingPredictionEntryInline]
