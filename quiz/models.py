from django.conf import settings
from django.db import models
from f1data.models import Race


class QuizQuestion(models.Model):
    BATCH_CHOICES = [
        ("quali", "Pre-Qualifying (5 questions)"),
        ("race", "Race Day (5 questions)"),
    ]

    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="quiz_questions")
    batch = models.CharField(max_length=10, choices=BATCH_CHOICES)
    question_text = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_option = models.CharField(
        max_length=1,
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")],
        blank=True,
    )
    is_ai_generated = models.BooleanField(default=True)
    is_voided = models.BooleanField(default=False)
    answers_confirmed = models.BooleanField(default=False)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="confirmed_quiz_questions",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    is_live = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.race} [{self.batch}] — {self.question_text[:60]}"


class QuizAnswer(models.Model):
    """A user's answer to a quiz question."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_answers")
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="answers")
    selected_option = models.CharField(max_length=1, choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")])
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "question")

    def __str__(self):
        return f"{self.user} — Q{self.question_id} — {self.selected_option}"
