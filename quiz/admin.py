from django.contrib import admin
from django.utils import timezone
from .models import QuizQuestion, QuizAnswer


class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 0
    readonly_fields = ["user", "selected_option", "submitted_at", "is_correct"]
    can_delete = False


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ["race", "batch", "question_text_short", "is_live", "answers_confirmed", "correct_option", "is_voided", "is_ai_generated"]
    list_editable = ["is_live", "correct_option", "is_voided"]
    list_filter = ["race", "batch", "is_live", "answers_confirmed", "is_ai_generated"]
    search_fields = ["question_text"]
    readonly_fields = ["created_at", "confirmed_by", "confirmed_at"]
    inlines = [QuizAnswerInline]

    def question_text_short(self, obj):
        return obj.question_text[:80]
    question_text_short.short_description = "Question"

    def save_model(self, request, obj, form, change):
        was_live = change and QuizQuestion.objects.filter(pk=obj.pk, is_live=False).exists()

        if "correct_option" in form.changed_data and obj.correct_option:
            obj.answers_confirmed = True
            obj.confirmed_by = request.user
            obj.confirmed_at = timezone.now()

        super().save_model(request, obj, form, change)

        # Notify when question first goes live
        if was_live and obj.is_live:
            from django.contrib.auth import get_user_model
            from users.notify import notify_many
            User = get_user_model()
            users = list(User.objects.filter(
                paddock_memberships__paddock__season=obj.race.season
            ).distinct())
            notify_many(
                users,
                f"{obj.race.name} quiz questions are live!",
                body=f"Answer the {obj.get_batch_display()} questions before the deadline.",
                type="quiz_live",
            )


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ["user", "question", "selected_option", "is_correct", "submitted_at"]
    list_filter = ["question__race", "is_correct"]
    search_fields = ["user__email"]
    readonly_fields = ["submitted_at"]
