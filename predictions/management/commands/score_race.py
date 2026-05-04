from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from f1data.models import Race, RaceEntry
from leaderboards.models import RacelyScore
from paddocks.models import Paddock, PaddockMembership, PaddockPool
from predictions.models import (
    FastestLapPrediction, PolePrediction,
    RacelyPrediction, RacelyPredictionEntry,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Calculate and save Racely scores for a completed race"

    def add_arguments(self, parser):
        parser.add_argument("race_id", type=int, help="Race DB ID to score")

    def handle(self, *args, **options):
        try:
            race = Race.objects.get(pk=options["race_id"])
        except Race.DoesNotExist:
            raise CommandError(f"Race {options['race_id']} not found")

        if not race.is_complete:
            raise CommandError(f"{race} is not marked complete — mark it first")

        # Pre-fetch race results
        entries = {e.driver_id: e for e in RaceEntry.objects.filter(race=race, is_confirmed=True)}
        if not entries:
            raise CommandError(f"No confirmed RaceEntry rows for {race}")

        pole_driver_id = next(
            (eid for eid, e in entries.items() if e.grid_position == 1), None
        )
        fl_driver_id = next(
            (eid for eid, e in entries.items() if e.is_fastest_lap), None
        )

        self.stdout.write(f"Scoring {race}  |  pole={pole_driver_id}  fl={fl_driver_id}")

        # All users in any paddock for this season
        season = race.season
        scored = 0

        for paddock in Paddock.objects.filter(season=season, is_active=True).prefetch_related("memberships"):
            rules = paddock.rules
            scoring_positions = rules.racely_scoring_positions

            # Which drivers count in this paddock (None = all)
            pool_ids = set(
                PaddockPool.objects.filter(paddock=paddock, driver__isnull=False)
                .values_list("driver_id", flat=True)
            )
            pool_constructor_ids = set(
                PaddockPool.objects.filter(paddock=paddock, constructor__isnull=False)
                .values_list("constructor_id", flat=True)
            )
            if pool_constructor_ids:
                from f1data.models import Driver
                extra = set(Driver.objects.filter(constructor_id__in=pool_constructor_ids).values_list("id", flat=True))
                pool_ids |= extra
            pool_ids = pool_ids or None  # None = no restriction

            for membership in paddock.memberships.all():
                user = membership.user
                prediction = _get_or_rollover(user, race)
                if prediction is None:
                    continue

                pos_points = _score_positions(prediction, entries, scoring_positions, pool_ids)
                pole_pts = _score_bonus(user, race, pole_driver_id, "pole", pool_ids, entries)
                fl_pts = _score_bonus(user, race, fl_driver_id, "fl", pool_ids, entries)

                RacelyScore.objects.update_or_create(
                    user=user,
                    paddock=paddock,
                    race=race,
                    defaults={
                        "position_points": pos_points,
                        "pole_points": pole_pts,
                        "fastest_lap_points": fl_pts,
                        "quiz_pending": True,  # quiz points calculated separately
                    },
                )
                scored += 1

        self.stdout.write(self.style.SUCCESS(f"Scored {scored} user-paddock combinations"))

        # Notify all scored users
        from users.notify import notify_many
        scored_users = list(User.objects.filter(
            racely_scores__race=race
        ).distinct())
        notify_many(
            scored_users,
            f"{race.name} — Racely scores updated",
            body="Check your paddock leaderboard to see how you did.",
            type="race_scored",
        )


def _get_or_rollover(user, race):
    """Return the prediction for this race, rolling over from the previous if missing."""
    pred = RacelyPrediction.objects.filter(user=user, race=race).first()
    if pred:
        return pred

    # Roll over: find most recent prior prediction with entries
    prev = (
        RacelyPrediction.objects.filter(user=user, race__season=race.season, race__round__lt=race.round)
        .order_by("-race__round")
        .first()
    )
    if not prev or not prev.entries.exists():
        return None

    new_pred = RacelyPrediction.objects.create(user=user, race=race, is_rolled_over=True)
    entries = [
        RacelyPredictionEntry(prediction=new_pred, driver_id=e.driver_id, position=e.position)
        for e in prev.entries.all()
    ]
    RacelyPredictionEntry.objects.bulk_create(entries)

    # Roll over pole and FL too
    prev_pole = PolePrediction.objects.filter(user=user, race__season=race.season, race__round__lt=race.round).order_by("-race__round").first()
    if prev_pole:
        PolePrediction.objects.get_or_create(user=user, race=race, defaults={"driver_id": prev_pole.driver_id, "is_rolled_over": True})

    prev_fl = FastestLapPrediction.objects.filter(user=user, race__season=race.season, race__round__lt=race.round).order_by("-race__round").first()
    if prev_fl:
        FastestLapPrediction.objects.get_or_create(user=user, race=race, defaults={"driver_id": prev_fl.driver_id, "is_rolled_over": True})

    return new_pred


def _score_positions(prediction, actual_entries, scoring_positions, pool_ids):
    """
    Score the top N predicted positions.
    Exact match = 2pts, off by 1 = 1pt, else 0.
    Only counts drivers in pool_ids (if restricted).
    """
    points = 0.0
    counted = 0

    for entry in prediction.entries.order_by("position"):
        if counted >= scoring_positions:
            break
        driver_id = entry.driver_id
        if pool_ids is not None and driver_id not in pool_ids:
            continue

        actual = actual_entries.get(driver_id)
        if actual is None or actual.finish_position is None:
            counted += 1
            continue

        diff = abs(entry.position - actual.finish_position)
        if diff == 0:
            points += 2
        elif diff == 1:
            points += 1

        counted += 1

    return points


def _score_bonus(user, race, actual_driver_id, bonus_type, pool_ids, actual_entries):
    """Score pole or fastest lap bonus (1 point if correct and driver is in pool)."""
    if actual_driver_id is None:
        return 0.0

    if pool_ids is not None and actual_driver_id not in pool_ids:
        return 0.0

    if bonus_type == "pole":
        pred = PolePrediction.objects.filter(user=user, race=race).first()
    else:
        pred = FastestLapPrediction.objects.filter(user=user, race=race).first()

    if pred and pred.driver_id == actual_driver_id:
        return 1.0
    return 0.0
