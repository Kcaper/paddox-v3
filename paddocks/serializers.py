from rest_framework import serializers

from .models import Paddock, PaddockMembership, PaddockRules


class PaddockRulesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaddockRules
        fields = [
            "racely_deadline_session", "racely_start_round", "racely_scoring_positions",
            "driver_standing_deadline_session", "driver_standing_start_round",
            "constructor_standing_deadline_session", "constructor_standing_start_round",
        ]


class PaddockListSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Paddock
        fields = [
            "id", "name", "join_code", "is_public", "is_world_paddock",
            "max_players", "member_count", "my_role", "created_at",
        ]

    def get_member_count(self, obj):
        return obj.memberships.count()

    def get_my_role(self, obj):
        user = self.context["request"].user
        m = obj.memberships.filter(user=user).first()
        return m.role if m else None


class PaddockDetailSerializer(PaddockListSerializer):
    rules = PaddockRulesSerializer(read_only=True)
    members = serializers.SerializerMethodField()

    class Meta(PaddockListSerializer.Meta):
        fields = PaddockListSerializer.Meta.fields + ["rules", "members"]

    def get_members(self, obj):
        return [
            {"id": m.user.id, "username": m.user.username, "role": m.role}
            for m in obj.memberships.select_related("user").order_by("joined_at")
        ]


class CreatePaddockSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=30)
    is_public = serializers.BooleanField(default=False)
    max_players = serializers.IntegerField(default=20, min_value=2, max_value=500)
    racely_deadline_session = serializers.ChoiceField(
        choices=PaddockRules.DEADLINE_SESSION_CHOICES, default="Q1"
    )
    racely_scoring_positions = serializers.IntegerField(default=10, min_value=1, max_value=20)
