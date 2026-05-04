from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from f1data.models import Season
from .models import Paddock, PaddockMembership, PaddockRules
from .serializers import CreatePaddockSerializer, PaddockDetailSerializer, PaddockListSerializer


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
    paddock.memberships  # already prefetched via select_related won't work here, but fine for detail
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
