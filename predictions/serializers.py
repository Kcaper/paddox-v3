from rest_framework import serializers

from f1data.serializers import DriverSerializer, RaceListSerializer
from .models import (
    RacelyPrediction, RacelyPredictionEntry,
    PolePrediction, FastestLapPrediction,
)


class RacelyPredictionEntrySerializer(serializers.ModelSerializer):
    driver = DriverSerializer(read_only=True)

    class Meta:
        model = RacelyPredictionEntry
        fields = ["position", "driver"]


class RacelyPredictionSerializer(serializers.ModelSerializer):
    entries = RacelyPredictionEntrySerializer(many=True, read_only=True)

    class Meta:
        model = RacelyPrediction
        fields = ["id", "race_id", "entries", "submitted_at", "is_rolled_over"]


class SubmitRacelySerializer(serializers.Serializer):
    """
    driver_positions: ordered list of driver IDs, index 0 = P1
    pole_driver_id: driver ID predicted for pole
    fastest_lap_driver_id: driver ID predicted for fastest lap
    """
    driver_positions = serializers.ListField(
        child=serializers.IntegerField(), min_length=1, max_length=20
    )
    pole_driver_id = serializers.IntegerField(required=False, allow_null=True)
    fastest_lap_driver_id = serializers.IntegerField(required=False, allow_null=True)
