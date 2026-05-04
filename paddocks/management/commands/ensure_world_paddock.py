from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from f1data.models import Season
from paddocks.models import Paddock, PaddockMembership, PaddockRules

User = get_user_model()


class Command(BaseCommand):
    help = "Create the World Paddock for the active season if it doesn't exist"

    def handle(self, *args, **options):
        season = Season.objects.filter(is_active=True).first()
        if not season:
            self.stdout.write(self.style.ERROR("No active season found. Run sync_f1data first."))
            return

        if Paddock.objects.filter(is_world_paddock=True, season=season).exists():
            self.stdout.write(f"World paddock already exists for {season.year}.")
            return

        super_admin = User.objects.filter(is_super_admin=True).first()
        if not super_admin:
            super_admin = User.objects.filter(is_superuser=True).first()
        if not super_admin:
            self.stdout.write(self.style.ERROR("No super admin user found."))
            return

        rules = PaddockRules.objects.create(
            name="World Paddock Rules",
            season=season,
            racely_deadline_session="Q1",
            racely_start_round=1,
            racely_scoring_positions=10,
            driver_standing_deadline_session="Q1",
            driver_standing_start_round=1,
            constructor_standing_deadline_session="Q1",
            constructor_standing_start_round=1,
        )

        world = Paddock.objects.create(
            season=season,
            name="World Paddock",
            rules=rules,
            is_public=True,
            is_world_paddock=True,
            max_players=99999,
            created_by=super_admin,
        )

        PaddockMembership.objects.create(paddock=world, user=super_admin, role="owner")

        self.stdout.write(self.style.SUCCESS(
            f"Created World Paddock for {season.year} (join code: {world.join_code})"
        ))
