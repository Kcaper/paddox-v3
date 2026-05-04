import json
import os

from django.core.management.base import BaseCommand, CommandError

from f1data.models import DriverChampionshipStanding, Race, RaceEntry
from quiz.models import QuizQuestion


SYSTEM_PROMPT = """You are a Formula 1 trivia expert. Generate multiple-choice quiz questions for F1 fans.
Each question must have exactly 4 options (A, B, C, D) and one correct answer.
Questions should be engaging, factual, and relevant to the specific race/context provided.
Return ONLY a valid JSON array with no markdown, no explanation — just the JSON."""

QUESTION_SCHEMA = """[
  {
    "question_text": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_option": "A"
  }
]"""


class Command(BaseCommand):
    help = "Generate AI quiz questions for a race using Claude"

    def add_arguments(self, parser):
        parser.add_argument("race_id", type=int)
        parser.add_argument(
            "--batch",
            choices=["quali", "race"],
            default="quali",
            help="Which batch to generate (quali or race)",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            help="Number of questions to generate (default 5)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print questions without saving to DB",
        )

    def handle(self, *args, **options):
        try:
            race = Race.objects.select_related("season", "circuit").get(pk=options["race_id"])
        except Race.DoesNotExist:
            raise CommandError(f"Race {options['race_id']} not found")

        batch = options["batch"]
        count = options["count"]

        # Build context for Claude
        context = self._build_context(race, batch)

        prompt = (
            f"Generate exactly {count} Formula 1 trivia questions for the {race.season.year} "
            f"{race.name} ({race.circuit.name}, {race.circuit.country}).\n\n"
            f"Context:\n{context}\n\n"
            f"Batch type: {'Pre-qualifying (use circuit history, driver stats, championship standings, predictions)' if batch == 'quali' else 'Race day (use qualifying results if available, race strategies, race history at this circuit)'}\n\n"
            f"Return a JSON array of exactly {count} questions using this schema:\n{QUESTION_SCHEMA}"
        )

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise CommandError("ANTHROPIC_API_KEY environment variable not set")

        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        self.stdout.write(f"Generating {count} {batch} questions for {race}…")

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text.strip()

        try:
            questions = json.loads(raw)
        except json.JSONDecodeError:
            # Try extracting JSON array from response
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start == -1 or end == 0:
                raise CommandError(f"Could not parse JSON from response:\n{raw}")
            questions = json.loads(raw[start:end])

        if not isinstance(questions, list):
            raise CommandError(f"Expected a JSON array, got: {type(questions)}")

        if options["dry_run"]:
            for i, q in enumerate(questions, 1):
                self.stdout.write(f"\n--- Q{i} ---")
                self.stdout.write(q["question_text"])
                for opt in ("a", "b", "c", "d"):
                    key = f"option_{opt}"
                    marker = " ✓" if q["correct_option"].upper() == opt.upper() else ""
                    self.stdout.write(f"  {opt.upper()}. {q[key]}{marker}")
            self.stdout.write(self.style.SUCCESS(f"\nDry run complete — {len(questions)} questions generated"))
            return

        # Check for existing questions to avoid duplicates
        existing = QuizQuestion.objects.filter(race=race, batch=batch).count()
        if existing > 0:
            self.stdout.write(
                self.style.WARNING(f"Warning: {existing} {batch} questions already exist for {race}. Adding more.")
            )

        created = 0
        for q in questions:
            correct = q.get("correct_option", "").strip().upper()
            if correct not in ("A", "B", "C", "D"):
                self.stdout.write(self.style.WARNING(f"Skipping question with invalid correct_option: {correct!r}"))
                continue

            QuizQuestion.objects.create(
                race=race,
                batch=batch,
                question_text=q["question_text"].strip(),
                option_a=q["option_a"].strip(),
                option_b=q["option_b"].strip(),
                option_c=q["option_c"].strip(),
                option_d=q["option_d"].strip(),
                correct_option=correct,
                is_ai_generated=True,
                is_live=False,
                answers_confirmed=False,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Created {created} {batch} questions for {race} — review in admin before going live"
        ))

    def _build_context(self, race, batch):
        lines = [f"Race: {race.name}", f"Circuit: {race.circuit.name}, {race.circuit.city}, {race.circuit.country}", f"Season: {race.season.year}", f"Round: {race.round}"]

        # Current drivers on grid
        entries = RaceEntry.objects.filter(race=race, is_confirmed=True).select_related("driver", "constructor")
        if entries.exists():
            lines.append("\nGrid (qualifying order):")
            for e in sorted(entries, key=lambda x: x.grid_position or 99):
                pos = e.grid_position or "?"
                lines.append(f"  P{pos}: {e.driver} ({e.constructor})")
        else:
            # Fall back to current-season on-grid drivers
            from f1data.models import Driver
            drivers = Driver.objects.filter(is_on_grid=True, is_reserve=False).select_related("constructor")
            lines.append("\nExpected drivers:")
            for d in drivers:
                lines.append(f"  {d} ({d.constructor})")

        # Championship standings
        standings = (
            DriverChampionshipStanding.objects
            .filter(race__season=race.season, race__round__lt=race.round)
            .order_by("-race__round", "position")
            .select_related("driver")
        )
        seen = set()
        top_standings = []
        for s in standings:
            if s.driver_id not in seen:
                top_standings.append(s)
                seen.add(s.driver_id)
            if len(top_standings) >= 10:
                break

        if top_standings:
            lines.append("\nDriver championship standings (going into this race):")
            for s in top_standings:
                lines.append(f"  P{s.position}: {s.driver} — {s.points} pts")

        return "\n".join(lines)
