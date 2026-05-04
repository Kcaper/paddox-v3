from datetime import datetime, timezone

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from f1data.models import Driver, Race, Season
from f1data.serializers import DriverSerializer, RaceListSerializer
from paddocks.models import Paddock, PaddockPool
from .models import (
    FastestLapPrediction, PolePrediction,
    RacelyPrediction, RacelyPredictionEntry,
)
from .serializers import RacelyPredictionSerializer, SubmitRacelySerializer


def _current_race():
    """Next race where quali hasn't started yet, or the most recent completed race."""
    now = datetime.now(timezone.utc)
    season = Season.objects.filter(is_active=True).first()
    if not season:
        return None
    upcoming = (
        Race.objects.filter(season=season, quali_at__gt=now)
        .order_by("round")
        .first()
    )
    if upcoming:
        return upcoming
    return Race.objects.filter(season=season).order_by("-round").first()


def _available_drivers(race, paddock):
    """Drivers available for prediction in this paddock. Falls back to all on-grid drivers."""
    pool_driver_ids = PaddockPool.objects.filter(
        paddock=paddock, driver__isnull=False
    ).values_list("driver_id", flat=True)

    pool_constructor_ids = PaddockPool.objects.filter(
        paddock=paddock, constructor__isnull=False
    ).values_list("constructor_id", flat=True)

    if pool_driver_ids or pool_constructor_ids:
        return Driver.objects.filter(
            is_on_grid=True
        ).filter(
            id__in=list(pool_driver_ids)
        ) | Driver.objects.filter(
            is_on_grid=True, constructor_id__in=list(pool_constructor_ids)
        ).distinct().select_related("constructor").order_by("last_name")

    return Driver.objects.filter(is_on_grid=True).select_related("constructor").order_by("last_name")


@api_view(["GET"])
def racely_current(request):
    """
    Returns the current/next race info, the user's existing prediction (if any),
    available drivers, and whether the deadline has passed.
    """
    race = _current_race()
    if not race:
        return Response({"detail": "No active race found."}, status=404)

    now = datetime.now(timezone.utc)
    deadline_passed = race.quali_at and race.quali_at <= now

    prediction = RacelyPrediction.objects.filter(
        user=request.user, race=race
    ).prefetch_related("entries__driver__constructor").first()

    pole_pred = PolePrediction.objects.filter(user=request.user, race=race).select_related("driver").first()
    fl_pred = FastestLapPrediction.objects.filter(user=request.user, race=race).select_related("driver").first()

    # Use world paddock for available drivers (widest pool)
    world_paddock = Paddock.objects.filter(is_world_paddock=True, is_active=True).first()
    available = _available_drivers(race, world_paddock) if world_paddock else Driver.objects.filter(is_on_grid=True).select_related("constructor")

    return Response({
        "race": RaceListSerializer(race).data,
        "deadline_passed": deadline_passed,
        "prediction": RacelyPredictionSerializer(prediction).data if prediction else None,
        "pole_prediction": {"driver": DriverSerializer(pole_pred.driver).data} if pole_pred else None,
        "fastest_lap_prediction": {"driver": DriverSerializer(fl_pred.driver).data} if fl_pred else None,
        "available_drivers": DriverSerializer(available, many=True).data,
    })


@api_view(["POST"])
def submit_racely(request):
    """Submit or update the racely prediction for the current race."""
    race = _current_race()
    if not race:
        return Response({"detail": "No active race found."}, status=404)

    now = datetime.now(timezone.utc)
    if race.quali_at and race.quali_at <= now:
        return Response({"detail": "Prediction deadline has passed."}, status=400)

    serializer = SubmitRacelySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    driver_positions = data["driver_positions"]  # ordered list of driver IDs

    # Validate drivers exist
    drivers = Driver.objects.filter(id__in=driver_positions)
    driver_map = {d.id: d for d in drivers}
    for driver_id in driver_positions:
        if driver_id not in driver_map:
            return Response({"detail": f"Driver {driver_id} not found."}, status=400)

    # Create/update the prediction
    prediction, _ = RacelyPrediction.objects.update_or_create(
        user=request.user,
        race=race,
        defaults={"is_rolled_over": False},
    )

    # Replace entries
    prediction.entries.all().delete()
    RacelyPredictionEntry.objects.bulk_create([
        RacelyPredictionEntry(prediction=prediction, driver_id=driver_id, position=idx + 1)
        for idx, driver_id in enumerate(driver_positions)
    ])

    # Pole prediction
    pole_id = data.get("pole_driver_id")
    if pole_id is not None:
        PolePrediction.objects.update_or_create(
            user=request.user, race=race,
            defaults={"driver_id": pole_id, "is_rolled_over": False},
        )

    # Fastest lap prediction
    fl_id = data.get("fastest_lap_driver_id")
    if fl_id is not None:
        FastestLapPrediction.objects.update_or_create(
            user=request.user, race=race,
            defaults={"driver_id": fl_id, "is_rolled_over": False},
        )

    prediction.refresh_from_db()
    return Response(RacelyPredictionSerializer(
        RacelyPrediction.objects.prefetch_related("entries__driver__constructor").get(pk=prediction.pk)
    ).data)
