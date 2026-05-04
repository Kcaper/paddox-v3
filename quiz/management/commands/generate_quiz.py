import json
import os

from django.core.management.base import BaseCommand, CommandError

from f1data.models import DriverChampionshipStanding, Race, RaceEntry
from quiz.models import QuizQuestion


SYSTEM_PROMPT = """You are a Formula 1 quiz master creating prediction questions for an upcoming race.

IMPORTANT: Questions must be about things that HAVE NOT HAPPENED YET — the answers are unknown at the time of asking.
Players predict what WILL happen, then correct answers are confirmed after the race.

Good question types:
- "Who will win the race?"
- "How many safety cars will be deployed?"
- "Will there be a red flag?"
- "Which team will have the first mechanical retirement?"
- "Who will set the fastest lap?"
- "Will the pole sitter win?"
- "How many drivers will finish on the lead lap?"
- "Which driver will be first to retire?"
- "Will there be a first-lap collision?"
- "Who will be last on the grid after penalties?"

Each question must have 4 options (A, B, C, D). The correct_option field is your BEST PREDICTION based on
current form, circuit history, and any news you've found — the admin will confirm the actual answer after the race.

Return ONLY a valid JSON array. No markdown, no explanation."""

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
    help = "Generate AI prediction quiz questions for an upcoming race using OpenAI (with web search)"

    def add_arguments(self, parser):
        parser.add_argument("race_id", type=int)
        parser.add_argument(
            "--batch",
            choices=["quali", "race"],
            default="quali",
            help="quali = before qualifying (predict everything); race = before race start (qualifying known)",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            help="Number of questions to generate (default 5)",
        )
        parser.add_argument(
            "--model",
            default="gpt-4o",
            help="OpenAI model to use (default: gpt-4o)",
        )
        parser.add_argument(
            "--no-search",
            action="store_true",
            help="Skip web search, use only local DB context",
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
        model = options["model"]

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise CommandError("OPENAI_API_KEY environment variable not set")

        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        context = self._build_context(race, batch)

        batch_desc = (
            "before qualifying — predict qualifying AND race outcomes (everything is unknown)"
            if batch == "quali"
            else "after qualifying, before race start — qualifying results are known, race outcomes are unknown"
        )

        prompt = (
            f"Generate exactly {count} prediction questions for the UPCOMING {race.season.year} {race.name} "
            f"at {race.circuit.name}, {race.circuit.country}.\n\n"
            f"Timing: {batch_desc}\n\n"
            f"Context from our database:\n{context}\n\n"
            f"Search for recent news, previews, driver form, weather forecasts, and circuit notes "
            f"for the {race.season.year} {race.name} to make the questions relevant and specific.\n\n"
            f"Make questions varied — mix driver picks, team outcomes, race incidents (safety cars, crashes, "
            f"retirements), and race format questions (how many laps under SC, red flag yes/no, etc.).\n\n"
            f"Return a JSON array of exactly {count} questions:\n{QUESTION_SCHEMA}"
        )

        self.stdout.write(f"Generating {count} {batch} prediction questions for {race} using {model}…")

        if options["no_search"]:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.8,
            )
            raw = response.choices[0].message.content.strip()
        else:
            # Use responses API with web search
            self.stdout.write("  Searching for race previews and news…")
            try:
                response = client.responses.create(
                    model=model,
                    tools=[{"type": "web_search_preview"}],
                    instructions=SYSTEM_PROMPT,
                    input=prompt,
                )
                raw = response.output_text.strip()
                # Strip markdown code fences if present
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Web search failed ({e}), falling back to no-search mode"))
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.8,
                )
                raw = response.choices[0].message.content.strip()

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                questions = next(
                    (v for v in parsed.values() if isinstance(v, list)),
                    None,
                )
                if questions is None:
                    raise CommandError(f"Could not find question list in response:\n{raw}")
            else:
                questions = parsed
        except json.JSONDecodeError:
            # Last resort: find array in raw text
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start == -1 or end == 0:
                raise CommandError(f"Could not parse JSON from response:\n{raw}")
            questions = json.loads(raw[start:end])

        if not isinstance(questions, list):
            raise CommandError(f"Expected a list, got {type(questions)}")

        if options["dry_run"]:
            for i, q in enumerate(questions, 1):
                self.stdout.write(f"\n--- Q{i} ---")
                self.stdout.write(q["question_text"])
                for opt in ("a", "b", "c", "d"):
                    marker = " ✓" if q["correct_option"].upper() == opt.upper() else ""
                    self.stdout.write(f"  {opt.upper()}. {q[f'option_{opt}']}{marker}")
            self.stdout.write(self.style.SUCCESS(f"\nDry run — {len(questions)} questions generated (not saved)"))
            return

        existing = QuizQuestion.objects.filter(race=race, batch=batch).count()
        if existing > 0:
            self.stdout.write(self.style.WARNING(
                f"Warning: {existing} {batch} questions already exist for {race}. Adding more."
            ))

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
            f"Created {created} {batch} questions for {race} — go to admin to review and mark live"
        ))

    def _build_context(self, race, batch):
        lines = [
            f"Race: {race.name}",
            f"Circuit: {race.circuit.name}, {race.circuit.city}, {race.circuit.country}",
            f"Season: {race.season.year}",
            f"Round: {race.round}",
        ]

        if batch == "race":
            entries = RaceEntry.objects.filter(race=race, is_confirmed=True).select_related("driver", "constructor")
            if entries.exists():
                lines.append("\nQualifying result (grid order):")
                for e in sorted(entries, key=lambda x: x.grid_position or 99):
                    lines.append(f"  P{e.grid_position or '?'}: {e.driver} ({e.constructor})")

        # Current championship standings for driver context
        standings = (
            DriverChampionshipStanding.objects
            .filter(race__season=race.season, race__round__lt=race.round)
            .order_by("-race__round", "position")
            .select_related("driver")
        )
        seen = set()
        top = []
        for s in standings:
            if s.driver_id not in seen:
                top.append(s)
                seen.add(s.driver_id)
            if len(top) >= 10:
                break

        if top:
            lines.append("\nChampionship standings before this race:")
            for s in top:
                lines.append(f"  P{s.position}: {s.driver} — {s.points} pts")
        else:
            from f1data.models import Driver
            drivers = Driver.objects.filter(is_on_grid=True, is_reserve=False).select_related("constructor")
            lines.append("\nDrivers:")
            for d in drivers:
                lines.append(f"  {d} ({d.constructor})")

        return "\n".join(lines)
