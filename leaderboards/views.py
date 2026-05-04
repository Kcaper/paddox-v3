from django.db.models import Sum
from rest_framework.decorators import api_view
from rest_framework.response import Response

from f1data.models import Race, Season
from leaderboards.models import RacelyScore
from paddocks.models import Paddock, PaddockMembership


def _assert_member(user, paddock_id):
    return PaddockMembership.objects.filter(user=user, paddock_id=paddock_id).exists()


@api_view(["GET"])
def racely_leaderboard(request, paddock_id):
    if not _assert_member(request.user, paddock_id):
        return Response({"detail": "Not a member."}, status=403)

    try:
        paddock = Paddock.objects.get(pk=paddock_id)
    except Paddock.DoesNotExist:
        return Response({"detail": "Not found."}, status=404)

    # Aggregate racely points per user in this paddock (all races)
    scores = (
        RacelyScore.objects.filter(paddock=paddock)
        .values("user__id", "user__username", "user__avatar_url")
        .annotate(
            total_position=Sum("position_points"),
            total_pole=Sum("pole_points"),
            total_fl=Sum("fastest_lap_points"),
            total_quiz=Sum("quiz_points"),
        )
        .order_by("-total_position", "-total_pole", "-total_fl")
    )

    board = []
    for rank, row in enumerate(scores, 1):
        total = (
            (row["total_position"] or 0)
            + (row["total_pole"] or 0)
            + (row["total_fl"] or 0)
            + (row["total_quiz"] or 0)
        )
        board.append({
            "rank": rank,
            "user": {
                "id": row["user__id"],
                "username": row["user__username"],
                "avatar_url": row["user__avatar_url"],
            },
            "position_points": row["total_position"] or 0,
            "pole_points": row["total_pole"] or 0,
            "fastest_lap_points": row["total_fl"] or 0,
            "quiz_points": row["total_quiz"] or 0,
            "total": total,
        })

    # Sort properly by total
    board.sort(key=lambda x: -x["total"])
    for rank, row in enumerate(board, 1):
        row["rank"] = rank

    return Response({"paddock": paddock.name, "leaderboard": board})


@api_view(["GET"])
def racely_leaderboard_race(request, paddock_id, race_id):
    """Per-race breakdown for a paddock."""
    if not _assert_member(request.user, paddock_id):
        return Response({"detail": "Not a member."}, status=403)

    scores = RacelyScore.objects.filter(
        paddock_id=paddock_id, race_id=race_id
    ).select_related("user").order_by("-position_points", "-pole_points")

    board = [
        {
            "rank": rank,
            "user": {"id": s.user.id, "username": s.user.username},
            "position_points": s.position_points,
            "pole_points": s.pole_points,
            "fastest_lap_points": s.fastest_lap_points,
            "quiz_points": s.quiz_points,
            "quiz_pending": s.quiz_pending,
            "total": s.total,
        }
        for rank, s in enumerate(scores, 1)
    ]
    board.sort(key=lambda x: -x["total"])
    for rank, row in enumerate(board, 1):
        row["rank"] = rank

    return Response({"leaderboard": board})
