from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import (
    Constructor, ConstructorChampionshipStanding, Driver,
    DriverChampionshipStanding, Race, Season,
)
from .serializers import (
    ConstructorSerializer, ConstructorStandingSerializer,
    DriverSerializer, DriverStandingSerializer,
    RaceDetailSerializer, RaceListSerializer, SeasonSerializer,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def active_season(request):
    season = Season.objects.filter(is_active=True).first()
    if not season:
        return Response({"detail": "No active season."}, status=404)
    return Response(SeasonSerializer(season).data)


class RaceListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = RaceListSerializer

    def get_queryset(self):
        year = self.kwargs.get("year") or _active_year()
        return Race.objects.filter(season__year=year).select_related("circuit").order_by("round")


class RaceDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = RaceDetailSerializer

    def get_queryset(self):
        year = self.kwargs.get("year") or _active_year()
        return Race.objects.filter(season__year=year).select_related("circuit").prefetch_related(
            "entries__driver__constructor",
            "entries__constructor",
        )


class DriverListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = DriverSerializer

    def get_queryset(self):
        qs = Driver.objects.select_related("constructor")
        on_grid = self.request.query_params.get("on_grid")
        if on_grid == "true":
            qs = qs.filter(is_on_grid=True)
        return qs.order_by("last_name")


class ConstructorListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ConstructorSerializer
    queryset = Constructor.objects.filter(is_on_grid=True).order_by("name")


@api_view(["GET"])
@permission_classes([AllowAny])
def driver_standings(request, year=None):
    year = year or _active_year()
    race = (
        Race.objects.filter(season__year=year, is_complete=True)
        .order_by("-round")
        .first()
    )
    if not race:
        return Response([])
    standings = (
        DriverChampionshipStanding.objects.filter(race=race)
        .select_related("driver__constructor")
        .order_by("position")
    )
    return Response(DriverStandingSerializer(standings, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def constructor_standings(request, year=None):
    year = year or _active_year()
    race = (
        Race.objects.filter(season__year=year, is_complete=True)
        .order_by("-round")
        .first()
    )
    if not race:
        return Response([])
    standings = (
        ConstructorChampionshipStanding.objects.filter(race=race)
        .select_related("constructor")
        .order_by("position")
    )
    return Response(ConstructorStandingSerializer(standings, many=True).data)


def _active_year():
    season = Season.objects.filter(is_active=True).first()
    return season.year if season else 2025
