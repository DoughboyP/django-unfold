try:
    from rest_framework.routers import DefaultRouter
except ImportError:
    raise ImportError(
        "djangorestframework is required for pocket_watch urls. "
        "Install it with: pip install djangorestframework"
    )

from django.urls import include, path

from .views import (
    CharacterViewSet,
    DimensionViewSet,
    EventViewSet,
    ParadoxViewSet,
    TimeJumpView,
    TimelineViewSet,
)

router = DefaultRouter()
router.register(r"dimensions", DimensionViewSet, basename="dimension")
router.register(r"timelines", TimelineViewSet, basename="timeline")
router.register(r"characters", CharacterViewSet, basename="character")
router.register(r"events", EventViewSet, basename="event")
router.register(r"paradoxes", ParadoxViewSet, basename="paradox")
router.register(r"jump", TimeJumpView, basename="jump")

app_name = "pocket_watch"

urlpatterns = [
    path("", include(router.urls)),
]
