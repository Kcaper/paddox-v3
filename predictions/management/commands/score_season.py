from django.core.management.base import BaseCommand, CommandError

from f1data.models import ConstructorChampionshipStanding, DriverChampionshipStanding, Race
from leaderboards.models import SeasonScore
from paddocks.models import Paddock, PaddockMembership
from predictions.models import ConstructorStandingPrediction, DriverStandingPrediction


class Command(BaseCommand):
    help = "Recalculate season standing scores for all paddocks after a completed race"

    def add_arguments(self, parser):
        parser.add_argument("race_id", type=int, help="Race DB ID (standings snapshot to score against)")

    def handle(self, *args, **options):
        try:
            race = Race.objects.get(pk=options["race_id"])
        except Race.DoesNotExist:
            raise CommandError(f"Race {options['race_id']} not found")

        if not race.is_complete:
            raise CommandError(f"{race} is not complete yet")

        # Actual standings after this race
        driver_standings = {
            s.driver_id: s.position
            for s in DriverChampionshipStanding.objects.filter(race=race)
        }
        ctor_standings = {
            s.constructor_id: s.position
            for s in ConstructorChampionshipStanding.objects.filter(race=race)
        }

        if not driver_standings:
            raise CommandError(f"No driver standings for {race} — run sync_f1data first")

        updated = 0
        season = race.season

        for paddock in Paddock.objects.filter(season=season, is_active=True):
            for membership in paddock.memberships.all():
                user = membership.user

                driver_pts = _score_standing_prediction(
                    DriverStandingPrediction.objects.filter(user=user, paddock=paddock)
                    .prefetch_related("entries")
                    .first(),
                    driver_standings,
                    entry_id_fn=lambda e: e.driver_id,
                )

                ctor_pts = _score_standing_prediction(
                    ConstructorStandingPrediction.objects.filter(user=user, paddock=paddock)
                    .prefetch_related("entries")
                    .first(),
                    ctor_standings,
                    entry_id_fn=lambda e: e.constructor_id,
                )

                SeasonScore.objects.update_or_create(
                    user=user,
                    paddock=paddock,
                    race=race,
                    defaults={
                        "driver_standing_points": driver_pts,
                        "constructor_standing_points": ctor_pts,
                    },
                )
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Scored season standings for {race} — updated {updated} user-paddock rows"
        ))


def _score_standing_prediction(prediction, actual_standings, entry_id_fn):
    if not prediction:
        return 0.0

    points = 0.0
    for entry in prediction.entries.all():
        item_id = entry_id_fn(entry)
        actual_pos = actual_standings.get(item_id)
        if actual_pos is None:
            continue
        diff = abs(entry.position - actual_pos)
        if diff == 0:
            points += 2
        elif diff == 1:
            points += 1
    return points
