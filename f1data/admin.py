from django.contrib import admin
from .models import Constructor, Driver, Circuit, Season, Race, RaceEntry, DriverChampionshipStanding, ConstructorChampionshipStanding


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ["year", "is_active"]
    list_editable = ["is_active"]


@admin.register(Constructor)
class ConstructorAdmin(admin.ModelAdmin):
    list_display = ["name", "nationality", "is_on_grid"]
    list_editable = ["is_on_grid"]
    search_fields = ["name", "ref"]


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name", "number", "abbreviation", "constructor", "is_on_grid", "is_reserve"]
    list_editable = ["is_on_grid", "is_reserve"]
    list_filter = ["constructor", "is_on_grid", "is_reserve"]
    search_fields = ["first_name", "last_name", "abbreviation", "ref"]


@admin.register(Circuit)
class CircuitAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "city"]
    search_fields = ["name", "country"]


@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display = ["season", "round", "name", "circuit", "is_sprint_weekend", "is_complete", "quali_at", "race_at"]
    list_editable = ["is_complete"]
    list_filter = ["season", "is_sprint_weekend", "is_complete"]
    search_fields = ["name"]


@admin.register(RaceEntry)
class RaceEntryAdmin(admin.ModelAdmin):
    list_display = ["race", "driver", "constructor", "grid_position", "finish_position", "is_fastest_lap", "is_substitute", "substituted_for", "is_confirmed"]
    list_editable = ["finish_position", "is_fastest_lap", "is_confirmed"]
    list_filter = ["race", "is_substitute", "is_confirmed"]
    search_fields = ["driver__last_name"]
    autocomplete_fields = ["driver", "constructor", "substituted_for"]


@admin.register(DriverChampionshipStanding)
class DriverChampionshipStandingAdmin(admin.ModelAdmin):
    list_display = ["race", "position", "driver", "points"]
    list_filter = ["race"]


@admin.register(ConstructorChampionshipStanding)
class ConstructorChampionshipStandingAdmin(admin.ModelAdmin):
    list_display = ["race", "position", "constructor", "points"]
    list_filter = ["race"]
