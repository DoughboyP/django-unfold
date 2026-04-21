from django.db import models


class Dimension(models.Model):
    """Represents an alternate universe / parallel dimension."""

    STABILITY_STABLE = "stable"
    STABILITY_FRAGILE = "fragile"
    STABILITY_COLLAPSING = "collapsing"
    STABILITY_DANGER = "danger"

    STABILITY_CHOICES = [
        (STABILITY_STABLE, "Stable"),
        (STABILITY_FRAGILE, "Fragile"),
        (STABILITY_COLLAPSING, "Collapsing"),
        (STABILITY_DANGER, "Danger Zone"),
    ]

    identifier = models.CharField(max_length=10, unique=True, help_text="E.g. α, β, ε")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    key_divergence = models.TextField(
        blank=True, help_text="The event that caused this dimension to split from the primary timeline"
    )
    stability = models.CharField(max_length=20, choices=STABILITY_CHOICES, default=STABILITY_STABLE)
    is_primary = models.BooleanField(default=False, help_text="True only for the baseline/origin dimension")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["identifier"]

    def __str__(self):
        return f"Dimension {self.identifier} — {self.name}"


class Timeline(models.Model):
    """A specific causal sequence within a dimension."""

    STATUS_ACTIVE = "active"
    STATUS_BRANCHED = "branched"
    STATUS_COLLAPSED = "collapsed"
    STATUS_FROZEN = "frozen"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_BRANCHED, "Branched"),
        (STATUS_COLLAPSED, "Collapsed"),
        (STATUS_FROZEN, "Frozen"),
    ]

    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE, related_name="timelines")
    name = models.CharField(max_length=100)
    year_start = models.IntegerField(help_text="Earliest year in this timeline")
    year_end = models.IntegerField(null=True, blank=True, help_text="Latest known year; null means ongoing")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    branched_from = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="branches",
        help_text="Parent timeline this one split from",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["dimension", "year_start"]

    def __str__(self):
        return f"{self.name} ({self.dimension.identifier}, {self.year_start}–{self.year_end or '…'})"


class Character(models.Model):
    """A person who exists (in at least one form) across the multiverse."""

    ROLE_PROTAGONIST = "protagonist"
    ROLE_ANTAGONIST = "antagonist"
    ROLE_ALLY = "ally"
    ROLE_NEUTRAL = "neutral"
    ROLE_DOPPELGANGER = "doppelganger"

    ROLE_CHOICES = [
        (ROLE_PROTAGONIST, "Protagonist"),
        (ROLE_ANTAGONIST, "Antagonist"),
        (ROLE_ALLY, "Ally"),
        (ROLE_NEUTRAL, "Neutral"),
        (ROLE_DOPPELGANGER, "Doppelgänger"),
    ]

    name = models.CharField(max_length=100)
    alias = models.CharField(max_length=100, blank=True, help_text="Street name or code name")
    origin_dimension = models.ForeignKey(
        Dimension, on_delete=models.SET_NULL, null=True, related_name="native_characters"
    )
    origin_year = models.IntegerField(null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_NEUTRAL)
    biography = models.TextField(blank=True)
    abilities = models.TextField(blank=True, help_text="Special powers, knowledge, or artifacts")
    motivation = models.TextField(blank=True)
    is_time_traveler = models.BooleanField(default=False)
    dimensional_anchor = models.BooleanField(
        default=False,
        help_text="If True, this character's existence stabilises their home dimension",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.alias})" if self.alias else self.name


class CharacterState(models.Model):
    """Records a character's status within a specific dimension at a point in time."""

    STATUS_ALIVE = "alive"
    STATUS_DEAD = "dead"
    STATUS_MISSING = "missing"
    STATUS_DISPLACED = "displaced"

    STATUS_CHOICES = [
        (STATUS_ALIVE, "Alive"),
        (STATUS_DEAD, "Dead"),
        (STATUS_MISSING, "Missing"),
        (STATUS_DISPLACED, "Dimensionally Displaced"),
    ]

    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name="states")
    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE, related_name="character_states")
    year = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ALIVE)
    allegiance = models.CharField(max_length=100, blank=True, help_text="Gang, faction, or organisation")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["character", "dimension", "year"]
        unique_together = [("character", "dimension", "year")]

    def __str__(self):
        return f"{self.character} in {self.dimension.identifier} ({self.year}): {self.get_status_display()}"


class Event(models.Model):
    """A significant occurrence within a timeline."""

    CATEGORY_ASSASSINATION = "assassination"
    CATEGORY_JUMP = "jump"
    CATEGORY_MOB = "mob"
    CATEGORY_DRUG_TRADE = "drug_trade"
    CATEGORY_PARADOX_TRIGGER = "paradox_trigger"
    CATEGORY_DIPLOMATIC = "diplomatic"
    CATEGORY_OTHER = "other"

    CATEGORY_CHOICES = [
        (CATEGORY_ASSASSINATION, "Assassination"),
        (CATEGORY_JUMP, "Time Jump"),
        (CATEGORY_MOB, "Mob Activity"),
        (CATEGORY_DRUG_TRADE, "Drug Trade"),
        (CATEGORY_PARADOX_TRIGGER, "Paradox Trigger"),
        (CATEGORY_DIPLOMATIC, "Diplomatic"),
        (CATEGORY_OTHER, "Other"),
    ]

    timeline = models.ForeignKey(Timeline, on_delete=models.CASCADE, related_name="events")
    name = models.CharField(max_length=200)
    year = models.IntegerField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    description = models.TextField()
    participants = models.ManyToManyField(Character, blank=True, related_name="events")
    paradox_risk = models.CharField(
        max_length=20,
        choices=[("none", "None"), ("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
        default="none",
    )
    is_fixed_point = models.BooleanField(
        default=False,
        help_text="Fixed points cannot be altered without catastrophic multiverse consequences",
    )

    class Meta:
        ordering = ["timeline", "year", "name"]

    def __str__(self):
        return f"{self.name} ({self.year}) — {self.timeline}"


class Paradox(models.Model):
    """A causal contradiction or temporal anomaly within the multiverse."""

    TYPE_GRANDFATHER = "grandfather"
    TYPE_BOOTSTRAP = "bootstrap"
    TYPE_COLLAPSE = "collapse"
    TYPE_OBSERVER = "observer"
    TYPE_PREDESTINATION = "predestination"

    TYPE_CHOICES = [
        (TYPE_GRANDFATHER, "Grandfather Paradox"),
        (TYPE_BOOTSTRAP, "Bootstrap Paradox"),
        (TYPE_COLLAPSE, "Collapse Paradox"),
        (TYPE_OBSERVER, "Observer Paradox"),
        (TYPE_PREDESTINATION, "Predestination Paradox"),
    ]

    STATUS_UNRESOLVED = "unresolved"
    STATUS_CONTAINED = "contained"
    STATUS_RESOLVED = "resolved"
    STATUS_CATASTROPHIC = "catastrophic"

    STATUS_CHOICES = [
        (STATUS_UNRESOLVED, "Unresolved"),
        (STATUS_CONTAINED, "Contained"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_CATASTROPHIC, "Catastrophic — Unrecoverable"),
    ]

    name = models.CharField(max_length=200)
    paradox_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    timeline = models.ForeignKey(Timeline, on_delete=models.CASCADE, related_name="paradoxes")
    triggering_event = models.ForeignKey(
        Event, null=True, blank=True, on_delete=models.SET_NULL, related_name="paradoxes_triggered"
    )
    involved_characters = models.ManyToManyField(Character, blank=True, related_name="paradoxes")
    description = models.TextField()
    resolution_description = models.TextField(blank=True, help_text="How was / can this paradox be resolved?")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNRESOLVED)
    collapses_timeline = models.BooleanField(
        default=False, help_text="If True, resolving or ignoring this paradox destroys its host timeline"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["timeline", "status", "name"]
        verbose_name_plural = "paradoxes"

    def __str__(self):
        return f"{self.name} [{self.get_status_display()}]"
