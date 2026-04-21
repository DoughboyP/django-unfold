try:
    from rest_framework import status
    from rest_framework.decorators import action
    from rest_framework.response import Response
    from rest_framework.viewsets import ModelViewSet, ViewSet
except ImportError:
    raise ImportError(
        "djangorestframework is required for pocket_watch views. "
        "Install it with: pip install djangorestframework"
    )

from .models import Character, CharacterState, Dimension, Event, Paradox, Timeline
from .serializers import (
    CharacterSerializer,
    CharacterStateSerializer,
    DimensionSerializer,
    EventSerializer,
    ParadoxResolveSerializer,
    ParadoxSerializer,
    TimeJumpSimulationSerializer,
    TimelineSerializer,
)


class DimensionViewSet(ModelViewSet):
    """
    CRUD endpoints for Dimensions.

    GET  /api/pocket-watch/dimensions/       — list all dimensions
    POST /api/pocket-watch/dimensions/       — create a dimension
    GET  /api/pocket-watch/dimensions/{id}/  — retrieve a dimension
    PUT  /api/pocket-watch/dimensions/{id}/  — update a dimension
    DEL  /api/pocket-watch/dimensions/{id}/  — delete a dimension
    """

    queryset = Dimension.objects.all()
    serializer_class = DimensionSerializer


class TimelineViewSet(ModelViewSet):
    """
    CRUD endpoints for Timelines.

    Supports filtering by ?dimension_id=<id> and ?status=<value>.
    """

    queryset = Timeline.objects.select_related("dimension", "branched_from").all()
    serializer_class = TimelineSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        dimension_id = self.request.query_params.get("dimension_id")
        timeline_status = self.request.query_params.get("status")
        if dimension_id:
            qs = qs.filter(dimension_id=dimension_id)
        if timeline_status:
            qs = qs.filter(status=timeline_status)
        return qs


class CharacterViewSet(ModelViewSet):
    """
    CRUD endpoints for Characters.

    Supports filtering by ?role=<value> and ?is_time_traveler=true/false.

    Extra action:
        GET /api/pocket-watch/characters/{id}/states/ — all dimensional states for this character
    """

    queryset = Character.objects.select_related("origin_dimension").prefetch_related("states__dimension").all()
    serializer_class = CharacterSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get("role")
        is_traveler = self.request.query_params.get("is_time_traveler")
        if role:
            qs = qs.filter(role=role)
        if is_traveler is not None:
            qs = qs.filter(is_time_traveler=is_traveler.lower() == "true")
        return qs

    @action(detail=True, methods=["get"])
    def states(self, request, pk=None):
        """Return all CharacterState records for this character across dimensions."""
        character = self.get_object()
        states = character.states.select_related("dimension").all()
        serializer = CharacterStateSerializer(states, many=True)
        return Response(serializer.data)


class EventViewSet(ModelViewSet):
    """
    CRUD endpoints for Timeline Events.

    Supports filtering by ?timeline_id=<id>, ?year=<int>, ?category=<value>,
    and ?paradox_risk=<value>.
    """

    queryset = (
        Event.objects.select_related("timeline__dimension").prefetch_related("participants").all()
    )
    serializer_class = EventSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        timeline_id = self.request.query_params.get("timeline_id")
        year = self.request.query_params.get("year")
        category = self.request.query_params.get("category")
        paradox_risk = self.request.query_params.get("paradox_risk")
        if timeline_id:
            qs = qs.filter(timeline_id=timeline_id)
        if year:
            qs = qs.filter(year=year)
        if category:
            qs = qs.filter(category=category)
        if paradox_risk:
            qs = qs.filter(paradox_risk=paradox_risk)
        return qs


class ParadoxViewSet(ModelViewSet):
    """
    CRUD endpoints for Paradoxes.

    Supports filtering by ?timeline_id=<id> and ?status=<value>.

    Extra action:
        POST /api/pocket-watch/paradoxes/{id}/resolve/ — resolve a paradox
    """

    queryset = (
        Paradox.objects.select_related("timeline__dimension", "triggering_event")
        .prefetch_related("involved_characters")
        .all()
    )
    serializer_class = ParadoxSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        timeline_id = self.request.query_params.get("timeline_id")
        paradox_status = self.request.query_params.get("status")
        if timeline_id:
            qs = qs.filter(timeline_id=timeline_id)
        if paradox_status:
            qs = qs.filter(status=paradox_status)
        return qs

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """
        Trigger paradox resolution.

        Payload:
            {
                "resolution_method": "Tre-α jumped out of the zone",
                "new_status": "resolved",
                "resolution_notes": "Optional extra detail"
            }
        """
        paradox = self.get_object()
        serializer = ParadoxResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        paradox.status = data["new_status"]
        if data.get("resolution_notes"):
            paradox.resolution_description = (
                f"{paradox.resolution_description}\n\n[{data['resolution_method']}] "
                f"{data['resolution_notes']}"
            ).strip()
        else:
            paradox.resolution_description = (
                f"{paradox.resolution_description}\n\n[{data['resolution_method']}]"
            ).strip()
        paradox.save(update_fields=["status", "resolution_description", "updated_at"])

        return Response(ParadoxSerializer(paradox).data, status=status.HTTP_200_OK)


class TimeJumpView(ViewSet):
    """
    Simulate a time jump and return predicted consequences.

    POST /api/pocket-watch/jump/

    Payload:
        {
            "character_id": 1,
            "from_dimension_id": 1,
            "to_dimension_id": 5,
            "from_year": 1993,
            "to_year": 1987
        }

    Returns:
        {
            "feasible": true/false,
            "year_delta": 6,
            "cross_dimensional": true/false,
            "estimated_aging_hours": 14,
            "paradox_risk": "high",
            "warnings": [...]
        }
    """

    def create(self, request, *args, **kwargs):
        serializer = TimeJumpSimulationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        character = data["character_id"]
        from_dim = data["from_dimension_id"]
        to_dim = data["to_dimension_id"]
        year_delta = abs(data["to_year"] - data["from_year"])
        cross_dimensional = from_dim.pk != to_dim.pk

        # Estimate aging: base 2 hours per decade + 6 hours per dimension crossed
        estimated_aging = (year_delta // 10) * 2 + (6 if cross_dimensional else 0)

        # Assess paradox risk
        warnings = []
        if year_delta == 0 and not cross_dimensional:
            paradox_risk = "none"
        elif year_delta <= 5 and not cross_dimensional:
            paradox_risk = "low"
        elif year_delta <= 20 or cross_dimensional:
            paradox_risk = "medium"
            if cross_dimensional:
                warnings.append(
                    f"Crossing from {from_dim.identifier} to {to_dim.identifier} — "
                    "ensure diplomatic clearance."
                )
        else:
            paradox_risk = "high"
            warnings.append("Large temporal displacement — risk of causal branch creation.")

        if to_dim.stability == "collapsing":
            paradox_risk = "critical"
            warnings.append(f"Dimension {to_dim.identifier} is collapsing — jump is extremely dangerous.")

        # Check for existing presence (simplified: check CharacterState)
        already_present = CharacterState.objects.filter(
            character=character, dimension=to_dim, year=data["to_year"]
        ).exists()
        if already_present:
            paradox_risk = "critical"
            warnings.append(
                f"{character.name} already has a recorded presence in "
                f"{to_dim.identifier} in {data['to_year']} — "
                "meeting yourself risks Collapse Paradox."
            )

        return Response(
            {
                "feasible": paradox_risk != "critical",
                "character": character.name,
                "from_dimension": from_dim.identifier,
                "to_dimension": to_dim.identifier,
                "from_year": data["from_year"],
                "to_year": data["to_year"],
                "year_delta": year_delta,
                "cross_dimensional": cross_dimensional,
                "estimated_aging_hours": estimated_aging,
                "paradox_risk": paradox_risk,
                "warnings": warnings,
            },
            status=status.HTTP_200_OK,
        )
