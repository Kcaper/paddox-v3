from rest_framework import serializers

from .models import (
    Circuit, Constructor, ConstructorChampionshipStanding, Driver,
    DriverChampionshipStanding, Race, RaceEntry, Season,
)


class ConstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constructor
        fields = ["id", "ref", "name", "nationality", "is_on_grid"]


class DriverSerializer(serializers.ModelSerializer):
    constructor = ConstructorSerializer(read_only=True)

    class Meta:
        model = Driver
        fields = [
            "id", "ref", "first_name", "last_name", "number",
            "abbreviation", "nationality", "constructor",
            "is_on_grid", "is_reserve",
        ]


class CircuitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circuit
        fields = ["id", "ref", "name", "country", "city"]


class RaceListSerializer(serializers.ModelSerializer):
    circuit = CircuitSerializer(read_only=True)

    class Meta:
        model = Race
        fields = [
            "id", "round", "name", "circuit",
            "is_sprint_weekend", "is_complete",
            "fp1_at", "fp2_at", "fp3_at",
            "sprint_quali_at", "sprint_at",
            "quali_at", "race_at",
        ]


class RaceEntrySerializer(serializers.ModelSerializer):
    driver = DriverSerializer(read_only=True)
    constructor = ConstructorSerializer(read_only=True)

    class Meta:
        model = RaceEntry
        fields = [
            "id", "driver", "constructor",
            "grid_position", "finish_position",
            "is_fastest_lap", "is_substitute", "is_confirmed",
        ]


class RaceDetailSerializer(RaceListSerializer):
    entries = RaceEntrySerializer(many=True, read_only=True)

    class Meta(RaceListSerializer.Meta):
        fields = RaceListSerializer.Meta.fields + ["entries"]


class DriverStandingSerializer(serializers.ModelSerializer):
    driver = DriverSerializer(read_only=True)

    class Meta:
        model = DriverChampionshipStanding
        fields = ["driver", "position", "points"]


class ConstructorStandingSerializer(serializers.ModelSerializer):
    constructor = ConstructorSerializer(read_only=True)

    class Meta:
        model = ConstructorChampionshipStanding
        fields = ["constructor", "position", "points"]


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ["id", "year", "is_active"]
