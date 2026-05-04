from datetime import datetime, timezone

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from f1data.models import Race, Season
from .models import QuizAnswer, QuizQuestion


def _current_race():
    now = datetime.now(timezone.utc)
    season = Season.objects.filter(is_active=True).first()
    if not season:
        return None
    upcoming = Race.objects.filter(season=season, quali_at__gt=now).order_by("round").first()
    return upcoming or Race.objects.filter(season=season).order_by("-round").first()


@api_view(["GET"])
def live_questions(request):
    race = _current_race()
    if not race:
        return Response({"questions": []})

    questions = QuizQuestion.objects.filter(race=race, is_live=True).order_by("batch", "id")
    user_answers = {
        a.question_id: a.selected_option
        for a in QuizAnswer.objects.filter(user=request.user, question__race=race)
    }

    data = []
    for q in questions:
        data.append({
            "id": q.id,
            "batch": q.batch,
            "question_text": q.question_text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "my_answer": user_answers.get(q.id),
            "is_voided": q.is_voided,
            "answers_confirmed": q.answers_confirmed,
            "correct_option": q.correct_option if q.answers_confirmed else None,
        })

    return Response({"race": race.name, "questions": data})


@api_view(["POST"])
def submit_answer(request, question_id):
    try:
        question = QuizQuestion.objects.get(pk=question_id, is_live=True)
    except QuizQuestion.DoesNotExist:
        return Response({"detail": "Question not found or not live."}, status=404)

    if question.answers_confirmed:
        return Response({"detail": "Answers already confirmed — too late to answer."}, status=400)

    option = (request.data.get("option") or "").upper()
    if option not in ("A", "B", "C", "D"):
        return Response({"detail": "option must be A, B, C, or D."}, status=400)

    if QuizAnswer.objects.filter(user=request.user, question=question).exists():
        return Response({"detail": "Already answered."}, status=400)

    QuizAnswer.objects.create(user=request.user, question=question, selected_option=option)
    return Response({"detail": "Answer recorded."})
