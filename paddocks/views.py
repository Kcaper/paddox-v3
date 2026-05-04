from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from f1data.models import Season
from .models import Paddock, PaddockMembership, PaddockRules
from .serializers import CreatePaddockSerializer, PaddockDetailSerializer, PaddockListSerializer

User = get_user_model()


@api_view(["GET"])
def my_paddocks(request):
    paddock_ids = request.user.paddock_memberships.values_list("paddock_id", flat=True)
    paddocks = Paddock.objects.filter(id__in=paddock_ids).prefetch_related("memberships")
    return Response(PaddockListSerializer(paddocks, many=True, context={"request": request}).data)


@api_view(["GET"])
def paddock_detail(request, pk):
    try:
        membership = request.user.paddock_memberships.select_related("paddock__rules").get(paddock_id=pk)
    except PaddockMembership.DoesNotExist:
        return Response({"detail": "Not found."}, status=404)
    paddock = membership.paddock
    return Response(PaddockDetailSerializer(paddock, context={"request": request}).data)


@api_view(["PATCH", "DELETE"])
def manage_member(request, pk, user_id):
    """Owner/admin can change roles or remove members."""
    try:
        my_membership = request.user.paddock_memberships.get(paddock_id=pk)
    except PaddockMembership.DoesNotExist:
        return Response({"detail": "Not found."}, status=404)

    if my_membership.role not in ("owner", "admin"):
        return Response({"detail": "Permission denied."}, status=403)

    if user_id == request.user.id:
        return Response({"detail": "Cannot modify your own membership this way."}, status=400)

    try:
        target = PaddockMembership.objects.get(paddock_id=pk, user_id=user_id)
    except PaddockMembership.DoesNotExist:
        return Response({"detail": "Member not found."}, status=404)

    if target.role == "owner":
        return Response({"detail": "Cannot modify the owner."}, status=400)

    paddock = Paddock.objects.get(pk=pk)

    if request.method == "DELETE":
        if my_membership.role == "admin" and target.role == "admin":
            return Response({"detail": "Admins cannot remove other admins."}, status=403)
        target.delete()
        return Response(PaddockDetailSerializer(paddock, context={"request": request}).data)

    new_role = request.data.get("role")
    if new_role not in ("admin", "member"):
        return Response({"detail": "role must be 'admin' or 'member'."}, status=400)

    if my_membership.role == "admin" and new_role == "admin":
        return Response({"detail": "Admins cannot promote others to admin."}, status=403)

    target.role = new_role
    target.save(update_fields=["role"])
    return Response(PaddockDetailSerializer(paddock, context={"request": request}).data)


@api_view(["POST"])
def create_paddock(request):
    serializer = CreatePaddockSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    season = Season.objects.filter(is_active=True).first()
    if not season:
        return Response({"detail": "No active season."}, status=400)

    data = serializer.validated_data

    rules = PaddockRules.objects.create(
        name=f"{data['name']} Rules",
        season=season,
        racely_deadline_session=data["racely_deadline_session"],
        racely_scoring_positions=data["racely_scoring_positions"],
        racely_start_round=1,
        driver_standing_deadline_session="Q1",
        driver_standing_start_round=1,
        constructor_standing_deadline_session="Q1",
        constructor_standing_start_round=1,
    )

    paddock = Paddock.objects.create(
        season=season,
        name=data["name"],
        rules=rules,
        is_public=data["is_public"],
        max_players=data["max_players"],
        created_by=request.user,
    )

    PaddockMembership.objects.create(paddock=paddock, user=request.user, role="owner")

    return Response(
        PaddockDetailSerializer(paddock, context={"request": request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def paddock_predictions(request, pk):
    """All members' Racely predictions for the current/latest locked race (deadline must have passed)."""
    try:
        PaddockMembership.objects.get(paddock_id=pk, user=request.user)
    except PaddockMembership.DoesNotExist:
        return Response({"detail": "Not found."}, status=404)

    from datetime import datetime, timezone as tz
    from f1data.models import Race, Season
    from predictions.models import RacelyPrediction, PolePrediction, FastestLapPrediction

    now = datetime.now(tz.utc)
    paddock = Paddock.objects.get(pk=pk)
    season = paddock.season

    # Find the most recent race whose qualifying deadline has passed
    race = (
        Race.objects.filter(season=season, quali_at__lte=now)
        .order_by("-round")
        .first()
    )
    if not race:
        return Response({"race": None, "predictions": []})

    members = list(paddock.memberships.select_related("user").order_by("joined_at"))

    result = []
    for membership in members:
        user = membership.user
        pred = (
            RacelyPrediction.objects.filter(user=user, race=race)
            .prefetch_related("entries__driver__constructor")
            .first()
        )
        pole = PolePrediction.objects.filter(user=user, race=race).select_related("driver").first()
        fl = FastestLapPrediction.objects.filter(user=user, race=race).select_related("driver").first()

        result.append({
            "user": {"id": user.id, "username": user.username, "avatar_url": user.avatar_url},
            "is_rolled_over": pred.is_rolled_over if pred else None,
            "entries": [
                {"position": e.position, "driver": {
                    "id": e.driver.id,
                    "first_name": e.driver.first_name,
                    "last_name": e.driver.last_name,
                    "abbreviation": e.driver.abbreviation,
                    "constructor": {"name": e.driver.constructor.name} if e.driver.constructor else None,
                }}
                for e in pred.entries.order_by("position")
            ] if pred else [],
            "pole": {"first_name": pole.driver.first_name, "last_name": pole.driver.last_name, "abbreviation": pole.driver.abbreviation} if pole else None,
            "fastest_lap": {"first_name": fl.driver.first_name, "last_name": fl.driver.last_name, "abbreviation": fl.driver.abbreviation} if fl else None,
        })

    return Response({
        "race": {"id": race.id, "name": race.name, "round": race.round},
        "predictions": result,
    })


@api_view(["POST"])
def join_paddock(request):
    code = (request.data.get("join_code") or "").strip().upper()
    if not code:
        return Response({"detail": "join_code is required."}, status=400)

    try:
        paddock = Paddock.objects.get(join_code=code, is_active=True)
    except Paddock.DoesNotExist:
        return Response({"detail": "Invalid join code."}, status=404)

    if paddock.memberships.filter(user=request.user).exists():
        return Response({"detail": "Already a member."}, status=400)

    if paddock.memberships.count() >= paddock.max_players:
        return Response({"detail": "Paddock is full."}, status=400)

    PaddockMembership.objects.create(paddock=paddock, user=request.user, role="member")

    # Notify owner/admins
    from users.notify import notify_many
    admins = [
        m.user for m in paddock.memberships.filter(role__in=("owner", "admin")).select_related("user")
        if m.user != request.user
    ]
    notify_many(admins, f"{request.user.username} joined {paddock.name}", type="paddock_joined")

    return Response(PaddockDetailSerializer(paddock, context={"request": request}).data)
