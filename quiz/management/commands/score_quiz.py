from django.core.management.base import BaseCommand, CommandError

from f1data.models import Race
from leaderboards.models import RacelyScore
from paddocks.models import Paddock, PaddockMembership
from quiz.models import QuizAnswer, QuizQuestion


class Command(BaseCommand):
    help = "Calculate quiz points for a race and update RacelyScore rows"

    def add_arguments(self, parser):
        parser.add_argument("race_id", type=int)

    def handle(self, *args, **options):
        try:
            race = Race.objects.get(pk=options["race_id"])
        except Race.DoesNotExist:
            raise CommandError(f"Race {options['race_id']} not found")

        confirmed_questions = QuizQuestion.objects.filter(
            race=race, answers_confirmed=True, is_voided=False
        )
        if not confirmed_questions.exists():
            self.stdout.write("No confirmed (non-voided) questions for this race yet.")
            return

        # Score each answer
        updated = 0
        for qa in QuizAnswer.objects.filter(question__race=race).select_related("question"):
            q = qa.question
            if not q.answers_confirmed:
                continue
            if q.is_voided:
                # Voided: everyone gets the point
                qa.is_correct = True
            else:
                qa.is_correct = qa.selected_option == q.correct_option
            qa.save(update_fields=["is_correct"])

        # For each user in each paddock, sum quiz points and update RacelyScore
        season = race.season
        for paddock in Paddock.objects.filter(season=season, is_active=True):
            for membership in paddock.memberships.all():
                user = membership.user

                # Total quiz points: correct answers + voided questions (everyone scores)
                answered_correct = QuizAnswer.objects.filter(
                    user=user, question__race=race, is_correct=True
                ).count()

                # Also count voided questions the user didn't answer (everyone scores)
                answered_ids = QuizAnswer.objects.filter(
                    user=user, question__race=race
                ).values_list("question_id", flat=True)

                unanswered_voided = QuizQuestion.objects.filter(
                    race=race, is_voided=True, answers_confirmed=True
                ).exclude(id__in=answered_ids).count()

                quiz_pts = float(answered_correct + unanswered_voided)

                score, _ = RacelyScore.objects.get_or_create(
                    user=user, paddock=paddock, race=race,
                    defaults={"position_points": 0, "pole_points": 0, "fastest_lap_points": 0},
                )
                score.quiz_points = quiz_pts
                score.quiz_pending = False
                score.save(update_fields=["quiz_points", "quiz_pending"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Scored quiz for {race} — updated {updated} RacelyScore rows"
        ))

        # Notify all paddock members
        from django.contrib.auth import get_user_model
        from users.notify import notify_many
        User = get_user_model()
        all_users = list(User.objects.filter(
            paddock_memberships__paddock__season=race.season
        ).distinct())
        notify_many(
            all_users,
            f"{race.name} — Quiz answers confirmed!",
            body="Check the quiz to see how you scored.",
            type="quiz_confirmed",
        )
