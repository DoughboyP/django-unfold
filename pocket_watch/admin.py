from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from unfold.admin import ModelAdmin, TabularInline

from .models import Character, CharacterState, Dimension, Event, Paradox, Timeline


class TimelineInline(TabularInline):
    model = Timeline
    extra = 0
    fields = ("name", "year_start", "year_end", "status")
    show_change_link = True


class CharacterStateInline(TabularInline):
    model = CharacterState
    extra = 0
    fields = ("dimension", "year", "status", "allegiance")


@admin.register(Dimension)
class DimensionAdmin(ModelAdmin):
    list_display = ("identifier", "name", "stability", "is_primary")
    list_filter = ("stability", "is_primary")
    search_fields = ("identifier", "name", "description")
    ordering = ("identifier",)
    inlines = [TimelineInline]
    fieldsets = (
        (
            _("Identity"),
            {
                "fields": ("identifier", "name", "is_primary"),
            },
        ),
        (
            _("Details"),
            {
                "fields": ("description", "key_divergence", "stability"),
            },
        ),
    )


@admin.register(Timeline)
class TimelineAdmin(ModelAdmin):
    list_display = ("name", "dimension", "year_start", "year_end", "status")
    list_filter = ("status", "dimension")
    search_fields = ("name", "notes")
    ordering = ("dimension", "year_start")
    fieldsets = (
        (
            _("Timeline"),
            {
                "fields": ("dimension", "name", "branched_from"),
            },
        ),
        (
            _("Temporal Range"),
            {
                "fields": ("year_start", "year_end", "status"),
            },
        ),
        (
            _("Notes"),
            {
                "fields": ("notes",),
            },
        ),
    )


@admin.register(Character)
class CharacterAdmin(ModelAdmin):
    list_display = ("name", "alias", "role", "origin_dimension", "origin_year", "is_time_traveler")
    list_filter = ("role", "is_time_traveler", "dimensional_anchor", "origin_dimension")
    search_fields = ("name", "alias", "biography")
    ordering = ("name",)
    inlines = [CharacterStateInline]
    fieldsets = (
        (
            _("Identity"),
            {
                "fields": ("name", "alias", "role"),
            },
        ),
        (
            _("Origin"),
            {
                "fields": ("origin_dimension", "origin_year"),
            },
        ),
        (
            _("Profile"),
            {
                "fields": ("biography", "abilities", "motivation"),
            },
        ),
        (
            _("Dimensional Properties"),
            {
                "fields": ("is_time_traveler", "dimensional_anchor"),
            },
        ),
    )


@admin.register(Event)
class EventAdmin(ModelAdmin):
    list_display = ("name", "year", "category", "timeline", "paradox_risk", "is_fixed_point")
    list_filter = ("category", "paradox_risk", "is_fixed_point", "timeline__dimension")
    search_fields = ("name", "description")
    filter_horizontal = ("participants",)
    ordering = ("timeline", "year")
    fieldsets = (
        (
            _("Event"),
            {
                "fields": ("timeline", "name", "year", "category"),
            },
        ),
        (
            _("Description"),
            {
                "fields": ("description",),
            },
        ),
        (
            _("Participants & Risk"),
            {
                "fields": ("participants", "paradox_risk", "is_fixed_point"),
            },
        ),
    )


@admin.register(Paradox)
class ParadoxAdmin(ModelAdmin):
    list_display = ("name", "paradox_type", "timeline", "status", "collapses_timeline")
    list_filter = ("paradox_type", "status", "collapses_timeline", "timeline__dimension")
    search_fields = ("name", "description", "resolution_description")
    filter_horizontal = ("involved_characters",)
    ordering = ("timeline", "status", "name")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Paradox"),
            {
                "fields": ("name", "paradox_type", "timeline", "triggering_event"),
            },
        ),
        (
            _("Narrative"),
            {
                "fields": ("description", "involved_characters"),
            },
        ),
        (
            _("Resolution"),
            {
                "fields": ("status", "resolution_description", "collapses_timeline"),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
