from django.contrib import admin
from .models import Paddock, PaddockRules, PaddockMembership, PaddockPool, PaddockDeadlineReopening, PredictionSnapshot


@admin.register(PaddockRules)
class PaddockRulesAdmin(admin.ModelAdmin):
    list_display = ["name", "season", "racely_deadline_session", "racely_start_round"]
    list_filter = ["season", "racely_deadline_session"]
    search_fields = ["name"]


class PaddockMembershipInline(admin.TabularInline):
    model = PaddockMembership
    extra = 0
    fields = ["user", "role", "joined_at"]
    readonly_fields = ["joined_at"]


class PaddockPoolInline(admin.TabularInline):
    model = PaddockPool
    extra = 0
    fields = ["constructor", "driver"]


@admin.register(Paddock)
class PaddockAdmin(admin.ModelAdmin):
    list_display = ["name", "season", "is_public", "is_world_paddock", "is_active", "join_code", "created_by", "created_at"]
    list_editable = ["is_active"]
    list_filter = ["season", "is_public", "is_world_paddock", "is_active"]
    search_fields = ["name", "join_code"]
    readonly_fields = ["join_code", "created_at"]
    inlines = [PaddockMembershipInline, PaddockPoolInline]


@admin.register(PaddockMembership)
class PaddockMembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "paddock", "role", "joined_at"]
    list_editable = ["role"]
    list_filter = ["role", "paddock"]
    search_fields = ["user__email", "paddock__name"]


class PredictionSnapshotInline(admin.TabularInline):
    model = PredictionSnapshot
    extra = 0
    readonly_fields = ["user", "snapshot_type", "prediction_data", "recorded_at"]
    can_delete = False


@admin.register(PaddockDeadlineReopening)
class PaddockDeadlineReopeningAdmin(admin.ModelAdmin):
    list_display = ["paddock", "deadline_type", "reopened_by", "reopened_at", "closed_at"]
    list_filter = ["deadline_type", "paddock"]
    readonly_fields = ["reopened_by", "reopened_at"]
    inlines = [PredictionSnapshotInline]
