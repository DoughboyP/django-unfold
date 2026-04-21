try:
    from rest_framework import serializers
except ImportError:
    raise ImportError(
        "djangorestframework is required for pocket_watch serializers. "
        "Install it with: pip install djangorestframework"
    )

from .models import Character, CharacterState, Dimension, Event, Paradox, Timeline


class DimensionSerializer(serializers.ModelSerializer):
    stability_display = serializers.CharField(source="get_stability_display", read_only=True)

    class Meta:
        model = Dimension
        fields = [
            "id",
            "identifier",
            "name",
            "description",
            "key_divergence",
            "stability",
            "stability_display",
            "is_primary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class TimelineSerializer(serializers.ModelSerializer):
    dimension = DimensionSerializer(read_only=True)
    dimension_id = serializers.PrimaryKeyRelatedField(
        queryset=Dimension.objects.all(), source="dimension", write_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    branch_count = serializers.SerializerMethodField()

    class Meta:
        model = Timeline
        fields = [
            "id",
            "dimension",
            "dimension_id",
            "name",
            "year_start",
            "year_end",
            "status",
            "status_display",
            "branched_from",
            "branch_count",
            "notes",
        ]

    def get_branch_count(self, obj):
        return obj.branches.count()


class CharacterStateSerializer(serializers.ModelSerializer):
    dimension = DimensionSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = CharacterState
        fields = ["id", "dimension", "year", "status", "status_display", "allegiance", "notes"]


class CharacterSerializer(serializers.ModelSerializer):
    origin_dimension = DimensionSerializer(read_only=True)
    origin_dimension_id = serializers.PrimaryKeyRelatedField(
        queryset=Dimension.objects.all(), source="origin_dimension", write_only=True, required=False, allow_null=True
    )
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    states = CharacterStateSerializer(many=True, read_only=True)

    class Meta:
        model = Character
        fields = [
            "id",
            "name",
            "alias",
            "origin_dimension",
            "origin_dimension_id",
            "origin_year",
            "role",
            "role_display",
            "biography",
            "abilities",
            "motivation",
            "is_time_traveler",
            "dimensional_anchor",
            "states",
        ]


class EventSerializer(serializers.ModelSerializer):
    timeline = TimelineSerializer(read_only=True)
    timeline_id = serializers.PrimaryKeyRelatedField(
        queryset=Timeline.objects.all(), source="timeline", write_only=True
    )
    participants = CharacterSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        queryset=Character.objects.all(), source="participants", many=True, write_only=True, required=False
    )
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    paradox_risk_display = serializers.CharField(source="get_paradox_risk_display", read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "timeline",
            "timeline_id",
            "name",
            "year",
            "category",
            "category_display",
            "description",
            "participants",
            "participant_ids",
            "paradox_risk",
            "paradox_risk_display",
            "is_fixed_point",
        ]


class ParadoxSerializer(serializers.ModelSerializer):
    timeline = TimelineSerializer(read_only=True)
    timeline_id = serializers.PrimaryKeyRelatedField(
        queryset=Timeline.objects.all(), source="timeline", write_only=True
    )
    triggering_event = EventSerializer(read_only=True)
    triggering_event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        source="triggering_event",
        write_only=True,
        required=False,
        allow_null=True,
    )
    involved_characters = CharacterSerializer(many=True, read_only=True)
    involved_character_ids = serializers.PrimaryKeyRelatedField(
        queryset=Character.objects.all(),
        source="involved_characters",
        many=True,
        write_only=True,
        required=False,
    )
    paradox_type_display = serializers.CharField(source="get_paradox_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Paradox
        fields = [
            "id",
            "name",
            "paradox_type",
            "paradox_type_display",
            "timeline",
            "timeline_id",
            "triggering_event",
            "triggering_event_id",
            "involved_characters",
            "involved_character_ids",
            "description",
            "resolution_description",
            "status",
            "status_display",
            "collapses_timeline",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class TimeJumpSimulationSerializer(serializers.Serializer):
    """Input serializer for the /jump/ simulation endpoint."""

    character_id = serializers.PrimaryKeyRelatedField(queryset=Character.objects.all())
    from_dimension_id = serializers.PrimaryKeyRelatedField(queryset=Dimension.objects.all())
    to_dimension_id = serializers.PrimaryKeyRelatedField(queryset=Dimension.objects.all())
    from_year = serializers.IntegerField()
    to_year = serializers.IntegerField()

    def validate(self, data):
        year_delta = abs(data["to_year"] - data["from_year"])
        if year_delta > 50:
            raise serializers.ValidationError(
                "The Pocket Watch cannot jump more than 50 years in a single use."
            )
        if not data["character_id"].is_time_traveler:
            raise serializers.ValidationError(
                f"{data['character_id'].name} is not a time traveler and cannot operate the Watch."
            )
        return data


class ParadoxResolveSerializer(serializers.Serializer):
    """Input serializer for the /paradoxes/{id}/resolve/ endpoint."""

    resolution_method = serializers.CharField(max_length=200)
    new_status = serializers.ChoiceField(choices=Paradox.STATUS_CHOICES)
    resolution_notes = serializers.CharField(required=False, allow_blank=True)
